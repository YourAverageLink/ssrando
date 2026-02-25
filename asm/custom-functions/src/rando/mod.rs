// Custom Rando Functions go here

// IMPORTANT: when adding functions here that need to get called from the game,
// add `#[no_mangle]` and add a .global *symbolname* to custom_funcs.asm

pub mod networking;

use core::{
    ffi::{c_char, c_int, c_uint, c_ushort, c_void},
    fmt::Write,
    ptr, slice,
    str::from_utf8,
};

use cstr::cstr;

use wchar::wch;

use crate::{
    game::{
        actor, arc,
        bird::AcOBird,
        events::ActorEventFlowMgr,
        file_manager::{self, get_current_health},
        flag_managers::*,
        item::{self, Item},
        message::{text_manager_set_num_args, text_manager_set_string_arg, FlowElement},
        minigame::SpecialMinigameState,
        player,
        reloader::{self, Reloader},
    },
    rando::item_arc_loader::{check_arcs_loaded, load_arcs_for_item, unload_arcs_for_item},
    system::{button::*, math::*},
    utils::console::Console,
};

mod custom_actor;
mod item_arc_loader;

#[link_section = "data"]
static mut IS_FILE_START: bool = false;

#[link_section = "data"]
#[no_mangle]
static mut FORCE_MOGMA_CAVE_DIVE: bool = false;

#[link_section = "data"]
#[no_mangle]
static mut archipelago_text_buffer: [u8; 0x200] = [0; 0x200];

#[no_mangle]
extern "C" fn process_startflags() {
    unsafe { (*file_manager::get_ptr()).anticommit_flag = 1 };
    #[repr(C)]
    struct StartflagInfo {
        storyflags:    [u16; 0x80],
        itemflags:     [u16; 0x40],
        dungeonflags:  [u8; 8],
        full_hearts:   u8,
        pouch_options: u8,
        // this is just the max amount of possible flags, not the actual amount
        sceneflags:    [u8; 118],
    }
    let startflag_info = unsafe { &*(0x804EE1B8 as *const StartflagInfo) };
    unsafe {
        // storyflags
        *StoryflagManager::get_static() = startflag_info.storyflags;
        // itemflags
        *ItemflagManager::get_static() = startflag_info.itemflags;
    }
    // sceneflags
    let mut scene_idx = 0;
    for flag in startflag_info.sceneflags.iter() {
        if *flag == 0xFF {
            break;
        } else if *flag >= 0x80 {
            scene_idx = flag & 0x7F;
        } else {
            SceneflagManager::set_global(scene_idx.into(), (*flag).into());
        }
    }
    // dungeonflags
    // includes keys, maps, boss keys
    // each entry is a byte, the bits work as follows:
    // B0KK KKM0, B(K), M(AP), K(EY)
    // doing it this weird way to save instructions
    const DUNGEONFLAG_INDICES: [u8; 8] = [
        11, // SV
        14, // ET
        17, // LMF
        12, // AC
        18, // SS
        15, // FS
        20, // SK
        9,  // Lanayru Caves
    ];
    for (&dungeon_startflag, &flagindex) in startflag_info
        .dungeonflags
        .iter()
        .zip(DUNGEONFLAG_INDICES.iter())
    {
        let first_short = dungeon_startflag & 0x82;
        let small_keys = (dungeon_startflag >> 2) & 0x0F;
        unsafe {
            if (*DungeonflagManager::get_ptr()).flagindex == flagindex as u16 {
                let flags = &mut *DungeonflagManager::get_local();
                flags[0] = first_short.into();
                flags[1] = small_keys.into();
            }
            let flags = &mut *DungeonflagManager::get_global(flagindex as u16);
            flags[0] = first_short.into();
            flags[1] = small_keys.into();
        }
    }

    // Starting heart capacity.
    let health_capatity = startflag_info.full_hearts * 4;
    unsafe { (*file_manager::get_ptr()).FA.health_capacity = health_capatity.into() };
    unsafe { (*file_manager::get_ptr()).FA.current_health = health_capatity.into() };

    let mut pouch_slot_iter = unsafe { (*file_manager::get_ptr()).FA.pouch_items.iter_mut() };

    // Starting Hylian Shield.
    // 4th bit.
    if startflag_info.pouch_options >> 3 & 0x1 == 1 {
        // ID for Hylian Shield + durability
        *pouch_slot_iter.next().unwrap() = 125 | 0x30 << 0x10;
    }

    // Starting Bottles.
    // Last bit.
    let bottle_count = startflag_info.pouch_options & 0x7;
    if bottle_count > 0 {
        ItemflagManager::set_to_value(153, 1);
    }
    for slot in pouch_slot_iter.take(bottle_count.into()) {
        *slot = 153; // ID for bottles
    }

    // Should set respawn info after new file start
    unsafe { IS_FILE_START = true };

    // Commit global flag managers.
    ItemflagManager::do_commit();
    StoryflagManager::do_commit();

    unsafe { (*file_manager::get_ptr()).anticommit_flag = 0 };
}

