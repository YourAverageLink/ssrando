use core::{
    ffi::{c_char, c_uint, c_void, CStr},
    fmt::Debug,
};

use arrayvec::ArrayVec;

use crate::game::flag_managers::Itemflag;
use crate::system::math::*;

extern "C" {
    static mut ITEM_GET_BOTTLE_POUCH_SLOT: u32;
    static mut NUMBER_OF_ITEMS: u32;

    fn getKeyPieceCount() -> u16;
    fn AcItem__setFlagForItem(itemflag: u16);
    fn AcItem__setupItemParams(
        item_id: u16,
        subtype: u32,
        unk1: u32,
        sceneflag: u32,
        unk2: u32,
        unk3: u32,
    ) -> u32;
    fn AcItem__spawnItem(
        room: u32,
        item_params: u32,
        pos: u32,   // actually Vec3f
        rot: u32,   // actually Vec3s
        scale: u32, // actually Vec3f
        params2: u32,
        unk: u32,
    ) -> *mut c_void;
    pub fn spawnDrop(itemid: Itemflag, roomid: u32, pos: *mut Vec3f, rot: *mut Vec3s);

    static ITEM_TO_MODEL_INDEX: [u16; 512];
    static ITEM_MODEL_INDEX: [u8; 168];
    static ITEM_MODEL_DEFS: [ItemModelDef; 106];
    static MODEL_ID_TO_PUT_ITEM_MODEL_IDX: [u8; 168];
    static PUT_ITEM_MODEL_NAMES: [PutItemModelNameDef; 10];
    static GET_SHIELD_MODEL_INDEX: [u8; 168];
    static GET_SHIELD_MODEL_NAMES: [GetShieldStruct; 9];
    static GET_BOTTLE_MODEL_INDEX: [u8; 168];
    static GET_BOTTLE_MODEL_NAMES: [GetBottleNameDef; 8];
    static GET_POTION_BOTTLE_MODEL_INDEX: [u8; 168];
    static GET_POTION_BOTTLE_DEFS: [GetPotionBottleNameDef; 4];
}

#[repr(C)]
pub struct ItemModelDef {
    pub arc_name:   *const c_char,
    pub model_name: *const c_char,
}

#[repr(C)]
pub struct PutItemModelNameDef {
    pub put_arc_name:   *const c_char,
    pub put_model_name: *const c_char,
    pub get_arc_name:   *const c_char,
    pub get_model_name: *const c_char,
}

#[repr(C)]
pub struct GetShieldStruct {
    pub unk:        f32,
    pub arc_name:   *const c_char,
    pub model_name: *const c_char,
    pub equip_name: *const c_char,
}

#[repr(C)]
pub struct GetBottleNameDef {
    pub arc_name:   *const c_char,
    pub model_name: *const c_char,
    pub equip_name: *const c_char,
}

#[repr(C)]
pub struct GetPotionBottleNameDef {
    pub name1: *const c_char,
    pub name2: *const c_char,
    pub name3: *const c_char,
    pub name4: *const c_char,
}

pub fn get_bottle_pouch_slot() -> u32 {
    unsafe { ITEM_GET_BOTTLE_POUCH_SLOT }
}

pub fn set_bottle_pouch_slot(val: u32) {
    unsafe { ITEM_GET_BOTTLE_POUCH_SLOT = val };
}

pub fn get_number_of_items() -> u32 {
    unsafe { NUMBER_OF_ITEMS }
}

pub fn set_number_of_items(val: u32) {
    unsafe { NUMBER_OF_ITEMS = val };
}

pub fn get_key_piece_count() -> u16 {
    unsafe { getKeyPieceCount() }
}

pub fn spawn_item(
    room: u32,
    item_params: u32,
    pos: u32,   // actually Vec3f
    rot: u32,   // actually Vec3s
    scale: u32, // actually Vec3f
    params2: u32,
    unk: u32,
) -> *mut Item {
    unsafe { AcItem__spawnItem(room, item_params, pos, rot, scale, params2, unk) as *mut Item }
}

pub fn setup_item_params(
    item_id: u16,
    subtype: u32,
    unk1: u32,
    sceneflag: u32,
    unk2: u32,
    unk3: u32,
) -> u32 {
    unsafe { AcItem__setupItemParams(item_id, subtype, unk1, sceneflag, unk2, unk3) }
}

pub fn set_flag_for_item(itemflag: u16) {
    unsafe { AcItem__setFlagForItem(itemflag) };
}

pub fn get_item_model_def_for_item(item_id: u16) -> Option<&'static ItemModelDef> {
    unsafe {
        ITEM_TO_MODEL_INDEX
            .get(item_id as usize)
            .and_then(|model| ITEM_MODEL_INDEX.get(*model as usize))
            .and_then(|model| ITEM_MODEL_DEFS.get(*model as usize))
    }
}
pub enum ArcNames {
    None,
    One([*const c_char; 1]),
    Two([*const c_char; 2]),
}

