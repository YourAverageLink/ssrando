import base64
import zipfile
import yaml
import random
import os
from pathlib import Path

from logic.logic_input import Areas
from logic.placement_file import PlacementFile
from options import Options, OPTIONS
from version import VERSION


class Archipelago:
    def __init__(self, apssr: str):
        if os.path.isfile(apssr) and Path(apssr).suffix == ".apssr":
            pass
        else:
            raise Exception("Invalid APSSR file.")

        apdata = self.load_apssr_yaml(apssr)
        self.apversion: list = apdata["AP Version"]
        self.worldversion: list = apdata["World Version"]
        self.hash: str = apdata["Hash"]
        self.apseed: str = apdata["AP Seed"]  # Treat this as a string
        self.randoseed: int = apdata["Rando Seed"]
        self.player: int = apdata["Slot"]
        self.slot_name: str = apdata["Name"]
        self.all_players: list[str] = apdata["All Players"]
        self.options: dict[str, any] = apdata["Options"]
        self.excluded_locations: set = apdata["Excluded Locations"]
        self.starting_items: list = apdata["Starting Items"]
        self.dungeons: list[str] = apdata["Required Dungeons"]
        self.locations: dict[str, dict] = apdata["Locations"]
        self.batreaux_rewards: dict[str, int] = apdata["Batreaux Rewards"]
        self.hints: dict[str, list] = apdata["Hints"]
        self.log_hints: dict[str, list] = apdata["Log Hints"]
        self.impa_hint: tuple[str, str] | None = apdata["SoT Location"]
        self.entrances: list[tuple] = apdata["Entrances"]
        self.trial_connections: dict[str, str] = apdata["Trial Entrances"]
        self.start_statues: dict = apdata["Starting Statues"]
        self.start_entrance: dict = apdata["Starting Entrance"]

        # Check valid APSSR
        if len(self.slot_name) > 16:
            raise Exception("Slot name should be under 16 characters!")
        if len(self.apseed) != 20:
            raise Exception(
                "AP Seed was not 20 characters long. Something went really wrong."
            )
            # Should never happen, but we patch this into 20 bytes in memory so let's be safe
        print(
            f"Skyward Sword AP World Version {self.worldversion[0]}.{self.worldversion[1]}.{self.worldversion[2]}"
        )
        print(f"Patching AP seed {self.apseed} for player {self.slot_name}")

    def fill_placement_file(
        self, options: Options, areas: Areas, rng: random.Random
    ) -> PlacementFile:
        self.placement_file = PlacementFile()
        self.placement_file.version = VERSION
        self.placement_file.options = options
        for optkey, opt in OPTIONS.items():  # Set placement file options
            if "cosmetic" in opt:
                if optkey == "print-client-messages":
                    options.set_option(optkey, False)
                pass
            elif optkey in UNTOUCHED_OPTIONS:
                pass
            elif optkey in FORCED_OPTIONS:
                self.placement_file.options.set_option(optkey, FORCED_OPTIONS[optkey])
                options.set_option(optkey, FORCED_OPTIONS[optkey])
            elif optkey == "excluded-locations":
                self.placement_file.options.set_option(
                    optkey, list(self.excluded_locations)
                )
                options.set_option(optkey, list(self.excluded_locations))
            elif optkey in self.options:
                if opt["type"] == "boolean":
                    self.placement_file.options.set_option(
                        optkey, bool(self.options[optkey])
                    )
                    options.set_option(optkey, bool(self.options[optkey]))
                elif opt["type"] == "singlechoice":
                    self.placement_file.options.set_option(
                        optkey, opt["choices"][self.options[optkey]]
                    )
                    options.set_option(optkey, opt["choices"][self.options[optkey]])
                elif opt["type"] == "int":
                    self.placement_file.options.set_option(optkey, self.options[optkey])
                    options.set_option(optkey, self.options[optkey])
                elif optkey == "starting-items":
                    self.placement_file.options.set_option(optkey, [])
                    options.set_option(optkey, [])
                else:
                    print("unknown type yet found in apssr: " + optkey)
            else:
                print("Could not find a value to set option: " + optkey)
        self.placement_file.hash_str = self.hash
        self.placement_file.starting_items.extend(self.starting_items)
        self.placement_file.required_dungeons.extend(self.dungeons)
        for loc, itm in self.locations.items():
            if itm["player"] != self.player:
                if itm["game"] == "Skyward Sword":
                    if itm["name"] in SS_ARCHIPELAGO_SPECIAL_ITEMS:
                        item_to_place = SS_ARCHIPELAGO_SPECIAL_ITEMS[itm["name"]][0]
                    else:
                        item_to_place = "Archipelago Item"
                else:
                    item_to_place = (
                        "Archipelago Item"  # Represents a general Archipelago item
                    )
            else:
                item_to_place = itm["name"]
            self.placement_file.item_locations[areas.short_to_full(loc)] = item_to_place
            self.placement_file.chest_dowsing[areas.short_to_full(loc)] = (
                self.get_dowsing_slot(itm, options)
            )
        for hint, data in self.hints.items():
            if "Gossip Stone" in hint:
                self.placement_file.hints[areas.short_to_full(hint)] = data
            else:
                self.placement_file.hints[hint] = data
        self.placement_file.entrances = self.entrances
        self.placement_file.trial_connections = self.trial_connections
        self.placement_file.start_statues = self.start_statues
        self.placement_file.start_entrance = self.start_entrance
        self.placement_file.trial_object_seed = rng.randint(1, 1_000_000)
        self.placement_file.music_rando_seed = rng.randint(1, 1_000_000)
        self.placement_file.bk_angle_seed = rng.randint(1, 2**32 - 1)

        return self.placement_file

    def load_apssr_yaml(self, fp) -> dict:
        with zipfile.ZipFile(fp, "r") as apssr:
            with apssr.open("plando") as plando_file:
                plando_encoded = plando_file.read()
        plando_decoded = base64.b64decode(plando_encoded)
        return yaml.safe_load(plando_decoded)

    def get_dowsing_slot(self, item, options) -> int:
        # Get info for which dowsing slot (if any) a chest should respond to.
        # Dowsing slots:
        # 0: Main quest
        # 1: Rupee
        # 2: Key Piece / Scrapper Quest
        # 3: Crystal
        # 4: Heart
        # 5: Goddess Cube
        # 6: Look around (not usable afaik)
        # 7: Treasure
        # 8: None
        dowsing_setting = options.get("chest-dowsing")
        if dowsing_setting == "Vanilla":
            return 8
        elif dowsing_setting == "All Chests":
            return 0
        else:
            assert dowsing_setting == "Progress Items"
            if item["classification"] in [
                "progression",
                "progression_skip_balancing",
                "trap",
            ]:
                return 0
            return 8