#[no_mangle]
extern "C" fn handle_bk_map_dungeonflag(item: c_ushort) {
    const BK_TO_FLAGINDEX: [u8; 7] = [
        // starts at 25
        12, // AC
        15, // FS
        18, // SSH
        13, // unused, shouldn't happen
        11, // SV
        14, // ET
        17, // LMF
    ];
    const MAP_TO_FLAGINDEX: [u8; 7] = [
        // starts at 207
        11, // SV
        14, // ET
        17, // LMF
        12, // AC
        15, // FS
        18, // SSH
        20, // SK
    ];

    let (flagindex, dungeonflag_mask) =
        if let Some(flagindex) = BK_TO_FLAGINDEX.get((item as usize).wrapping_sub(25)) {
            (*flagindex, 0x80)
        } else if let Some(flagindex) = MAP_TO_FLAGINDEX.get((item as usize).wrapping_sub(207)) {
            (*flagindex, 0x02)
        } else {
            return;
        };
    unsafe {
        if (*DungeonflagManager::get_ptr()).flagindex == flagindex as u16 {
            (*DungeonflagManager::get_local())[0] |= dungeonflag_mask;
        }
        (*DungeonflagManager::get_global(flagindex as u16))[0] |= dungeonflag_mask;
    }
}

const OBTAINED_TEXT: &[u16; 9] = wch!(u16, "Obtained\0");
const UNOBTAINED_TEXT: &[u16; 11] = wch!(u16, "Unobtained\0");
const COMPLETE_TEXT: &[u16; 21] = wch!(
    u16,
    "\x0E\x00\x03\x02\x08 Complete \x0E\x00\x03\x02\u{FFFF}\0"
);
const INCOMPLETE_TEXT: &[u16; 23] = wch!(
    u16,
    "\x0E\x00\x03\x02\x09 Incomplete \x0E\x00\x03\x02\u{FFFF}\0"
);
const UNREQUIRED_TEXT: &[u16; 23] = wch!(
    u16,
    "\x0E\x00\x03\x02\x0C Unrequired \x0E\x00\x03\x02\u{FFFF}\0"
);

#[no_mangle]
extern "C" fn rando_text_command_handler(
    _event_flow_mgr: *mut ActorEventFlowMgr,
    p_flow_element: *const FlowElement,
) {
    let flow_element = unsafe { &*p_flow_element };
    match flow_element.param3 {
        71 => {
            let dungeon_index = flow_element.param1;
            let completion_storyflag = flow_element.param2;
            let key_count = if dungeon_index == 14
            // ET
            {
                item::get_key_piece_count()
            } else {
                DungeonflagManager::get_global_key_count(dungeon_index)
            };
            text_manager_set_num_args(&[key_count as u32]);
            let map_and_bk = unsafe { (*DungeonflagManager::get_global(dungeon_index))[0] };
            let bk_text = match map_and_bk & 0x82 {
                0x80 => OBTAINED_TEXT.as_ptr(),
                0x82 => OBTAINED_TEXT.as_ptr(),
                _ => UNOBTAINED_TEXT.as_ptr(),
            };
            let map_text = match map_and_bk & 0x82 {
                0x02 => OBTAINED_TEXT.as_ptr(),
                0x82 => OBTAINED_TEXT.as_ptr(),
                _ => UNOBTAINED_TEXT.as_ptr(),
            };
            text_manager_set_string_arg(bk_text as *const c_void, 0);
            text_manager_set_string_arg(map_text as *const c_void, 1);

            let completed_text = if completion_storyflag == 0xFFFF {
                UNREQUIRED_TEXT.as_ptr()
            } else if StoryflagManager::check(completion_storyflag) {
                COMPLETE_TEXT.as_ptr()
            } else {
                INCOMPLETE_TEXT.as_ptr()
            };
            text_manager_set_string_arg(completed_text as *const c_void, 2);
        },
        72 => {
            let caves_key = DungeonflagManager::get_global_key_count(9);
            let caves_key_text = if caves_key == 1 {
                OBTAINED_TEXT.as_ptr()
            } else {
                UNOBTAINED_TEXT.as_ptr()
            };
            text_manager_set_string_arg(caves_key_text as *const c_void, 0);

            let spiral_charge_obtained = 364; // story flag for spiral charge
            let spiral_charge_text = if StoryflagManager::check(spiral_charge_obtained) {
                OBTAINED_TEXT.as_ptr()
            } else {
                UNOBTAINED_TEXT.as_ptr()
            };
            text_manager_set_string_arg(spiral_charge_text as *const c_void, 1);

            let life_tree_fruit_obtained = 198; // item flag for life tree fruit
            let life_tree_fruit_text = if ItemflagManager::check(life_tree_fruit_obtained) {
                OBTAINED_TEXT.as_ptr()
            } else {
                UNOBTAINED_TEXT.as_ptr()
            };
            text_manager_set_string_arg(life_tree_fruit_text as *const c_void, 2);

            // Tadtones obtained.
            text_manager_set_num_args(&[StoryflagManager::get_value(953) as u32]);
        },
        73 => send_to_start(),
        74 => {
            // Increment storyflag counter
            let flag = flow_element.param1;
            let increment = flow_element.param2;

            StoryflagManager::set_to_value(flag, StoryflagManager::get_value(flag) + increment);
        },
        75 => {
            // Have collected all tadtone groups?
            let tadtone_groups_left: u32 = 17_u16
                .saturating_sub(StoryflagManager::get_value(953))
                .into();
            text_manager_set_num_args(&[tadtone_groups_left]);
            unsafe {
                (*_event_flow_mgr).result_from_previous_check = tadtone_groups_left;
            }
        },
        76 => {
            // set numeric arg0 to number of keys of area in param1
            // we need to add one, the key counter is only incremented *after* the textbox
            let keys = DungeonflagManager::get_global_key_count(flow_element.param1) + 1;
            text_manager_set_num_args(&[keys.into()]);
        },
        _ => (),
    }
}

