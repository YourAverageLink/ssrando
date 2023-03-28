from pathlib import Path
from typing import Callable, Iterable, Dict, Optional, List
import re
from io import BytesIO
from collections import defaultdict
import shutil

import colourReplace as cr
from paths import RANDO_ROOT_PATH
import os
import json

import nlzss11
from .bzs import ParsedBzs, parseBzs, buildBzs
from .msb import ParsedMsb, parseMSB, buildMSB
from .u8file import U8File
from .utils import write_bytes_create_dirs

from brresTools.brres import BRRES
from brresTools.TEX0 import TEX0
import numpy as np

STAGE_REGEX = re.compile("(.+)_stg_l([0-9]+).arc.LZ")
EVENT_REGEX = re.compile("([0-9])-[A-Za-z]+.arc")
ROOM_REGEX = re.compile(r"/rarc/(?P<stage>.+)_r(?P<roomid>[0-9]+).arc")
OARC_ARC_REGEX = re.compile(r"/oarc/(?P<name>.+\.arc)")
TEXT_ARC_REGEX = re.compile(
    r"(.+(/|\\))*(?P<lang>(en|es|fr))_US(/|\\)(?P<name>.+\.arc)"
)
LANGUAGES = {"EU": "en_GB", "US": "en_US", "JP": "ja_JP"}

LINK_MODEL_DATA_PATH = RANDO_ROOT_PATH / "assets" / "default-link-data"
CUSTOM_MODELS_PATH = RANDO_ROOT_PATH / "models"
OARC_PATH = RANDO_ROOT_PATH / "oarc"

MASK_REGEX = re.compile(r"(.+(/|\\))*(?P<texName>(a|p)l_.+)_(?P<colorGroupName>.+).png")

DEFAULT_COLOUR_METADATA_PATH = LINK_MODEL_DATA_PATH / "metadata.json"


