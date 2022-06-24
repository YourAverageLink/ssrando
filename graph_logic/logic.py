from __future__ import annotations
from functools import cache
from typing import Any, Dict, Iterable, List, Tuple
from collections import defaultdict
from dataclasses import dataclass, field

from .constants import *
from .logic_input import Area, Areas, DayOnly, NightOnly, Both
from .logic_expression import DNFInventory, AndCombination, OrCombination
from .inventory import Inventory, EXTENDED_ITEM


@dataclass
class PoolEntrance:
    entrance: EXTENDED_ITEM_NAME
    constraints: List[EXTENDED_ITEM_NAME] = field(default_factory=list)


@dataclass
class PoolExit:
    exit: EXTENDED_ITEM_NAME
    constraints: List[EXTENDED_ITEM_NAME] = field(default_factory=list)


@dataclass
class Placement:
    item_placement_limit: Dict[EXTENDED_ITEM_NAME, EXTENDED_ITEM_NAME] = field(
        default_factory=lambda: defaultdict(lambda: EIN(str()))
    )

    map_transitions: Dict[EIN, EIN] = field(default_factory=dict)
    reverse_map_transitions: Dict[EIN, EIN] = field(default_factory=dict)

    locations: Dict[EIN, EIN] = field(default_factory=dict)
    items: Dict[EXTENDED_ITEM_NAME, EXTENDED_ITEM_NAME] = field(default_factory=dict)
    hints: Dict[EXTENDED_ITEM_NAME, Any] = field(default_factory=dict)
    # hints: Dict[str, "Hint"] = field(default_factory=dict)

    def copy(self):
        return Placement(
            self.item_placement_limit.copy(),
            self.map_transitions.copy(),
            self.reverse_map_transitions.copy(),
            self.locations.copy(),
            self.items.copy(),
            self.hints.copy(),
        )

    def __or__(self, other):
        if not isinstance(other, Placement):
            raise ValueError
        for k, v in other.item_placement_limit.items():
            if k in self.item_placement_limit and v != self.item_placement_limit[k]:
                raise ValueError
        for k, v in other.map_transitions.items():
            if k in self.map_transitions and v != self.map_transitions[k]:
                raise ValueError
        for k, v in other.reverse_map_transitions.items():
            if (
                k in self.reverse_map_transitions
                and v != self.reverse_map_transitions[k]
            ):
                raise ValueError
        for k, v in other.locations.items():
            if k in self.locations and v != self.locations[k]:
                raise ValueError
        for k, v in other.items.items():
            if k in self.items and v != self.items[k]:
                raise ValueError
        for k, v in other.hints.items():
            if k in self.hints and v != self.hints[k]:
                raise ValueError
        return Placement(
            self.item_placement_limit | other.item_placement_limit,
            self.map_transitions | other.map_transitions,
            self.reverse_map_transitions | other.reverse_map_transitions,
            self.locations | other.locations,
            self.items | other.items,
            self.hints | other.hints,
        )


@dataclass
class LogicSettings:
    exit_pools: List[
        Tuple[
            Dict[EXTENDED_ITEM_NAME, PoolEntrance], Dict[EXTENDED_ITEM_NAME, PoolExit]
        ]
    ]
    starting_inventory: Inventory
    starting_area: EXTENDED_ITEM_NAME
    additional_requirements: Dict[str, DNFInventory]


def make_exit_pool(i: int) -> EXTENDED_ITEM_NAME:
    return EIN(f"Exit pool {i}")