#[no_mangle]
extern "C" fn textbox_a_pressed_or_b_held() -> bool {
    if is_pressed(A) || is_down(B) {
        return true;
    }
    return false;
}

#[no_mangle]
extern "C" fn set_goddess_sword_pulled_scene_flag() {
    // Set story flag 951 (Raised Goddess Sword in Goddess Statue).
    StoryflagManager::storyflag_set_to_1(951);
}

fn simple_rng(rng: &mut u32) -> u32 {
    *rng = rng.wrapping_mul(1664525).wrapping_add(1013904223);
    *rng
}

#[no_mangle]
extern "C" fn randomize_boss_key_start_pos(ptr: *mut u16, mut seed: u32) {
    // 6 dungeons, each having a Vec3s which is just 3 u16 (or rather i16)
    let angles = unsafe { slice::from_raw_parts_mut(ptr, 3 * 6) };
    for angle in angles.iter_mut() {
        *angle = simple_rng(&mut seed) as u16;
    }
}

#[no_mangle]
extern "C" fn get_item_arc_name(
    oarc_mgr: *const c_void,
    vanilla_item_str: *const c_char,
    item_id: u32,
) -> *const c_void {
    let oarc_name;

    match item_id {
        214 => oarc_name = cstr!("Onp").as_ptr(),         // tadtone
        215 => oarc_name = cstr!("DesertRobot").as_ptr(), // scrapper
        216 => oarc_name = cstr!("GetKobunALetter").as_ptr(), // ap item
        217 => oarc_name = cstr!("GetSwordA").as_ptr(),   // ap sword
        218 => oarc_name = cstr!("GetHarp").as_ptr(),     // ap harp
        219 => oarc_name = cstr!("GetBowA").as_ptr(),     // ap bow
        220 => oarc_name = cstr!("GetHookShot").as_ptr(), // ap clawshots
        221 => oarc_name = cstr!("GetBirdStatue").as_ptr(), // ap spiral charge
        222 => oarc_name = cstr!("GetVacuum").as_ptr(),   // ap bellows
        223 => oarc_name = cstr!("GetPachinkoA").as_ptr(), // ap slingshot
        224 => oarc_name = cstr!("GetBeetleA").as_ptr(),  // ap beetle
        225 => oarc_name = cstr!("GetMoleGloveA").as_ptr(), // ap mitts
        226 => oarc_name = cstr!("GetUroko").as_ptr(),    // ap scale
        227 => oarc_name = cstr!("GetNetA").as_ptr(),     // ap net
        228 => oarc_name = cstr!("GetBombBag").as_ptr(),  // ap bomb bag
        229 => oarc_name = cstr!("GetTriForceSingle").as_ptr(), // ap triforce
        230 => oarc_name = cstr!("GetWhip").as_ptr(),     // ap whip
        231 => oarc_name = cstr!("GetEarring").as_ptr(),  // ap earrings
        232 => oarc_name = cstr!("GetSozaiC").as_ptr(),   // ap tumbleweed
        233 => oarc_name = cstr!("GetSekibanMapA").as_ptr(), // ap emerald tablet
        234 => oarc_name = cstr!("GetSekibanMapB").as_ptr(), // ap ruby tablet
        235 => oarc_name = cstr!("GetSekibanMapC").as_ptr(), // ap amber tablet
        236 => oarc_name = cstr!("GetSirenKey").as_ptr(), // ap stone of trials
        237 => oarc_name = cstr!("DesertRobot").as_ptr(), // ap scrapper
        238 => oarc_name = cstr!("GetMap").as_ptr(),      // ap map
        239 => oarc_name = cstr!("GetKeySmall").as_ptr(), // ap small key
        240 => oarc_name = cstr!("GetKeyBoss2A").as_ptr(), // ap ac boss key
        241 => oarc_name = cstr!("GetKeyBoss2B").as_ptr(), // ap fs boss key
        242 => oarc_name = cstr!("GetKeyBoss2C").as_ptr(), // ap ssh boss key
        243 => oarc_name = cstr!("GetKeyBossA").as_ptr(), // ap sv boss key
        244 => oarc_name = cstr!("GetKeyBossB").as_ptr(), // ap et boss key
        245 => oarc_name = cstr!("GetKeyBossC").as_ptr(), // ap lmf boss key
        _ => oarc_name = vanilla_item_str,
    }

    return arc::get_model_data(oarc_mgr, oarc_name);
}

