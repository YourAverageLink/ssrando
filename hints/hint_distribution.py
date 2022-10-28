from __future__ import annotations
from collections import defaultdict
import json
from random import Random
from graph_logic.inventory import EXTENDED_ITEM
from graph_logic.logic_input import Areas

from graph_logic.constants import *
from hints.hint_types import *
from options import Options
from paths import RANDO_ROOT_PATH
from graph_logic.randomize import LogicUtils


HINTABLE_ITEMS = (
    dict.fromkeys(
        [
            CLAWSHOTS,
            EMERALD_TABLET,
            RUBY_TABLET,
            AMBER_TABLET,
            GODDESS_HARP,
            WATER_SCALE,
            FIRESHIELD_EARRINGS,
        ]
    )
    | PROGRESSIVE_BEETLES
    | PROGRESSIVE_SWORDS
)

with open(RANDO_ROOT_PATH / f"hints/junk_hints.json") as f:
    JUNK_TEXT = json.load(f)


class InvalidHintDistribution(Exception):
    pass


class HintDistribution:
    def __init__(self):
        self.hints_per_stone = 0
        self.banned_stones = []
        self.added_locations = []
        self.removed_locations = []
        self.added_items = []
        self.removed_items = []
        self.dungeon_sots_limit = 0
        self.sots_dungeon_placed = 0
        self.dungeon_barren_limit = 0
        self.distribution = {}
        self.goal_index = 0
        self.barren_overworld_zones = []
        self.placed_ow_barren = 0
        self.barren_dungeons = []
        self.placed_dungeon_barren = 0
        self.prev_barren_type = None
        self.hinted_locations = []
        self.barren_hinted_areas = set()
        self.counts_by_type = defaultdict(int)

        self.hintfuncs = {
            "always": self._create_always_hint,
            "sometimes": self._create_sometimes_hint,
            "sots": self._create_sots_hint,
            "goal": self._create_goal_hint,
            "barren": self._create_barren_hint,
            "item": self._create_item_hint,
            "random": self._create_random_hint,
            "junk": self._create_junk_hint,
            "bk": self._create_bk_hint,
        }

    def read_from_file(self, f):
        self._read_from_json(json.load(f))

    def read_from_str(self, s):
        self._read_from_json(json.loads(s))

    def _read_from_json(self, jsn):
        self.hints_per_stone = jsn["hints_per_stone"]
        # Limit number of hints per stone as there appears to be ~600 character limit to the hintstone text.
        if self.hints_per_stone <= 0 or self.hints_per_stone >= 9:
            raise ValueError(
                "Selected hint distribution must have no less than one hint per stone and no more than 8."
            )
        self.banned_stones = jsn["banned_stones"]
        self.added_locations = jsn["added_locations"]
        self.removed_locations = jsn["removed_locations"]
        self.added_items = jsn["added_items"]
        self.removed_items = jsn["removed_items"]
        self.dungeon_sots_limit = jsn["dungeon_sots_limit"]
        self.dungeon_barren_limit = jsn["dungeon_barren_limit"]
        self.distribution = jsn["distribution"]

    """
    Performs initial calculations and populates the distributions internal
    tracking mechanisms for hint generation
    """

    def start(
        self,
        areas: Areas,
        options: Options,
        logic: LogicUtils,
        rng: Random,
        unhintable: List[EIN],
        always_hints: List[EIN],
        sometimes_hints: List[EIN],
    ):
        self.rng = rng
        self.logic = logic
        self.areas = areas
        self.options = options

        self.hinted_locations.extend(unhintable)

        self.banned_stones = list(map(areas.short_to_full, self.banned_stones))
        self.max_hints_per_stone = {
            stone: 0 if stone in self.banned_stones else self.hints_per_stone
            for stone in self.areas.gossip_stones
        }
        self.nb_hints = sum(self.max_hints_per_stone.values())
        assert self.nb_hints <= MAX_HINTS

        for loc in self.added_locations:
            location = areas.short_to_full(loc["location"])
            if loc["type"] == "always":
                if location in always_hints:
                    continue
                always_hints.append(location)
                if location in sometimes_hints:
                    sometimes_hints.remove(location)
            elif loc["type"] == "sometimes":
                if location in sometimes_hints:
                    continue
                sometimes_hints.append(location)
                if location in always_hints:
                    always_hints.remove(location)

        for loc in self.removed_locations:
            loc = areas.short_to_full(loc)
            if loc in always_hints:
                always_hints.remove(loc)
            if loc in sometimes_hints:
                sometimes_hints.remove(loc)

        self.rng.shuffle(always_hints)
        self.rng.shuffle(sometimes_hints)
        self.always_hints = always_hints
        self.sometimes_hints = sometimes_hints

        # creates a list of boss key locations for required dungeons
        self.required_boss_keys = [
            boss_key
            for dungeon in self.logic.required_dungeons
            for boss_key in BOSS_KEYS[dungeon]
        ]
        self.rng.shuffle(self.required_boss_keys)

        # populate our internal list copies for later manipulation
        self.sots_locations = list(self.logic.get_sots_locations())
        self.rng.shuffle(self.sots_locations)

        self.goals = [
            DUNGEON_GOALS[dungeon] for dungeon in self.logic.required_dungeons
        ]
        # shuffle the goal names that will be chosen in sequence when goal hints are placed to try to ensure one is placed for each goal
        self.rng.shuffle(self.goals)
        # create corresponding list of shuffled goal items

        self.goal_locations = []
        for goal in self.goals:
            check = areas.short_to_full(GOAL_CHECKS[goal])
            goal_locations = list(self.logic.get_sots_locations(EXTENDED_ITEM[check]))
            self.rng.shuffle(goal_locations)
            self.goal_locations.append(goal_locations)

        self.hintable_items = list(HINTABLE_ITEMS)
        for item in self.added_items:
            self.hintable_items.extend([item["name"]] * item["amount"])
        if SEA_CHART in self.logic.get_useful_items():
            self.hintable_items.append(SEA_CHART)
        for item in self.removed_items:
            if (loc := self.logic.placement.items[item]) not in self.hinted_locations:
                self.hinted_locations.append(loc)
            if item in self.hintable_items:
                self.hintable_items.remove(item)
        self.rng.shuffle(self.hintable_items)

        region_barren, nonprogress = self.logic.get_barren_regions()
        for zone in region_barren:
            if all(
                loc in self.hinted_locations
                for loc in self.logic.locations_by_hint_region(zone)
            ):
                continue

            if zone in ALL_DUNGEONS:
                self.barren_dungeons.append(zone)
            else:
                self.barren_overworld_zones.append(zone)

        # for each fixed goal hint, place one for each required dungeon
        if "goal" in self.distribution.keys():
            self.distribution["goal"]["fixed"] *= len(self.logic.required_dungeons)
        # all always hints are always hinted
        self.distribution["always"]["fixed"] = len(self.always_hints)

        needed_fixed = []
        for hint_type in self.distribution.keys():
            if self.distribution[hint_type]["fixed"] > 0:
                needed_fixed.append(hint_type)
        needed_fixed.sort(key=lambda type: self.distribution[type]["order"])

        self.junk_hints = JUNK_TEXT.copy()
        self.rng.shuffle(self.junk_hints)

        self.hints = []
        for hint_type in needed_fixed:
            curr_type = self.distribution[hint_type]
            func = self.hintfuncs[hint_type]
            for _ in range(curr_type["fixed"]):
                if (loc := func()) is not None:
                    self.counts_by_type[hint_type] += 1
                    self.hints.extend([loc] * curr_type["copies"])

        self.weighted_types = []
        self.weights = []
        for hint_type in self.distribution.keys():
            self.weighted_types.append(hint_type)
            self.weights.append(self.distribution[hint_type]["weight"])

    """
    Uses the distribution to calculate all the hints
    """

    def get_hints(self) -> List[GossipStoneHint]:
        hints = self.hints
        count = self.nb_hints
        while len(hints) < count:
            [hint_type] = self.rng.choices(self.weighted_types, self.weights)
            func = self.hintfuncs[hint_type]
            limit = self.distribution[hint_type].get("max")

            if limit is not None and self.counts_by_type[hint_type] >= limit:
                continue

            if (hint := func()) is not None:
                self.counts_by_type[hint_type] += 1
                hints.extend([hint] * self.distribution[hint_type]["copies"])

        hints = hints[:count]
        return hints

    def _create_always_hint(self):
        if not self.always_hints:
            return None

        loc = self.always_hints.pop()
        item = self.logic.placement.locations[loc]
        text = self.areas.checks[loc].get("text")

        if loc in self.hinted_locations:
            return self._create_always_hint()
        self.hinted_locations.append(loc)

        silent_realm_checks_rev = SILENT_REALM_CHECKS_REV(self.areas.short_to_full)
        trial_rando = self.options["randomize-trials"]

        if trial_rando and loc in silent_realm_checks_rev:
            trial = silent_realm_checks_rev[loc]
            trial_gate = {
                v: k for k, v in self.logic.randomized_trial_entrance.items()
            }[trial]
            return TrialGateGossipStoneHint(loc, item, trial_gate)
        else:
            return LocationGossipStoneHint("always", loc, item, text)

    def _create_sometimes_hint(self):
        if not self.sometimes_hints:
            return None

        loc = self.sometimes_hints.pop()
        item = self.logic.placement.locations[loc]
        text = self.areas.checks[loc].get("text")

        if loc in self.hinted_locations:
            return self._create_sometimes_hint()
        self.hinted_locations.append(loc)

        return LocationGossipStoneHint("sometimes", loc, item, text)

    def _create_bk_hint(self):
        if not self.required_boss_keys:
            return None

        item = self.required_boss_keys.pop()
        loc = self.logic.placement.items[item]
        text = self.areas.checks[loc].get("text")

        if loc in self.hinted_locations:
            return self._create_bk_hint()
        self.hinted_locations.append(loc)

        return LocationGossipStoneHint("boss_key", loc, item, text)

    def _create_item_hint(self):
        if not self.hintable_items:
            return None

        item = self.hintable_items.pop()
        location = self.logic.placement.items[item]

        if location in self.hinted_locations:
            return self._create_item_hint()
        self.hinted_locations.append(location)

        if self.options["precise-item"]:
            text = self.areas.checks[location].get("text")
            return LocationGossipStoneHint("precise_item", location, item, text)

        if (zone_override := self.areas.checks[location].get("cube_region")) is None:
            zone_override = self.areas.checks[location]["hint_region"]

        return ZoneItemGossipStoneHint(location, item, zone_override)

    def _create_random_hint(self):
        all_locations_without_hint = [
            loc
            for loc in self.logic.placement.locations
            if loc not in self.hinted_locations
            and self.areas.checks[loc]["hint_region"] not in self.barren_hinted_areas
            and EXTENDED_ITEM[loc] in self.logic.fill_restricted()
        ]

        assert all_locations_without_hint

        loc = self.rng.choice(all_locations_without_hint)
        item = self.logic.placement.locations[loc]
        text = self.areas.checks[loc].get("text")
        self.hinted_locations.append(loc)

        return LocationGossipStoneHint("random", loc, item, text)

    def _create_sots_goal_hint(self, goal_mode=False):
        if goal_mode:
            locs = self.goal_locations[self.goal_index]
        else:
            locs = self.sots_locations

        if not locs:
            if not goal_mode:
                return None
            # if there aren't applicable locations for any goal, return None
            if not any(self.goal_locations):
                return None
            # go to next goal if no locations are left for this goal
            self.goal_index += 1
            self.goal_index %= len(self.goals)
            return self._create_sots_goal_hint(goal_mode)

        zone, loc, item = locs.pop()

        if loc in self.hinted_locations:
            return self._create_sots_goal_hint(goal_mode)

        if self.sots_dungeon_placed >= self.dungeon_sots_limit and zone in ALL_DUNGEONS:
            return self._create_sots_goal_hint(goal_mode)

        if zone in ALL_DUNGEONS:
            # goal hints will use the same dungeon limits as sots hints
            self.sots_dungeon_placed += 1

        self.hinted_locations.append(loc)

        if goal_mode:
            # move to next goal boss for next goal hint
            goal = self.goals[self.goal_index]
            self.goal_index += 1
            self.goal_index %= len(self.goals)
        else:
            goal = None

        if (zone := self.areas.checks[loc].get("cube_region")) is not None:
            # place cube sots hint & catch specific zones and fit them into their general zone (as seen in the cube progress options)
            if self.options["cube-sots"]:
                if zone == SV:
                    zone = FARON_WOODS
                elif zone == MOGMA_TURF:
                    zone = ELDIN_VOLCANO
                elif zone == LANAYRU_MINES:
                    zone = LANAYRU_DESERT
                elif zone == LANAYRU_GORGE:
                    zone = SAND_SEA
                return CubeSotsGoalGossipStoneHint(loc, item, zone, goal)
        zone = self.areas.checks[loc]["hint_region"]
        return SotsGoalGossipStoneHint(loc, item, zone, goal)

    def _create_sots_hint(self):
        return self._create_sots_goal_hint(goal_mode=False)

    def _create_goal_hint(self):
        return self._create_sots_goal_hint(goal_mode=True)

    def _create_barren_hint(self):
        # weights = (dungeon_weight, overworld_weight)
        if self.prev_barren_type is None:
            # 50/50 between dungeon and overworld on the first hint
            weights = (1, 1)
        elif self.prev_barren_type == "dungeon":
            weights = (1, 3)
        elif self.prev_barren_type == "overworld":
            weights = (3, 1)
        else:
            assert False

        barren_type = self.rng.choices(["dungeon", "overworld"], weights)[0]

        # Check against caps
        if self.placed_dungeon_barren > self.dungeon_barren_limit:
            barren_type = "overworld"

        # Failsafes if there are not enough barren hints to fill out the generated hint
        for barren_area_list in (self.barren_dungeons, self.barren_overworld_zones):
            for region in barren_area_list:
                if not len(self.logic.locations_by_hint_region(region)):
                    barren_area_list.remove(region)

        if len(self.barren_dungeons) == 0:
            if len(self.barren_overworld_zones) == 0:
                return None
            barren_type = "overworld"
        if len(self.barren_overworld_zones) == 0:
            barren_type = "dungeon"

        # generate a hint and remove it from the lists
        if barren_type == "dungeon":
            barren_area_list = self.barren_dungeons
        else:
            barren_area_list = self.barren_overworld_zones

        weights = [
            len(self.logic.locations_by_hint_region(area)) for area in barren_area_list
        ]

        area = self.rng.choices(barren_area_list, weights)[0]
        barren_area_list.remove(area)
        self.barren_hinted_areas.add(area)
        self.prev_barren_type = barren_type

        return BarrenGossipStoneHint(area)

    def _create_junk_hint(self):
        return EmptyGossipStoneHint(self.rng.choice(self.junk_hints))

    def get_junk_text(self):
        return self.junk_hints.pop()