class AllPatcher:
    def __init__(
        self,
        actual_extract_path: Path,
        modified_extract_path: Path,
        oarc_cache_path: Path,
        arc_replacement_path: Path,
        assets_path: Path,
        current_custom_model_pack_name: str,
        copy_unmodified: bool = True,
    ):
        """
        Creates a new instance of the AllPatcher, which patches the game files but with a single callback for each resource type
        actual_extract_path: a path pointing to the root directory of the extracted game, so that it has the subdirectories DATA and UPDATE
        modified_extract_path: a path where to write the patched files to, should be a copy of the actual extract if intended to be repacked into an iso
        copy_unmodified: If unmodified Stage and Event files should be copied, other files are never copied
        """
        self.actual_extract_path = actual_extract_path
        self.modified_extract_path = modified_extract_path
        self.oarc_cache_path = oarc_cache_path
        self.assets_path = assets_path
        self.current_custom_model_pack_name = current_custom_model_pack_name
        self.copy_unmodified = copy_unmodified
        self.arc_replacements = {}
        if arc_replacement_path.is_dir():
            for replace_path in arc_replacement_path.rglob("*.arc"):
                arcname = replace_path.parts[-1]
                self.arc_replacements[arcname] = replace_path
        self.objpackoarcadd = []
        self.objPackCustomModelAdd = None
        self.stage_oarc_add = {}
        self.stage_oarc_delete = {}
        self.bzs_patch = None
        self.event_patch = None
        self.event_text_patch = None

        def dummy_progress_callback(action):
            pass

        self.progress_callback = dummy_progress_callback
        if not (self.actual_extract_path / "DATA").exists():
            raise Exception(
                "actual_extract path should have a DATA subdir, make sure the directory structure is properly set up."
            )

    def add_stage_oarc(self, stage: str, layer: int, oarcs: Iterable[str]):
        self.stage_oarc_add[(stage, layer)] = oarcs

    def delete_stage_oarc(self, stage: str, layer: int, oarcs: Iterable[str]):
        self.stage_oarc_delete[(stage, layer)] = oarcs

    def set_bzs_patch(
        self, patchfunc: Callable[[ParsedBzs, str, Optional[int]], Optional[ParsedBzs]]
    ):
        """
        The function gets called for every bzs (so stages and rooms), it passes the parsed bzs,
        the stage name and the room id or None, if it's a stage and not a room
        if the return value of the function is not None, it will override the game files,
        otherwise nothing will change
        """
        self.bzs_patch = patchfunc

    def set_event_patch(self, patchfunc: Callable[[ParsedMsb, str], ParsedMsb]):
        """
        The function gets called for every event file, which stores the logic of events (msbf)
        it passes the parsed msbf file and the filename (for example `110-DivingGame`)
        if the return value of the function is not None, it will override the game files,
        otherwise nothing will change
        """
        self.event_patch = patchfunc

    def set_event_text_patch(self, patchfunc: Callable[[ParsedMsb, str], ParsedMsb]):
        """
        The function gets called for every event file, which stores the text for textboxes etc. (msbt)
        it passes the parsed msbt file and the filename (for example `110-DivingGame`)
        if the return value of the function is not None, it will override the game files,
        otherwise nothing will change
        """
        self.event_text_patch = patchfunc

    def create_oarc_cache(self, extracts):
        self.oarc_cache_path.mkdir(parents=True, exist_ok=True)
        for extract in extracts:
            if "objectpack" in extract:
                # special case: object pack
                arcs = extract["objectpack"]
                all_not_existing = [
                    objname
                    for objname in arcs
                    if not (self.oarc_cache_path / f"{objname}.arc").exists()
                ]
                if len(all_not_existing) == 0:
                    continue
                data = (
                    self.actual_extract_path
                    / "DATA"
                    / "files"
                    / "Object"
                    / "ObjectPack.arc.LZ"
                ).read_bytes()
                data = nlzss11.decompress(data)
                data = U8File.parse_u8(BytesIO(data))
                for arcname in all_not_existing:
                    arcdata = data.get_file_data(f"oarc/{arcname}.arc")
                    (self.oarc_cache_path / f"{arcname}.arc").write_bytes(arcdata)
            else:
                # check if it already exists first
                objs = extract["oarcs"]
                stage = extract["stage"]
                layer = extract["layer"]
                all_exits = all(
                    (
                        (self.oarc_cache_path / f"{objname}.arc").exists()
                        for objname in objs
                    )
                )
                if all_exits:
                    # print(f'already in cache for {stage}, l{layer}')
                    continue
                data = (
                    self.actual_extract_path
                    / "DATA"
                    / "files"
                    / "Stage"
                    / f"{stage}"
                    / f"{stage}_stg_l{layer}.arc.LZ"
                ).read_bytes()
                data = nlzss11.decompress(data)
                data = U8File.parse_u8(BytesIO(data))

                for objname in objs:
                    # print(f'loading {objname} from {stage}, l{layer}')
                    outdata = data.get_file_data(f"oarc/{objname}.arc")
                    (self.oarc_cache_path / f"{objname}.arc").write_bytes(outdata)

    def patch_arc_replacements(self):
        # handles arc replacement for all other arcs
        for path in self.actual_extract_path.glob("**/*.arc"):

            modified = False
            modified_path = str(path).replace(
                str(self.actual_extract_path), str(self.modified_extract_path)
            )
            replacement = Path()

            # replaces arc with actual arc if deleted
            if not Path(modified_path).exists():
                shutil.copy(path, modified_path)

            # handles stage text arcs as they have duplicate names for each language
            if match := TEXT_ARC_REGEX.match(str(path)):
                if match.group("lang") == "en":
                    if replacement := (
                        self.arc_replacements.get(match.group("name"))
                        or self.arc_replacements.get(
                            match.group("lang") + match.group("name")
                        )
                    ):
                        modified = True
                elif match.group("lang") == "es" or match.group("lang") == "fr":
                    if replacement := self.arc_replacements.get(
                        match.group("lang") + match.group("name")
                    ):
                        modified = True

            # handles motion plus movie cursor and regular cursor arcs separately as they have duplicate names
            elif path.parts[-1] == "cursor.arc":
                if path.parts[-3] == "mpls_movie":
                    if replacement := self.arc_replacements.get(f"mplscursor.arc"):
                        modified = True
                else:
                    if replacement := self.arc_replacements.get("cursor.arc"):
                        modified = True

            # handles all other non-duplicate named arcs
            elif replacement := self.arc_replacements.get(path.parts[-1]):
                modified = True

            if modified:
                shutil.copy(replacement, modified_path)
            else:
                # replaces arc with actual arc if unchanged
                shutil.copy(path, modified_path)

    def patch_custom_model(self):
        self.mask_lookup = {}

        if self.current_custom_model_pack_name == 'Link':
            model_pack_path = LINK_MODEL_DATA_PATH
            linkArcPath = OARC_PATH / "Alink.arc"
        else:
            model_pack_path = CUSTOM_MODELS_PATH / self.current_custom_model_pack_name
            linkArcPath = model_pack_path / "Alink.arc"



        if os.path.isfile(model_pack_path / 'metadata.json'):
            with open(model_pack_path / 'metadata.json') as f:
                self.color_metadata = json.load(f)

        for p in Path(model_pack_path / "TextureMasks" / "Player").iterdir():
            if match := MASK_REGEX.match(str(p)):
                if match.group("texName") not in self.mask_lookup:
                    self.mask_lookup[match.group("texName")] = []
                self.mask_lookup[match.group("texName")].append(match.group("colorGroupName"))
        
        self.hero_color_data = self.color_metadata.get("Hero")

        linkArcBytes = linkArcPath.read_bytes()
        parsedLinkArc = U8File.parse_u8(BytesIO(linkArcBytes))
        brresData = parsedLinkArc.get_file_data("g3d/model.brres")
        parsedBRRES = BRRES.parse_brres(BytesIO(brresData))

        for texName in self.mask_lookup:
            texPath = f'Textures(NW4R)/{texName}'
            imageData: np.array = parsedBRRES.get_file_data(path=texPath)
            maskPaths = []
            colors = []
            process = False
            print(self.mask_lookup[texName])
            for colorGroup in self.mask_lookup[texName]:
                if self.hero_color_data[colorGroup] == "Default": continue
                maskPath = str(model_pack_path / "TextureMasks" / "Player" / (str(texName) + "_" + str(colorGroup) + ".png"))
                maskPaths.append(maskPath)
                colors.append(self.hero_color_data[colorGroup])
                process = True

            if process:
                modifiedTexture: np.array = cr.process_texture(texture=imageData, maskPaths=maskPaths, colors=colors)
                parsedBRRES.set_file_data(path=texPath, data=modifiedTexture)
        
        parsedLinkArc.set_file_data("g3d/model.brres", parsedBRRES.to_buffer().read())
        self.objPackCustomModelAdd = parsedLinkArc.to_buffer()
        
        return

    def do_patch(self):
        self.modified_extract_path.mkdir(parents=True, exist_ok=True)

        self.patch_arc_replacements()
        self.patch_custom_model()

        # stages
        for stagepath in (self.actual_extract_path / "DATA" / "files" / "Stage").glob(
            "*/*_stg_l*.arc.LZ"
        ):
            match = STAGE_REGEX.match(stagepath.parts[-1])
            stage = match[1]
            layer = int(match[2])
            self.progress_callback(f"patching {stage} l{layer}")
            modified_stagepath = (
                self.modified_extract_path
                / "DATA"
                / "files"
                / "Stage"
                / f"{stage}"
                / f"{stage}_stg_l{layer}.arc.LZ"
            )
            modified = False
            should_be_copied = False
            # remove some arcs if necessary
            remove_arcs = set(self.stage_oarc_delete.get((stage, layer), []))
            # add additional arcs if needed
            additional_arcs = set(self.stage_oarc_add.get((stage, layer), []))
            if remove_arcs or additional_arcs or layer == 0 or self.arc_replacements:
                # only decompress and extract files, if needed
                stagedata = nlzss11.decompress(stagepath.read_bytes())
                stageu8 = U8File.parse_u8(BytesIO(stagedata))
                # remove arcs that are already added on layer 0
                if layer != 0:
                    additional_arcs = additional_arcs - (
                        set(self.stage_oarc_add.get((stage, 0), [])) - set(("dummy",))
                    )
                remove_arcs = remove_arcs - additional_arcs
                for arc in remove_arcs:
                    stageu8.delete_file(f"oarc/{arc}.arc")
                    modified = True
                patched_arcs = set()
                for arc in additional_arcs:
                    if arc == "dummy":
                        # dummy arcs inserted to make sure this layer gets patched
                        should_be_copied = True
                        continue
                    arcname = f"{arc}.arc"
                    oarc_path = self.arc_replacements.get(arcname) or (
                        self.oarc_cache_path / arcname
                    )
                    stageu8.add_file_data(f"oarc/{arcname}", oarc_path.read_bytes())
                    patched_arcs.add(arcname)
                    modified = True
                if self.arc_replacements:
                    for path in stageu8.get_all_paths():
                        if match := OARC_ARC_REGEX.match(path):
                            arc = match.group("name")
                            if arc in patched_arcs:
                                continue
                            if replacement := self.arc_replacements.get(arc):
                                stageu8.set_file_data(path, replacement.read_bytes())
                                patched_arcs.add(arc)
                                modified = True
                if layer == 0:
                    stagebzs = parseBzs(stageu8.get_file_data("dat/stage.bzs"))
                    # patch stage
                    if self.bzs_patch:
                        newstagebzs = self.bzs_patch(stagebzs, stage, None)
                        if newstagebzs is not None:
                            stageu8.set_file_data(
                                "dat/stage.bzs", buildBzs(newstagebzs)
                            )
                            modified = True
                        # patch rooms
                        room_path_matches = (
                            ROOM_REGEX.match(x) for x in stageu8.get_all_paths()
                        )
                        room_path_matches = (
                            x for x in room_path_matches if not x is None
                        )
                        for room_path_match in room_path_matches:
                            roomid = int(room_path_match.group("roomid"))
                            roomdata = stageu8.get_file_data(room_path_match.group(0))
                            roomarc = U8File.parse_u8(BytesIO(roomdata))
                            roombzs = parseBzs(roomarc.get_file_data("dat/room.bzs"))
                            roombzs = self.bzs_patch(roombzs, stage, roomid)
                            if roombzs is not None:
                                roomarc.set_file_data("dat/room.bzs", buildBzs(roombzs))
                                stageu8.set_file_data(
                                    room_path_match.group(0), roomarc.to_buffer()
                                )
                                modified = True
                    # check if zev.dat can be patched
                    zev_path = self.assets_path / f"{stage}zev.dat"
                    if zev_path.is_file():
                        zev_data = zev_path.read_bytes()
                        stageu8.set_file_data("dat/zev.dat", zev_data)

            # repack u8 and compress it if modified
            if modified:
                stagedata = stageu8.to_buffer()
                write_bytes_create_dirs(modified_stagepath, nlzss11.compress(stagedata))
                # print(f'patched {stage} l{layer}')
            elif self.copy_unmodified or layer == 0 or should_be_copied:
                # always copy layer 0 because it contains the stage definitions
                shutil.copy(stagepath, modified_stagepath)
                # print(f"copied {stage} l{layer}")

        # events and text
        modified_eventrootpath = None

        # check target language
        for path, lang in LANGUAGES.items():
            if (self.modified_extract_path / "DATA" / "files" / path).exists():
                modified_eventrootpath = (
                    self.modified_extract_path
                    / "DATA"
                    / "files"
                    / path
                    / "Object"
                    / lang
                )

        if modified_eventrootpath == None:
            raise Exception("Event files not found.")
        for eventpath in modified_eventrootpath.glob("*.arc"):
            modified = False
            filename = eventpath.parts[-1]
            self.progress_callback(f"patching {filename}")
            modified_eventpath = modified_eventrootpath / filename
            eventarc = U8File.parse_u8(BytesIO(eventpath.read_bytes()))
            # make sure to handle text files first for labels
            for eventfilepath in sorted(
                eventarc.get_all_paths(), key=lambda x: x[-1], reverse=True
            ):
                eventfilename = eventfilepath.split("/")[-1]
                if eventfilename.endswith(".msbf"):
                    parsedMsb = parseMSB(eventarc.get_file_data(eventfilepath))
                    if self.event_patch:
                        patchedMsb = self.event_patch(parsedMsb, eventfilename[:-5])
                        if patchedMsb:
                            eventarc.set_file_data(eventfilepath, buildMSB(patchedMsb))
                            modified = True
                elif eventfilename.endswith(".msbt"):
                    parsedMsb = parseMSB(eventarc.get_file_data(eventfilepath))
                    if self.event_text_patch:
                        patchedMsb = self.event_text_patch(
                            parsedMsb, eventfilename[:-5]
                        )
                        if patchedMsb:
                            eventarc.set_file_data(eventfilepath, buildMSB(patchedMsb))
                            modified = True
            if modified:
                write_bytes_create_dirs(modified_eventpath, eventarc.to_buffer())
                # print(f'patched {filename}')

        self.progress_callback("patching ObjectPack...")
        # patch object pack
        objpack_data = nlzss11.decompress(
            (
                self.actual_extract_path
                / "DATA"
                / "files"
                / "Object"
                / "ObjectPack.arc.LZ"
            ).read_bytes()
        )
        object_arc = U8File.parse_u8(BytesIO(objpack_data))
        objpack_modified = False
        patched_arcs = set()
        for oarc in self.objpackoarcadd:
            arcname = f"{oarc}.arc"
            oarc_path = self.arc_replacements.get(arcname) or (
                self.oarc_cache_path / arcname
            )
            object_arc.add_file_data(f"oarc/{arcname}", oarc_path.read_bytes())
            patched_arcs.add(arcname)
            objpack_modified = True

        if self.objPackCustomModelAdd:
            object_arc.set_file_data("oarc/Alink.arc", self.objPackCustomModelAdd)
            objpack_modified = True

        if self.arc_replacements:
            for path in object_arc.get_all_paths():
                if match := OARC_ARC_REGEX.match(path):
                    arc = match.group("name")
                    if arc in patched_arcs:
                        continue
                    if replacement := self.arc_replacements.get(arc):
                        object_arc.set_file_data(path, replacement.read_bytes())
                        patched_arcs.add(arc)
                        objpack_modified = True

        if objpack_modified:
            objpack_data = object_arc.to_buffer()
            write_bytes_create_dirs(
                self.modified_extract_path
                / "DATA"
                / "files"
                / "Object"
                / "ObjectPack.arc.LZ",
                nlzss11.compress(objpack_data),
            )