#[no_mangle]
extern "C" fn get_item_model_name_ptr(item_id: u32) -> *const c_char {
    match item_id {
        214 => return cstr!("OnpB").as_ptr(),              // tadtone
        215 => return cstr!("DesertRobot").as_ptr(),       // scrapper
        216 => return cstr!("GetKobunALetter").as_ptr(),   // ap item
        217 => return cstr!("GetSwordA").as_ptr(),         // ap sword
        218 => return cstr!("GetHarp").as_ptr(),           // ap harp
        219 => return cstr!("GetBowA").as_ptr(),           // ap bow
        220 => return cstr!("GetHookShot").as_ptr(),       // ap clawshots
        221 => return cstr!("GetBirdStatue").as_ptr(),     // ap spiral charge
        222 => return cstr!("GetVacuum").as_ptr(),         // ap bellows
        223 => return cstr!("GetPachinkoA").as_ptr(),      // ap slingshot
        224 => return cstr!("GetBeetleA").as_ptr(),        // ap beetle
        225 => return cstr!("GetMoleGloveA").as_ptr(),     // ap mitts
        226 => return cstr!("GetUroko").as_ptr(),          // ap scale
        227 => return cstr!("GetNetA").as_ptr(),           // ap net
        228 => return cstr!("GetBombBag").as_ptr(),        // ap bomb bag
        229 => return cstr!("GetTriForceSingle").as_ptr(), // ap triforce
        230 => return cstr!("GetWhip").as_ptr(),           // ap whip
        231 => return cstr!("GetEarring").as_ptr(),        // ap earrings
        232 => return cstr!("GetSozaiC").as_ptr(),         // ap tumbleweed
        233 => return cstr!("SekibanMapA").as_ptr(),       // ap emerald tablet
        234 => return cstr!("SekibanMapB").as_ptr(),       // ap ruby tablet
        235 => return cstr!("SekibanMapC").as_ptr(),       // ap amber tablet
        236 => return cstr!("GetSirenKey").as_ptr(),       // ap stone of trials
        237 => return cstr!("DesertRobot").as_ptr(),       // ap scrapper
        238 => return cstr!("GetMap").as_ptr(),            // ap map
        239 => return cstr!("GetKeySmallNormal").as_ptr(), // ap small key
        240 => return cstr!("GetKeyBoss2A").as_ptr(),      // ap ac boss key
        241 => return cstr!("GetKeyBoss2B").as_ptr(),      // ap fs boss key
        242 => return cstr!("GetKeyBoss2C").as_ptr(),      // ap ssh boss key
        243 => return cstr!("GetKeyBossA").as_ptr(),       // ap sv boss key
        244 => return cstr!("GetKeyBossB").as_ptr(),       // ap et boss key
        245 => return cstr!("GetKeyBossC").as_ptr(),       // ap lmf boss key
        _ => return core::ptr::null(),
    }
}

#[no_mangle]
extern "C" fn enforce_loftwing_speed_cap(loftwing_ptr: *mut AcOBird) {
    let loftwing = unsafe { &mut *loftwing_ptr };
    let mut is_in_levias_fight = false;
    if &reloader::get_spawn_slave().name[..4] == b"F023"
        && StoryflagManager::check(368 /* Pumpkin soup delivered */)
        && !StoryflagManager::check(200 /* Levias explains SotH quest */)
    {
        let levias_ptr = actor::find_actor_by_type(184 /* NusiB */, ptr::null());
        if !levias_ptr.is_null() {
            if player::check_distance_from(levias_ptr, 20_000f32) {
                is_in_levias_fight = true;
            }
        }
    }
    let in_spiral_charge_training = SpecialMinigameState::SpiralChargeTutorial.is_current();
    let cap = if is_in_levias_fight || in_spiral_charge_training || is_down(B) {
        80f32
    } else {
        350f32
    };
    if loftwing.speed > cap {
        loftwing.speed = cap;
    }
}

