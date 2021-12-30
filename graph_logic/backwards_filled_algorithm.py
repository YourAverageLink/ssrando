from dataclasses import dataclass
import random  # Only for typing purposes
from typing import Set

from .logic import Logic
from .inventory import EXTENDED_ITEM


@dataclass
class RandomizationSettings:
    must_be_placed_items: Set[str]
    may_be_placed_items: Set[str]
    duplicable_items: Set[str]


class BFA:
    def __init__(
        self, logic: Logic, rng: random.Random, randosettings: RandomizationSettings
    ):

        self.logic = logic
        self.rng = rng
        self.randosettings = randosettings

        truly_progress_item = self.logic.aggregate_required_items(
            self.logic.requirements, self.inventory
        )

        # Initialize item related attributes.
        self.progress_items = {
            item
            for item in randosettings.must_be_placed_items
            | randosettings.may_be_placed_items
            if truly_progress_item[EXTENDED_ITEM[item]]
        }

    def randomize(self):
        # The order of operations is a guess at this point
        progress_list = list(self.progress_items)
        self.rng.shuffle(progress_list)

        for item in progress_list:
            self.place_item(item)

        for i, (e, _) in self.logic.pools:
            for _ in range(len(e)):
                self.link(i)

        must_be_placed_items = list(
            self.randosettings.must_be_placed_items - self.progress_items
        )
        may_be_placed_items = list(
            self.randosettings.may_be_placed_items - self.progress_items
        )
        self.rng.shuffle(must_be_placed_items)
        self.rng.shuffle(may_be_placed_items)

        self.logic.add_item(EXTENDED_ITEM.banned_bit())
        self.fill_inventory()
        for item in must_be_placed_items:
            self.place_item(item)
        for item in may_be_placed_items:
            if not self.place_item(item, force=False):
                break
        self.fill_with_junk(self.randosettings.duplicable_items)

    def fill_with_junk(self, junk):
        empty_locations = [
            loc
            for loc in self.logic.accessible_checks(self.areas[""])
            if loc not in self.logic.placement.locations
        ]

        for location in empty_locations:
            result = self.logic.place_item(location, self.rng.choice(junk))
            assert result

    def place_item(self, item, depth=0, force=True):
        self.logic.remove_item(item)
        placement_limit = self.logic.placement.item_placement_limit.get(item, "")
        accessible_locations = list(self.logic.accessible_checks(placement_limit))

        empty_locations = [
            loc
            for loc in accessible_locations
            if loc not in self.logic.placement.locations
        ]

        if empty_locations:
            result = self.logic.place_item(self.rng.choice(empty_locations), item)
            assert result  # Undefined if False
            return True

        # We have to replace an already placed item
        if not force:
            return False
        assert accessible_locations
        new_item = self.logic.replace_item(self.rng.choice(accessible_locations), item)
        return self.place_item(item, depth + 1)

    def link(self, pool: int, entrance=None, depth=0):
        entrance_pool, exit_pool = self.logic.pools[pool]
        unassigned_entrances = [
            entrance
            for entrance in entrance_pool
            if entrance.entrance not in self.logic.placement.reverse_map_transitions
        ]
        if entrance is None:
            entrance = self.rng.choice(unassigned_entrances)
        else:
            assert entrance in unassigned_entrances

        accessible_exits = list(self.logic.accessible_exits(exit_pool))
        unassigned_exits, assigned_exits = [], []
        for exit in accessible_exits:
            if exit.exit in self.logic.placement.map_transitions:
                assigned_exits.append(exit)
            else:
                unassigned_exits.append(exit)
        self.rng.shuffle(unassigned_exits)

        for exit in unassigned_exits:
            result = self.logic.link_connection(exit, entrance, pool)
            if result:
                return

        # No unassigned exit works, so we try with already assigned exits
        self.rng.shuffle(assigned_exits)
        for exit in unassigned_exits:
            result = self.logic.relink_connection(exit, entrance, pool)
            if result:
                self.link(pool, result, depth + 1)

        raise ValueError("No exit could be found for the entrance")