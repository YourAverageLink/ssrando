from graph_logic.constants import *
from graph_logic.inventory import EXTENDED_ITEM
from graph_logic.logic import DNFInventory
from graph_logic.logic_input import Areas
from hints.hint_distribution import HintDistribution
from hints.hint_types import *
from .randomize import LogicUtils, UserOutput
from options import Options
from paths import RANDO_ROOT_PATH
from typing import Dict, List


class Hints:
    def __init__(self, options: Options, rng, areas: Areas, logic: LogicUtils):
        self.logic = logic
        self.areas = areas
        self.norm = areas.short_to_full
        self.placement = logic.placement
        self.options = options
        self.rng = rng

        with open(
            RANDO_ROOT_PATH
            / f"hints/distributions/{self.options['hint-distribution']}.json"
        ) as f:
            self.dist = HintDistribution()
            self.dist.read_from_file(f)

    def do_hints(self, useroutput: UserOutput):
        self.useroutput = useroutput

        not_banned = self.logic.fill_restricted()
        needed_always_hints: List[EIN] = [
            loc
            for loc, check in self.areas.checks.items()
            if check.get("hint") == "always" and not_banned[check["req_index"]]
        ]
        needed_sometimes_hints = [
            loc
            for loc, check in self.areas.checks.items()
            if check.get("hint") == "sometimes" and not_banned[check["req_index"]]
        ]

        # ensure prerandomized locations cannot be hinted
        unhintables = list(self.logic.known_locations) + [START_ITEM, UNPLACED_ITEM]

        hint_mode = self.options["song-hints"]
        if hint_mode != "None":
            for check in SILENT_REALM_CHECKS.values():
                unhintables.append(self.norm(check))

        self.placement.trial_hints, self.placement.npc_hints = self.get_miscellaneous_hints() 

        self.dist.start(
            self.areas,
            self.options,
            self.logic,
            self.rng,
            unhintables,
            needed_always_hints,
            needed_sometimes_hints,
        )
        hints = self.dist.get_hints()
        self.useroutput.progress_callback("placing hints...")
        hints = {hintname: hint for hint, hintname in zip(hints, HINTS)}
        self.max_hints_for = self.dist.max_hints_for
        self.randomize(hints)

        return {
            stone: GossipStoneHintWrapper(
                [hints[name] for name in self.logic.placement.stones[stone]]
            )
            for stone in self.areas.gossip_stones
        }
    
    def get_miscellaneous_hints(self):
        trial_hintnames = {
            # (getting it text patch, inventory text line)
            SKYLOFT_TRIAL_GATE: EIN("Song of the Hero - Trial Hint"),
            FARON_TRIAL_GATE: EIN("Farore's Courage - Trial Hint"),
            LANAYRU_TRIAL_GATE: EIN("Nayru's Wisdom - Trial Hint"),
            ELDIN_TRIAL_GATE: EIN("Din's Power - Trial Hint"),
        }
        trial_hints = {}
        hint_mode = self.options["song-hints"]
        # mode for sots/progress/barren hint generalization
        def advanced_hint(item, sots_text, useful_text, useless_text):
            if item in self.logic.get_sots_items():
                return sots_text
            if item in self.logic.get_useful_items():
                return useful_text
            return useless_text

        for (trial_gate, hintname) in trial_hintnames.items():
            randomized_trial = self.logic.randomized_trial_entrance[trial_gate]
            randomized_check = SILENT_REALM_CHECKS[randomized_trial]
            item = self.logic.placement.locations[
                self.areas.short_to_full(randomized_check)
            ]

            if hint_mode == "Basic":
                useful_text = advanced_hint(item,
                    "You might need what it reveals...",
                    "You might need what it reveals...",
                    "It's probably not too important..."
                )
            elif hint_mode == "Advanced":
                useful_text = advanced_hint(item,
                    "Your spirit will grow by completing this trial",
                    "You might need what it reveals...",
                    "It's probably not too important..."
                )
            elif hint_mode == "Direct":
                useful_text = f"This trial holds {item}"
            else:
                useful_text = ""
            trial_hints[hintname] = useful_text

        npc_hints = {
            "Water Dragon's Hint": "",
            "Owlan's Hint": "",
            "Kina's Hint": "",
            "Pumm's Hint": "",
        }
        if self.options["npc-hints"]:
            npc_hints["Water Dragon's Hint"] = advanced_hint(
                self.logic.placement.locations[
                self.areas.short_to_full("Flooded Faron Woods - Water Dragon's Reward")
            ],
                "You're <b<going to need my reward>> to complete your quest!",
                "You <g+<might find my reward useful>>...",
                "Admittedly, I don't have a very enticing reward...",
            )
            npc_hints["Owlan's Hint"] = advanced_hint(
                self.logic.placement.locations[
                self.areas.short_to_full("Knight Academy - Owlan's Crystals")
            ],
                "I promise I will return the favor with an <b<item you need>>!",
                "I'll give you <g+<something you might find useful>> in return!",
                "I'm sorry, I don't have anything very good to reward you with...",
            )
            npc_hints["Kina's Hint"] = advanced_hint(
                self.logic.placement.locations[
                self.areas.short_to_full("Sky - Kina's Crystals")
            ],
                "I'll bet I can give you <b<something you really need>> for helping me!",
                "I could give you a <g+<possibly useful item>> if you help me...",
                "Sorry, kid, I can't give you anything useful, but I'd still appreciate help!",
            )
            npc_hints["Pumm's Hint"] = advanced_hint(
                self.logic.placement.locations[
                self.areas.short_to_full("Thunderhead - Song from Levias")
            ],
                "I think you'll <b<need to deliver my soup>> to Levias!",
                "Levias <g+<might have something useful>> if you help him come to his senses.",
                "I doubt helping Levias will do you much good...",
            )

        return trial_hints, npc_hints

    def randomize(self, hints: Dict[EIN, GossipStoneHint]):
        for hintname, hint in hints.items():
            hint_bit = EXTENDED_ITEM[hintname]
            if isinstance(hint, LocationGossipStoneHint) and hint.item in EXTENDED_ITEM:
                itembit = EXTENDED_ITEM[hint.item]
                hint_req = DNFInventory(hint_bit)
                self.logic.backup_requirements[itembit] &= hint_req
                self.logic.requirements[itembit] &= hint_req

            self.logic.inventory |= hint_bit

        self.logic.aggregate = self.logic.aggregate_requirements(
            self.logic.requirements, None
        )
        self.logic.fill_inventory_i(monotonic=False)

        for hintname in hints:
            if not self.place_hint(hintname):
                raise self.useroutput.GenerationFailed(f"could not place {hintname}")

    def place_hint(self, hintname: EXTENDED_ITEM_NAME, depth=0) -> bool:
        hint_bit = EXTENDED_ITEM[hintname]
        self.logic.remove_item(hint_bit)

        accessible_stones = list(self.logic.accessible_stones())

        available_stones = [
            stone
            for stone in accessible_stones
            for spot in range(
                self.max_hints_for[stone] - len(self.logic.placement.stones[stone])
            )
        ]

        if available_stones:
            stone = self.rng.choice(available_stones)
            result = self.logic.place_item(stone, hintname, hint_mode=True)
            assert result  # Undefined if False
            return True

        # We have to replace an already placed hint
        if depth > 50:
            return False
        if not accessible_stones:
            raise self.useroutput.GenerationFailed(
                f"no more location accessible for {hintname}"
            )

        spots = [
            (stone, old_hint)
            for stone in accessible_stones
            for old_hint in self.placement.stones[stone]
        ]
        stone, old_hint = self.rng.choice(spots)
        old_removed_hint = self.logic.replace_item(stone, hintname, old_hint)
        return self.place_hint(old_removed_hint, depth + 1)