// The same as give_item only you can control the sceneflag of the item given.
#[no_mangle]
extern "C" fn give_item_with_sceneflag(
    item_id: u16,
    bottle_pouch_slot: u32,
    number: u32,
    sceneflag: u32,
) -> *mut Item {
    item::set_bottle_pouch_slot(bottle_pouch_slot);
    item::set_number_of_items(number);
    // Same as the vanilla setupItemParams function only with extra control over
    // the sceneflag
    let item_params = item::setup_item_params(item_id, 5, 0, sceneflag, 1, 0xFF);

    let item = item::spawn_item(u32::MAX, item_params, 0, 0, 0, u32::MAX, 1);
    item::set_bottle_pouch_slot(u32::MAX);
    item::set_number_of_items(0);
    return item;
}

#[repr(C)]
struct StartInfo {
    stage:        [u8; 8],
    room:         u8,
    layer:        u8,
    entrance:     u8,
    forced_night: u8,
}

#[no_mangle]
extern "C" fn get_start_info() -> *const StartInfo {
    // this is where the start entrance info is patched
    return unsafe { &*(0x802DA0E0 as *const StartInfo) };
}

#[no_mangle]
extern "C" fn send_to_start() {
    let start_info = unsafe { get_start_info().as_ref().unwrap() };

    // manage storyflag that indicates day/night
    StoryflagManager::set_to_value(737, start_info.forced_night.into());

    // we can't use the normal triggerEntrance function, because that doesn't work
    // properly when going from title screen to normal gameplay while keeping
    // the stage
    reloader::trigger_entrance(
        start_info.stage.as_ptr(),
        start_info.room,
        start_info.layer,
        start_info.entrance,
        start_info.forced_night,
        0,
        0,
        0xF,
        0xFF,
    );
    reloader::set_reload_trigger(5);
}

#[no_mangle]
// args only used by replaced function call
extern "C" fn do_er_fixes(room_mgr: *mut c_void, room_number: u32) {
    unsafe {
        if (*reloader::get_ptr()).initial_speed > 30f32 {
            (*reloader::get_ptr()).initial_speed = 30f32;
        }
    }
    let spawn = reloader::get_spawn_slave();
    if spawn.name.starts_with(b"F000") && spawn.entrance == 53 && !StoryflagManager::check(22) {
        // Skyloft from Sky Keep
        spawn.entrance = 52;
    } else if spawn.name.starts_with(b"F300\0")
        && spawn.entrance == 5
        && !StoryflagManager::check(8)
    {
        // Lanayru Desert from LMF - only if LMF isn't raised (storyflag 8)
        spawn.entrance = 19;
    } else if (spawn.name.starts_with(b"F300\0") && spawn.entrance == 2)
        || (spawn.name.starts_with(b"F300_1") && spawn.entrance == 1)
    {
        // desert from mines and mines from desert
        // there are 2 timeshift stones that are fine
        // 7 is sceneflagindex for desert
        if !(SceneflagManager::check_global(7, 113) || SceneflagManager::check_global(7, 114)) {
            for flag in (115..=124).chain([108, 111]) {
                SceneflagManager::unset_global(7, flag);
            }
            // last timeshift stone in mines
            SceneflagManager::set_global(7, 113);
        }
    }

    if unsafe { FORCE_MOGMA_CAVE_DIVE } && spawn.name.starts_with(b"F210") && spawn.entrance == 0 {
        unsafe {
            (*reloader::get_ptr()).spawn_state = 0x13; // diving
        }
    }

    // replaced function call
    extern "C" {
        fn RoomManager__getRoomByIndex(room_mgr: *mut c_void, room_number: u32);
    }
    unsafe {
        RoomManager__getRoomByIndex(room_mgr, room_number);
    }
}

#[no_mangle]
extern "C" fn allow_set_respawn_info() -> *mut Reloader {
    unsafe {
        if IS_FILE_START {
            (*reloader::get_ptr()).prevent_save_respawn_info = false;
            IS_FILE_START = false;
        }

        return reloader::get_ptr();
    }
}