impl ArcNames {
    pub fn slice(&self) -> &[*const c_char] {
        match self {
            ArcNames::None => &[],
            ArcNames::One(x) => x,
            ArcNames::Two(x) => x,
        }
    }
}

impl Debug for ArcNames {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        match self {
            ArcNames::None => f.write_str("None"),
            ArcNames::One([name]) => {
                let s = unsafe { CStr::from_ptr(*name).to_str().unwrap_unchecked() };
                f.write_fmt(format_args!("One({s})"))
            },
            ArcNames::Two([name1, name2]) => {
                let s1 = unsafe { CStr::from_ptr(*name1).to_str().unwrap_unchecked() };
                let s2 = unsafe { CStr::from_ptr(*name2).to_str().unwrap_unchecked() };
                f.write_fmt(format_args!("Two({s1}, {s2})"))
            },
        }
    }
}

pub fn get_item_arc_names_for_item(item_id: u16) -> ArrayVec<*const c_char, 2> {
    fn single_arrayvec(s: *const c_char) -> ArrayVec<*const c_char, 2> {
        let mut v = ArrayVec::new();
        v.push(s);
        v
    }
    // custom rando models
    match item_id {
        214 => return single_arrayvec(cstr::cstr!("Onp").as_ptr()), // tadtone
        215 => return single_arrayvec(cstr::cstr!("DesertRobot").as_ptr()), // scrapper
        216 => return single_arrayvec(cstr::cstr!("GetKobunALetter").as_ptr()), // ap item
        217 => return single_arrayvec(cstr::cstr!("GetSwordA").as_ptr()), // ap sword
        218 => return single_arrayvec(cstr::cstr!("GetHarp").as_ptr()), // ap harp
        219 => return single_arrayvec(cstr::cstr!("GetBowA").as_ptr()), // ap bow
        220 => return single_arrayvec(cstr::cstr!("GetHookShot").as_ptr()), // ap clawshots
        221 => return single_arrayvec(cstr::cstr!("GetBirdStatue").as_ptr()), // ap spiral charge
        222 => return single_arrayvec(cstr::cstr!("GetVacuum").as_ptr()), // ap bellows
        223 => return single_arrayvec(cstr::cstr!("GetPachinkoA").as_ptr()), // ap slingshot
        224 => return single_arrayvec(cstr::cstr!("GetBeetleA").as_ptr()), // ap beetle
        225 => return single_arrayvec(cstr::cstr!("GetMoleGloveA").as_ptr()), // ap mitts
        226 => return single_arrayvec(cstr::cstr!("GetUroko").as_ptr()), // ap scale
        227 => return single_arrayvec(cstr::cstr!("GetNetA").as_ptr()), // ap net
        228 => return single_arrayvec(cstr::cstr!("GetBombBag").as_ptr()), // ap bomb bag
        229 => return single_arrayvec(cstr::cstr!("GetTriForceSingle").as_ptr()), // ap triforce
        230 => return single_arrayvec(cstr::cstr!("GetWhip").as_ptr()), // ap whip
        231 => return single_arrayvec(cstr::cstr!("GetEarring").as_ptr()), // ap earrings
        232 => return single_arrayvec(cstr::cstr!("GetSozaiC").as_ptr()), // ap tumbleweed
        233 => return single_arrayvec(cstr::cstr!("GetSekibanMapA").as_ptr()), // ap emerald tablet
        234 => return single_arrayvec(cstr::cstr!("GetSekibanMapB").as_ptr()), // ap ruby tablet
        235 => return single_arrayvec(cstr::cstr!("GetSekibanMapC").as_ptr()), // ap amber tablet
        236 => return single_arrayvec(cstr::cstr!("GetSirenKey").as_ptr()), // ap stone of trials
        237 => return single_arrayvec(cstr::cstr!("DesertRobot").as_ptr()), // ap scrapper
        238 => return single_arrayvec(cstr::cstr!("GetMap").as_ptr()), // ap map
        239 => return single_arrayvec(cstr::cstr!("GetKeySmall").as_ptr()), // ap small key
        240 => return single_arrayvec(cstr::cstr!("GetKeyBoss2A").as_ptr()), // ap ac boss key
        241 => return single_arrayvec(cstr::cstr!("GetKeyBoss2B").as_ptr()), // ap fs boss key
        242 => return single_arrayvec(cstr::cstr!("GetKeyBoss2C").as_ptr()), // ap ssh boss key
        243 => return single_arrayvec(cstr::cstr!("GetKeyBossA").as_ptr()), // ap sv boss key
        244 => return single_arrayvec(cstr::cstr!("GetKeyBossB").as_ptr()), // ap et boss key
        245 => return single_arrayvec(cstr::cstr!("GetKeyBossC").as_ptr()), // ap lmf boss key
        _ => (),
    }
    unsafe {
        if let Some(model_idx) = ITEM_TO_MODEL_INDEX.get(item_id as usize).copied() {
            // dummy entry
            if model_idx == 0xA7 {
                return ArrayVec::new();
            }
            if let Some(item_model_def) = ITEM_MODEL_INDEX
                .get(model_idx as usize)
                .and_then(|model| ITEM_MODEL_DEFS.get(*model as usize))
            {
                return single_arrayvec(item_model_def.arc_name);
            }
            if let Some(put_model_def) = MODEL_ID_TO_PUT_ITEM_MODEL_IDX
                .get(model_idx as usize)
                .and_then(|model| PUT_ITEM_MODEL_NAMES.get(*model as usize))
            {
                return ArrayVec::from([put_model_def.put_arc_name, put_model_def.get_arc_name]);
            }
            if let Some(shield_model_def) = GET_SHIELD_MODEL_INDEX
                .get(model_idx as usize)
                .and_then(|model| GET_SHIELD_MODEL_NAMES.get(*model as usize))
            {
                return single_arrayvec(shield_model_def.arc_name);
            }
            if let Some(bottle_model_def) = GET_BOTTLE_MODEL_INDEX
                .get(model_idx as usize)
                .and_then(|model| GET_BOTTLE_MODEL_NAMES.get(*model as usize))
            {
                return single_arrayvec(bottle_model_def.arc_name);
            }
            if let Some(potion_model_def) = GET_POTION_BOTTLE_MODEL_INDEX
                .get(model_idx as usize)
                .and_then(|model| GET_POTION_BOTTLE_DEFS.get(*model as usize))
            {
                return single_arrayvec(potion_model_def.name1);
            }
        }
    }
    ArrayVec::new()
}