SS_ARCHIPELAGO_SPECIAL_ITEMS = {
    # These items have their normal models if you find another player's
    "Progressive Sword": ["Archipelago Sword", 217],
    "Goddess's Harp": ["Archipelago Harp", 218],
    "Progressive Bow": ["Archipelago Bow", 219],
    "Clawshots": ["Archipelago Clawshots", 220],
    "Spiral Charge": ["Archipelago Spiral Charge", 221],
    "Gust Bellows": ["Archipelago Gust Bellows", 222],
    "Progressive Slingshot": ["Archipelago Slingshot", 223],
    "Progressive Beetle": ["Archipelago Beetle", 224],
    "Progressive Mitts": ["Archipelago Mitts", 225],
    "Water Dragon's Scale": ["Archipelago Scale", 226],
    "Progressive Bug Net": ["Archipelago Bug Net", 227],
    "Bomb Bag": ["Archipelago Bomb Bag", 228],
    "Triforce of Courage": ["Archipelago Triforce", 229],
    "Triforce of Power": ["Archipelago Triforce", 229],
    "Triforce of Wisdom": ["Archipelago Triforce", 229],
    "Whip": ["Archipelago Whip", 230],
    "Fireshield Earrings": ["Archipelago Earrings", 231],
    "Tumbleweed": ["Archipelago Tumbleweed", 232],
    "Emerald Tablet": ["Archipelago Emerald Tablet", 233],
    "Ruby Tablet": ["Archipelago Ruby Tablet", 234],
    "Amber Tablet": ["Archipelago Amber Tablet", 235],
    "Stone of Trials": ["Archipelago Stone of Trials", 236],
    "Scrapper": ["Archipelago Scrapper", 237],
    # Dungeon Items
    "Skyview Map": ["Archipelago Map", 238],
    "Earth Temple Map": ["Archipelago Map", 238],
    "Lanayru Mining Facility Map": ["Archipelago Map", 238],
    "Ancient Cistern Map": ["Archipelago Map", 238],
    "Fire Sanctuary Map": ["Archipelago Map", 238],
    "Sandship Map": ["Archipelago Map", 238],
    "Sky Keep Map": ["Archipelago Map", 238],
    "Skyview Small Key": ["Archipelago Small Key", 239],
    "Lanayru Mining Facility Small Key": ["Archipelago Small Key", 239],
    "Ancient Cistern Small Key": ["Archipelago Small Key", 239],
    "Fire Sanctuary Small Key": ["Archipelago Small Key", 239],
    "Sandship Small Key": ["Archipelago Small Key", 239],
    "Sky Keep Small Key": ["Archipelago Small Key", 239],
    "Lanayru Caves Small Key": ["Archipelago Small Key", 239],
    "Ancient Cistern Boss Key": ["Archipelago Ancient Cistern Boss Key", 240],
    "Fire Sanctuary Boss Key": ["Archipelago Fire Sanctuary Boss Key", 241],
    "Sandship Boss Key": ["Archipelago Sandship Boss Key", 242],
    "Skyview Boss Key": ["Archipelago Skyview Boss Key", 243],
    "Earth Temple Boss Key": ["Archipelago Earth Temple Boss Key", 244],
    "Lanayru Mining Facility Boss Key": [
        "Archipelago Lanayru Mining Facility Boss Key",
        245,
    ],
}

UNTOUCHED_OPTIONS = [
    # If cosmetic, assume untouched
    "dry-run",
    "output-folder",
    "json",
    "noui",
    "apssr",
    "gui-theme",
    "gui-theme-preset",
    "use-custom-theme",
    "font-family",
    "font-size",
    "use-sharp-corners",
    "seed",
    "no-spoiler-log",
    "out-placement-file",
]

FORCED_OPTIONS = {
    "logic-mode": "BiTless",
    "enabled-tricks-bitless": [],
    "enabled-tricks-glitched": [],
    "hint-distribution": "Balanced",
}