#[no_mangle]
extern "C" fn get_glow_color(item_id: u32) -> u32 {
    let stage = &reloader::get_spawn_slave().name[..4];
    // only proceed if in a silent realm
    if stage[0] == b'S' {
        // exclude stamina fruit, light fruit, and dusk relics
        if (item_id != 42) && (item_id != 47) && (item_id != 168) {
            if (item_id > 42) && (item_id < 47) {
                // item is a tear; keep the correct id
                // skyloft is subtype 3, faron 0, eldin 1, lanayru 2
                return ((stage[1] as u32) + 3) & 3;
            }
            // offset the color by 2 so items look distinct from tears
            return ((stage[1] as u32) + 1) & 3;
        }
    }
    4
}

#[link_section = "data"]
#[no_mangle]
static mut ITEM_ID: u16 = 0;

#[no_mangle]
extern "C" fn game_update_hook() -> u32 {
    1
}

#[link_section = "data"]
#[no_mangle]
static mut HERO_MODE_OPTIONS: u8 = 0;

#[no_mangle]
pub fn has_upgraded_skyward_strike() -> c_int {
    if unsafe { HERO_MODE_OPTIONS } & 0b001 != 0 {
        1
    } else {
        0
    }
}

#[no_mangle]
pub fn has_fast_air_meter_drain() -> c_int {
    if unsafe { HERO_MODE_OPTIONS } & 0b010 != 0 {
        1
    } else {
        0
    }
}

#[no_mangle]
pub fn has_heart_drops_enabled() -> c_int {
    if unsafe { HERO_MODE_OPTIONS } & 0b100 != 0 {
        1
    } else {
        0
    }
}

#[no_mangle]
pub fn add_ammo_drops(
    param1: *mut c_void,
    param2_s0x18: u8,
    roomid: u32,
    pos: *mut Vec3f,
    _subtype: u32,
    _rot: *mut c_void,
) -> bool {
    // 0xFE is the custom id being used to drop arrows, bombs, and seeds.
    // Should set the eq flag for comparison after this addtion.
    if param2_s0x18 == 0xFE {
        if ItemflagManager::check(Itemflag::BOW as u16) {
            unsafe {
                item::spawnDrop(
                    Itemflag::BUNDLE_OF_ARROWS,
                    roomid,
                    pos,
                    &mut Vec3s::default() as *mut Vec3s,
                );
            }
        }

        if ItemflagManager::check(Itemflag::BOMB_BAG as u16) {
            unsafe {
                item::spawnDrop(
                    Itemflag::TEN_BOMBS,
                    roomid,
                    pos,
                    &mut Vec3s::default() as *mut Vec3s,
                );
            }
        }

        if ItemflagManager::check(Itemflag::SLINGSHOT as u16) {
            unsafe {
                item::spawnDrop(
                    Itemflag::FIVE_DEKU_SEEDS,
                    roomid,
                    pos,
                    &mut Vec3s::default() as *mut Vec3s,
                );
            }
        }
        return false;
    } else {
        extern "C" {
            fn processSpecialItemDropIndex(param1: *mut c_void, param2_s0x18: u8) -> bool;
        }
        unsafe {
            return processSpecialItemDropIndex(param1, param2_s0x18);
        }
    }
}

#[no_mangle]
pub fn drop_nothing(param1: *mut c_void, param2_s0x18: u8) -> bool {
    // if should drop seeds, arrows, or bombs
    if param2_s0x18 == 0xB || param2_s0x18 == 0xC || param2_s0x18 == 0xD {
        return false;
    } else {
        extern "C" {
            fn processSpecialItemDropIndex(param1: *mut c_void, param2_s0x18: u8) -> bool;
        }
        unsafe {
            return processSpecialItemDropIndex(param1, param2_s0x18);
        }
    }
}

#[no_mangle]
extern "C" fn get_tablet_keyframe_count() -> c_int {
    // The tablet frames effectively start with a Gray Code, the continuation of
    // which looks like this:
    //
    // Count     Emerald   Ruby      Amber     As Index
    // 0         0         0         0         0
    // 1         1         0         0         1
    // 2         1         1         0         3
    // 3         1         1         1         7
    // 4         1         0         1         5
    // 5         0         0         1         4
    // 6         0         1         1         6
    // 7         0         1         0         2

    const TABLET_BITMAP_TO_KEYFRAME: [u8; 8] = [0, 1, 7, 2, 5, 4, 6, 3];
    const TABLET_IDS: [u16; 3] = [0xB1, 0xB2, 0xB3];

    let item_bitmap = ItemflagManager::check(TABLET_IDS[0]) as usize
        | ((ItemflagManager::check(TABLET_IDS[1]) as usize) << 1)
        | ((ItemflagManager::check(TABLET_IDS[2]) as usize) << 2);

    TABLET_BITMAP_TO_KEYFRAME[item_bitmap & 0x7] as i32
}