class Logic:
    def __init__(
        self,
        areas: Areas,
        logic_settings: LogicSettings,
        placement: Placement | None = None,
        # remove_placed_from_inv=False,
        # acc_areas_default=False,
    ):
        self.areas = areas
        self.map_exits = areas.map_exits
        self.checks = areas.checks
        self.pools = logic_settings.exit_pools
        self.short_to_full = areas.short_to_full
        self.full_to_short = areas.full_to_short

        self.requirements = areas.requirements.copy()
        self.opaque = areas.opaque
        self.entrance_allowed_time_of_day = areas.entrance_allowed_time_of_day
        self.exit_to_area = areas.exit_to_area

        for loc, req in logic_settings.additional_requirements.items():
            self.requirements[EXTENDED_ITEM[self.short_to_full(loc)]] &= req
        self.placement = placement.copy() if placement is not None else Placement()

        starting_area_bit = EXTENDED_ITEM[logic_settings.starting_area]
        self.inventory = logic_settings.starting_inventory.add(starting_area_bit)
        self.accessibility_check_bit = starting_area_bit

        for i, (entrances, exits) in enumerate(self.pools):
            EXTENDED_ITEM.items_list.append(make_exit_pool(i))
            self.requirements.append(DNFInventory())
            self.opaque.append(True)
            pool_as_req = DNFInventory(make_exit_pool(i))
            for entrance in entrances:
                full_entrance = self.short_to_full(entrance)
                if self.entrance_allowed_time_of_day[full_entrance] == Both:
                    bits = [
                        EXTENDED_ITEM[make_day(full_entrance)],
                        EXTENDED_ITEM[make_night(full_entrance)],
                    ]
                else:
                    bits = [EXTENDED_ITEM[full_entrance]]
                for entrance_bit in bits:
                    self.requirements[entrance_bit] = pool_as_req
                    self.opaque[entrance_bit] = True

            pool_as_loc = EXTENDED_ITEM[make_exit_pool(i)]
            for exit in exits:
                self.requirements[pool_as_loc] |= DNFInventory(self.short_to_full(exit))

        self.backup_requirements = self.requirements.copy()

        for exit, entrance in self.placement.map_transitions.items():
            pool = None
            for i, (ent_pool, exit_pool) in enumerate(self.pools):
                if exit in exit_pool:
                    pool = i
                    break
            self._link_connection(exit, entrance, pool)

        self.full_inventory = self.inventory
        for k, v in self.placement.locations.items():
            self._place_item(k, v)

        self.shallow_simplify()
        self.backup_requirements = self.requirements.copy()
        self.aggregate = self.aggregate_required_items(
            self.requirements, self.full_inventory
        )

    def add_item(self, item: EXTENDED_ITEM | str):
        self.inventory.add(item)
        self.fill_inventory(monotonic=True)

    def remove_item(self, item: EXTENDED_ITEM):
        self.inventory = self.inventory.remove(item)
        if Inventory(item) <= self.aggregate:
            self.fill_inventory()

    @staticmethod
    def _deep_simplify(requirements, opaques):
        simplified = [False for _ in requirements]
        visited = [False for _ in requirements]
        hit_a_visited = False

        def simplify(item):
            nonlocal hit_a_visited
            if opaques[item]:
                return DNFInventory(item)

            if visited[item]:
                hit_a_visited = True
                return DNFInventory(item)

            if simplified[item]:
                return requirements[item]

            visited[item] = True
            simplified_disj = []
            for possibility in requirements[item].disjunction:
                simplified_conj = []
                for req_item in possibility.intset:
                    simplified_conj.append(simplify(req_item))
                simplified_disj.append(AndCombination.simplifyDNF(simplified_conj))

            result = OrCombination.simplifyDNF(simplified_disj).remove(item)
            if not hit_a_visited:
                requirements[item] = result
                simplified[item] = True
            visited[item] = False
            return result

        for item in range(len(requirements)):
            hit_a_visited = False
            requirements[item] = simplify(item)
            simplified[item] = True

    def deep_simplify(self):
        self._deep_simplify(self.requirements, self.opaque)

    @staticmethod
    def _shallow_simplify(requirements, opaques):
        simplifiables = Inventory(
            {
                item
                for item in EXTENDED_ITEM.items()
                if len(requirements[item].disjunction) <= 1
            }
        )

        for item, req in enumerate(requirements):
            if opaques[item] or len(req.disjunction) >= 30:
                continue
            new_req = DNFInventory()
            for conj in req.disjunction:
                if conj & simplifiables:
                    new_conj = Inventory()
                    skip = False
                    for req_item in conj.intset:
                        if opaques[req_item] or not simplifiables[req_item]:
                            new_conj |= Inventory(req_item)
                        else:
                            req_item_req = requirements[req_item].disjunction
                            if not req_item_req:
                                skip = True
                                break
                            (req_item_conj,) = req_item_req
                            new_conj |= req_item_conj
                    if not skip and not new_conj[EXTENDED_ITEM(item)]:
                        new_req |= DNFInventory(new_conj)
                else:
                    new_req |= conj
            requirements[item] = new_req

    def shallow_simplify(self):
        self._shallow_simplify(self.requirements, self.opaque)

    @staticmethod
    def aggregate_required_items(
        requirements: List[DNFInventory], inventory: Inventory
    ):
        full_inventory = Logic._fill_inventory(requirements, inventory)
        aggregate = Inventory()

        for item in EXTENDED_ITEM.items():
            if full_inventory[item]:
                for conj in requirements[item].disjunction:
                    aggregate |= conj

        return aggregate

    @staticmethod
    def _fill_inventory(requirements: List[DNFInventory], inventory: Inventory):
        keep_going = True
        while keep_going:
            keep_going = False
            for i in EXTENDED_ITEM.items():
                if not inventory[i] and requirements[i].eval(inventory):
                    inventory |= i
                    keep_going = True
        return inventory

    def fill_inventory(self, monotonic=False):
        # self.shallow_simplify()
        inventory = self.full_inventory if monotonic else self.inventory
        self.full_inventory = self._fill_inventory(self.requirements, inventory)

    @staticmethod
    def explore(checks, area: Area) -> Iterable[EIN]:
        def explore(area):
            for loc in area.locations:
                loc_full = with_sep_full(area.name, loc)
                if loc_full in checks:
                    yield loc_full
            for sub_area in area.sub_areas.values():
                yield from explore(sub_area)

        return explore(area)

    @cache
    def check_list(self, placement_limit: str) -> List[EIN]:
        return list(
            self.explore(self.checks, self.areas[self.short_to_full(placement_limit)])
        )

    def accessible_checks(self, placement_limit: str) -> List[str]:
        if placement_limit in self.checks:
            placement_limit, loc = placement_limit.rsplit("/", 1)
            locations = self.areas[placement_limit].locations
            assert loc in locations
            return [placement_limit]
        else:
            return [
                self.full_to_short(loc)
                for loc in self.check_list(placement_limit)
                if self.full_inventory[EXTENDED_ITEM[loc]]
            ]

    def accessible_exits(self, exit_pool: Iterable[PoolExit]) -> Iterable[PoolExit]:
        for exit in exit_pool:
            exit_full = self.short_to_full(exit.exit)
            if exit_full in self.map_exits:
                if self.full_inventory[EXTENDED_ITEM[exit_full]]:
                    yield exit

    def _link_connection(self, exit: EIN, entrance: EIN, pool=None, requirements=None):
        full_entrance = self.short_to_full(entrance)
        allowed_times = self.entrance_allowed_time_of_day[full_entrance]
        full_exit = self.short_to_full(exit)
        exit_bit = EXTENDED_ITEM[full_exit]
        exit_area = self.exit_to_area[full_exit]
        exit_as_req = DNFInventory(exit_bit)

        if exit_area.abstract:
            day_req = exit_as_req
            night_req = exit_as_req
        elif exit_area.allowed_time_of_day == Both:
            day_req = exit_as_req & DNFInventory(
                EXTENDED_ITEM[make_day(exit_area.name)]
            )
            night_req = exit_as_req & DNFInventory(
                EXTENDED_ITEM[make_night(exit_area.name)]
            )
        elif exit_area.allowed_time_of_day == DayOnly:
            day_req = exit_as_req & DNFInventory(EXTENDED_ITEM[exit_area.name])
            night_req = DNFInventory()
        else:
            day_req = DNFInventory()
            night_req = exit_as_req & DNFInventory(EXTENDED_ITEM[exit_area.name])

        if allowed_times == Both:
            bit_req = [
                (EXTENDED_ITEM[make_day(full_entrance)], day_req),
                (EXTENDED_ITEM[make_night(full_entrance)], night_req),
            ]
        elif allowed_times == DayOnly:
            bit_req = [(EXTENDED_ITEM[full_entrance], day_req)]
        else:
            bit_req = [(EXTENDED_ITEM[full_entrance], night_req)]

        if requirements is None:
            self.placement.map_transitions[exit] = entrance
            self.placement.reverse_map_transitions[entrance] = exit
            for bit, req in bit_req:
                self.opaque[bit] = False
                self.requirements[bit] |= req
                self.backup_requirements[bit] |= req
        else:
            for bit, req in bit_req:
                requirements[bit] = req

        if pool is None or True:
            return
        index = EXTENDED_ITEM[f"Exit pool #{pool}"]
        if requirements is None:
            self.requirements[index] = self.requirements[index].remove(exit_bit)
            self.backup_requirements[index] = self.backup_requirements[index].remove(
                exit_bit
            )
        else:
            requirements[index] = requirements[index].remove(exit_bit)

    def _link_connection_group(
        self, exit: PoolExit, entrance: PoolEntrance, pool=None, requirements=None
    ):
        self._link_connection(exit.exit, entrance.entrance, pool, requirements)
        for conn1, conn2 in zip(exit.constraints, entrance.constraints):
            exit_str, entrance_str = Logic.order_entrance_exit(conn1, conn2)
            self._link_connection(exit_str, entrance_str, pool, requirements)

    def can_link(self, exit, entrance, requirements_linked, check_already_linked=True):
        exit, entrance = Logic.order_entrance_exit(exit, entrance)
        if not check_already_linked:
            if (
                entrance in self.placement.reverse_map_transitions
                or exit in self.placement.map_transitions
            ):
                return False

        exit_area = self.exit_to_area[self.short_to_full(exit)]
        full_inventory = self._fill_inventory(requirements_linked, Inventory(exit_area))

        return full_inventory[self.accessibility_check_bit]

    def link_connection(self, exit: PoolExit, entrance: PoolEntrance, pool: int):
        """Assumes that the poll is restrictive enough that constraintss are always compatible"""
        requirements_linked = self.requirements.copy()
        self._link_connection_group(exit, entrance, pool, requirements_linked)

        if not (
            self.can_link(exit.exit, entrance.entrance, requirements_linked)
            and all(
                self.can_link(exit, entrance, requirements_linked)
                for exit, entrance in zip(exit.constraints, entrance.constraints)
            )
        ):
            return False
        self._link_connection_group(exit, entrance, pool)
        return True

    def relink_connection(self, exit: PoolExit, entrance: PoolEntrance, pool: int):
        """Link occupied exit to entrance, returning old linked entrance"""
        requirements_linked = self.requirements.copy()
        self._link_connection_group(exit, entrance, pool, requirements_linked)

        if not (
            self.can_link(
                exit.exit,
                entrance.entrance,
                requirements_linked,
                check_already_linked=False,
            )
            and all(
                self.can_link(
                    exit, entrance, requirements_linked, check_already_linked=False
                )
                for exit, entrance in zip(exit.constraints, entrance.constraints)
            )
        ):
            return False  # raise ValueError("Cannot link these")

        def all_entrance_bits(full_entrance):
            if self.entrance_allowed_time_of_day[full_entrance] == Both:
                return [
                    EXTENDED_ITEM[make_day(full_entrance)],
                    EXTENDED_ITEM[make_night(full_entrance)],
                ]
            else:
                return [EXTENDED_ITEM[full_entrance]]

        old_entrance = self.placement.map_transitions[exit.exit]
        del self.placement.map_transitions[exit.exit]
        del self.placement.reverse_map_transitions[old_entrance]
        for old_entrance_bit in all_entrance_bits(self.short_to_full(old_entrance)):
            self.opaque[old_entrance_bit] = True
            self.backup_requirements[old_entrance_bit] = DNFInventory(
                make_exit_pool(pool)
            )
        old_entrance_full = self.pools[pool][0][old_entrance]
        pool_as_loc = EXTENDED_ITEM[f"Exit pool #{pool}"]
        for other_entrance in old_entrance_full.constraints:
            other_entrance = self.short_to_full(other_entrance)
            if is_entrance(other_entrance):
                assoc_exit = self.placement.reverse_map_transitions[other_entrance]
                del self.placement.reverse_map_transitions[other_entrance]
                del self.placement.map_transitions[assoc_exit]

                for other_entrance_bit in all_entrance_bits(other_entrance):
                    self.opaque[other_entrance_bit] = True
                    self.backup_requirements[other_entrance_bit] = DNFInventory(
                        make_exit_pool(pool)
                    )
            else:
                other_exit = other_entrance
                assoc_entrance = self.placement.map_transitions[other_exit]
                del self.placement.reverse_map_transitions[assoc_entrance]
                del self.placement.map_transitions[other_exit]

                self.requirements[pool_as_loc] |= DNFInventory(
                    self.short_to_full(other_exit)
                )
        self.requirements = self.backup_requirements.copy()
        self.fill_inventory()
        self._link_connection_group(exit, entrance, pool)

        return old_entrance_full

    def _place_item(self, location, item):
        full_location = self.short_to_full(location)
        if (
            item in self.placement.item_placement_limit
            and not full_location.startswith(
                self.areas.search_area("", self.placement.item_placement_limit[item])
            )
        ):
            raise ValueError(
                "This item cannot be placed in this area, "
                f"it must be placed in {self.placement.item_placement_limit[item]}"
            )
        if item in EXTENDED_ITEM:
            item_bit = EXTENDED_ITEM[item]
            self.requirements[item_bit] = DNFInventory(full_location)
            self.backup_requirements[item_bit] = DNFInventory(full_location)
            self.opaque[item_bit] = False
            self.fill_inventory(monotonic=True)
            self.placement.items[item] = location

        self.placement.locations[location] = item

    def place_item(self, location, item):
        if location in self.placement.locations:
            raise ValueError(f"Location {location} is already taken")
        if item in self.placement.items:
            raise ValueError(f"Item {item} is already placed")
        self._place_item(location, item)
        return True

    def replace_item(self, location, item):
        if location not in self.placement.locations:
            raise ValueError(f"Location {location} is not taken")
        if item in self.placement.items:
            raise ValueError(f"Item {item} is already placed")
        old_item = self.placement.locations[location]
        del self.placement.locations[location]
        del self.placement.items[old_item]

        if old_item in EXTENDED_ITEM:
            # We should always be in this case
            old_item_bit = EXTENDED_ITEM[old_item]
            self.opaque[old_item_bit] = True
            self.backup_requirements[old_item_bit] = DNFInventory()
            self.requirements = self.backup_requirements.copy()
            self.fill_inventory()

        self.place_item(location, item)
        return old_item

    @cache
    def _fill_for_test(self, banned_intset, inventory):
        custom_requirements = self.requirements.copy()
        for index, e in enumerate(reversed(bin(banned_intset))):
            if e == "1":
                custom_requirements[index] = DNFInventory(False)

        return self._fill_inventory(custom_requirements, inventory)

    def fill_restricted(
        self,
        banned_indices: List[EXTENDED_ITEM] = [],
        starting_inventory: None | Inventory = None,
    ):
        if starting_inventory is None:
            starting_inventory = self.inventory

        banned_intset = 0
        for i in banned_indices:
            banned_intset += 1 << i

        return self._fill_for_test(banned_intset, self.inventory)

    def restricted_test(
        self,
        test_index,
        banned_indices: List[EXTENDED_ITEM] = [],
        starting_inventory: None | Inventory = None,
    ):
        if starting_inventory is None:
            starting_inventory = self.inventory

        banned_intset = 0
        for i in banned_indices:
            banned_intset += 1 << i

        restricted_full = self._fill_for_test(banned_intset, self.inventory)

        return restricted_full[test_index]