fn play_item_sound(id: u16) {
    extern "C" {
        static mut SMALL_SFX_MANAGER: *mut c_void;
        fn playSound(manager: *mut c_void, id: u16);
    }

    unsafe { playSound(SMALL_SFX_MANAGER, id) }
}

pub fn give_item_by_id(item_id: u16) {
    match item_id {
        _ => {},
    }
}

#[repr(C)]
pub struct DummyItem {
    base:      [u8; 0x60],
    vtable:    *const DummyItemVTable,
    pad:       [u8; 0x44],
    params:    u32,
    pad2:      [u8; 0x284],
    item_id:   u16,
    pad3:      [u8; 0x586],
    state_mgr: *mut c_void,
}

#[repr(C)]
pub struct Item {
    pad:                               [u8; 0xD2C],
    pub frames_in_air:                 u32,
    pad2:                              u32,
    pub show_no_model_and_other_flags: u32,
    pad3:                              [u8; 0x2F],
    pub unkfield:                      u8,
}

#[repr(C)]
struct DummyItemVTable {
    stuff:       [u8; 0x80],
    get_item_id: extern "C" fn(item: *mut DummyItem) -> c_uint,
}

static DUMMY_ITEM_VTABLE: DummyItemVTable = DummyItemVTable {
    stuff:       [0; 0x80],
    get_item_id: DummyItem__get_item_id,
};

static mut DUMMY_ITEM: DummyItem = DummyItem {
    base:      [0; 0x60],
    vtable:    &DUMMY_ITEM_VTABLE,
    pad:       [0; 0x44],
    params:    0,
    pad2:      [0; 0x284],
    item_id:   0,
    pad3:      [0; 0x586],
    state_mgr: core::ptr::null_mut(),
};

static mut IS_DUMMY_ITEM_INIT: bool = false;

extern "C" fn DummyItem__get_item_id(item: *mut DummyItem) -> c_uint {
    unsafe { (*item).params & 0x1FF }
}

pub fn make_dummy_item(item_id: u16) -> *mut DummyItem {
    extern "C" {
        fn AcItem__ctor(item: *mut DummyItem);
        fn AcItem__dtor(item: *mut c_void);
        fn AcItem__performCollection1and2(item: *mut c_void);
        fn AcItem__init(item: *mut c_void);
    }
    unsafe {
        if !IS_DUMMY_ITEM_INIT {
            AcItem__ctor(&mut DUMMY_ITEM);
            IS_DUMMY_ITEM_INIT = true;
        }
    }
    set_bottle_pouch_slot(0xFFFFFFFF);
    set_number_of_items(0);
    let item_params = setup_item_params(item_id, 1, 0, 0xFF, 1, 0xFF);
    let dummy_item = unsafe { &mut DUMMY_ITEM };
    dummy_item.params = item_params;
    dummy_item.item_id = item_id;
    set_bottle_pouch_slot(u32::MAX);
    set_number_of_items(0);

    unsafe {
        AcItem__performCollection1and2(dummy_item as *mut DummyItem as *mut c_void);
        // AcItem__dtor(item);
    }
    dummy_item
}