#[no_mangle]
pub fn print_archipelago_text() -> u32 {
    let text_cstr = unsafe { archipelago_text_buffer };
    let mut last_char = 0;
    if text_cstr[0] != 0 {
        let mut top_height = 438f32;
        for char in text_cstr.iter() {
            // We want to move the text box up for each newline so it's bottom-justified
            // Ignore if last character was 0x02, as that means it's part of a tag
            // processor control sequence
            if *char == b'\n' && last_char != 0x02 {
                top_height -= 14f32;
            }
            last_char = *char;
        }
        let text = from_utf8(&text_cstr).unwrap();
        let mut console = Console::with_pos(0f32, top_height);
        console.set_bg_color(0x00000055);
        console.set_font_color(0xFFFFFFFF);
        console.set_font_size(0.4f32);
        let _ = console.write_str(text);
        console.draw(false);
    }

    // Return 1 to tell the game to continue running
    1
}

// static mut SHARED_AP_ITEM: Option<*mut c_void> = None;

fn can_remove_textbox(item_id: u16) -> bool {
    match item_id {
        2..=4 // Rupees
        | 6 // Heart
        | 32..=34 // more rupees
        | 40 // 5 bombs
        | 41 // 10 bombs
        | 60 // 10 deku seeds
        | 63 // semi rare treasure
        | 64 // rare treasure
        | 94 // heart piece
        // a bunch of treasures
        | 165
        | 171
        | 173
        | 175
        | 176 => true,
        _ => false,
    }
}

// #[no_mangle]
// extern "C" fn spawn_ap_item(item_id: u16) -> *mut c_void {
// extern "C" {
// static mut archipelago_is_giving_item: bool;
// }
// item::set_bottle_pouch_slot(0xFFFFFFFF);
// item::set_number_of_items(0);
// let subtype = if can_remove_textbox(item_id) { 4 } else { 5 };
// let item_params = item::setup_item_params(item_id, subtype, 0, 0xFF, 1,
// 0xFF); let item = item::spawn_item(u32::MAX, item_params, 0, 0, 0, u32::MAX,
// 1); item::set_bottle_pouch_slot(u32::MAX);
// item::set_number_of_items(0);
// unsafe {
// archipelago_is_giving_item = true;
// }
// item as *mut c_void
// item::make_dummy_item(item_id) as *mut c_void
//
// extern "C" {
// fn AcItem__dtor(item: *mut c_void);
// fn AcItem__performCollection1and2(item: *mut c_void);
// fn AcItem__init(item: *mut c_void);
// }
// let shared_item = unsafe { &mut SHARED_AP_ITEM };
// match *shared_item {
// Some(item) => {
// unsafe { AcItem__performCollection1and2(item); }
// item
// }
// None => {
// item::set_bottle_pouch_slot(0xFFFFFFFF);
// item::set_number_of_items(0);
// let item_params = item::setup_item_params(item_id, 1, 0, 0xFF, 1, 0xFF);
// let item = item::spawn_item(u32::MAX, item_params, 0, 0, 0, u32::MAX,
// 1); item::set_bottle_pouch_slot(u32::MAX);
// item::set_number_of_items(0);
//
// unsafe {
// AcItem__init(item);
// AcItem__performCollection1and2(item);
// SHARED_AP_ITEM = Some(item);
// AcItem__dtor(item);
// }
// item
// },
// }
// }
//
// #[no_mangle]
// extern "C" fn done_ap_item(item: *mut Item) {
// extern "C" {
// static mut archipelago_is_giving_item: bool;
// }
//
// unsafe {
// archipelago_is_giving_item = false;
// }
// }

// #[no_mangle]
// extern "C" fn increment_item_queue() {
// unsafe {
// IS_GETTING_ITEM = true;
// }
// }

const AP_ITEM_BUFFER_SIZE: usize = 6;

extern "C" {
    static TITLE_LOADER_ADDR: u32;
    static mut ARCHIPELAGO_ITEM_SLOTS: [u8; AP_ITEM_BUFFER_SIZE]; // ring buffer
    static FRAME_COUNT: u32;
}

#[no_mangle]
extern "C" fn decrement_item_queue(item: *mut Item) {
    unsafe {
        if (*item).unkfield == AP_ITEM_MAGIC {
            // finished receiving an AP item
            (*item).unkfield = 0;
            // shift over the received item queue by one
            // we implement this as a ring buffer so it's guaranteed that any slot
            // that *was* 0xFF will stay 0xFF in the future (to avoid client race
            // conditions)
            ARCHIPELAGO_ITEM_SLOTS[CURR_ITEM_SLOT] = 0xFF;
            CURR_ITEM_SLOT += 1;
            if CURR_ITEM_SLOT == AP_ITEM_BUFFER_SIZE {
                CURR_ITEM_SLOT = 0;
            }
            IS_GETTING_ITEM = false;
        }
    }
}

// #[no_mangle]
// static mut ARCHIPELAGO_ITEM_SLOT: u8 = 0xFF;

#[no_mangle]
static mut CURR_AP_ARC: u8 = 0xFF;

#[no_mangle]
static mut IS_GETTING_ITEM: bool = false;

#[no_mangle]
static mut DID_DIE: bool = false;

#[no_mangle]
static mut CURR_ITEM_SLOT: usize = 0;

const AP_ITEM_MAGIC: u8 = 0xAB;

const ACTION_FLAG_MASK: u32 = 0xFFFFFFFF;

#[no_mangle]
pub fn give_ap_rs() {
    if let Some(link) = player::as_ref() {
        // don't give items on the title screen!!
        if unsafe { TITLE_LOADER_ADDR } != 0 {
            unsafe {
                ARCHIPELAGO_ITEM_SLOTS = [0xFF; AP_ITEM_BUFFER_SIZE];
            };
            return;
        }
        let item_id = unsafe { ARCHIPELAGO_ITEM_SLOTS[CURR_ITEM_SLOT] };
        let getting_item = unsafe { IS_GETTING_ITEM };
        let current_item_arc = unsafe { CURR_AP_ARC };
        // is this hacky? yes. do I care? immensely, but I need to prevent bad things
        // from happening, okay
        let frame_count = unsafe { FRAME_COUNT };
        if get_current_health() == 0 {
            unsafe {
                DID_DIE = true;
            }
            return;
        }
        if unsafe { DID_DIE } {
            if frame_count == 19 {
                unsafe {
                    DID_DIE = false;
                }
            } else {
                return;
            }
        }
        if item_id == 0xFF {
            // switch to next item in the ring buffer, try next frame
            unsafe {
                CURR_ITEM_SLOT += 1;
                if CURR_ITEM_SLOT == AP_ITEM_BUFFER_SIZE {
                    CURR_ITEM_SLOT = 0;
                }
            }
            return;
        }
        // is Link on foot or in water?
        // is the item ID not 0xFF?
        // is Link not receiving another item?
        if link.actionflags & ACTION_FLAG_MASK != 0 && !getting_item {
            let is_minor_item = can_remove_textbox(item_id.into());
            if is_minor_item {
                // just give the item directly, no need to load in any arcs
                item::set_bottle_pouch_slot(0xFFFFFFFF);
                item::set_number_of_items(0);
                // subtype 4 means no textbox
                let item_params = item::setup_item_params(item_id.into(), 4, 0, 0xFF, 1, 0xFF);
                let item = item::spawn_item(u32::MAX, item_params, 0, 0, 0, u32::MAX, 1);
                item::set_bottle_pouch_slot(u32::MAX);
                item::set_number_of_items(0);
                unsafe {
                    (*item).unkfield = AP_ITEM_MAGIC;
                    IS_GETTING_ITEM = true;
                };
            } else {
                if current_item_arc == 0xFF {
                    load_arcs_for_item(item_id.into());
                    unsafe {
                        CURR_AP_ARC = item_id;
                    };
                }
                if unsafe { CURR_AP_ARC } == item_id && check_arcs_loaded(item_id.into()) {
                    item::set_bottle_pouch_slot(0xFFFFFFFF);
                    item::set_number_of_items(0);
                    // subtype 5 means textbox
                    let item_params = item::setup_item_params(item_id.into(), 5, 0, 0xFF, 1, 0xFF);
                    let item = item::spawn_item(u32::MAX, item_params, 0, 0, 0, u32::MAX, 1);
                    item::set_bottle_pouch_slot(u32::MAX);
                    item::set_number_of_items(0);
                    unsafe {
                        (*item).unkfield = AP_ITEM_MAGIC;
                        CURR_AP_ARC = 0xFF;
                        IS_GETTING_ITEM = true;
                    };
                    unload_arcs_for_item(item_id.into());
                }
            }
        }
    } else {
        unsafe {
            IS_GETTING_ITEM = false;
        }
    }
}

#[no_mangle]
pub fn add_more_colors() {
    extern "C" {
        static mut FONT_COLORS_1: [u32; 49];
        static mut FONT_COLORS_2: [u32; 49];
    }
    // Indices 39 and 41 in the color table are unused
    unsafe {
        // Slateblue
        FONT_COLORS_1[0x27] = 0x4040C0FF;
        FONT_COLORS_2[0x27] = 0x202080FF;
        // Magenta
        FONT_COLORS_1[0x29] = 0xFF00FFFF;
        FONT_COLORS_2[0x29] = 0xC800C8FF;
    }
}
