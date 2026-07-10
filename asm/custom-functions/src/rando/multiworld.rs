use core::{fmt::Write, str::from_utf8};

use crate::{
    game::{
        file_manager,
        flag_managers::SceneflagManager,
        item::{self, Item},
        minigame,
        player::{self, ActorLink},
        reloader::{self, get_spawn_slave},
    },
    rando::item_arc_loader,
    system::mutex::{WiiLockGuard, WiiMutex},
    utils::console::Console,
};

// Contains info the AP client needs to know whether it can
// send certain requests to the game
#[repr(C)]
pub struct APStatusReport {
    stage_name:         [u8; 16],
    last_received_item: u16,
    link_exists:        bool,
    is_on_title_screen: bool,
    is_dead:            bool,
    is_out_of_stamina:  bool,
}

impl APStatusReport {
    pub fn new() -> Self {
        let spawn_slave = reloader::get_spawn_slave();
        unsafe {
            let mut stage_name = [0u8; 16];
            stage_name.copy_from_slice(&spawn_slave.name[0..16]);
            let link = player::as_ref();
            Self {
                stage_name,
                last_received_item: ARCHIPELAGO_EXPECTED_INDEX,
                link_exists: link.is_some(),
                is_on_title_screen: TITLE_LOADER_ADDR != 0,
                is_dead: file_manager::get_current_health() == 0,
                is_out_of_stamina: match link {
                    Some(p) => p.stamina_amount == 0,
                    None => false,
                },
            }
        }
    }
}

pub fn is_on_title_screen() -> bool {
    (unsafe { TITLE_LOADER_ADDR }) != 0
}

pub fn deplete_stamina() -> bool {
    if let Some(link) = player::as_mut() {
        link.field_0x43dc = 0x7F;
        link.field_0x4379 = 0x1E;
        link.field_0x437a = 0x19;
        link.stamina_amount = 0;
        return true;
    }

    false
}

pub fn kill_link() -> bool {
    if player::as_ref().is_some()
        && minigame::SpecialMinigameState::is_current(minigame::SpecialMinigameState::StateNone)
    {
        file_manager::set_current_health(0);
        return true;
    }

    false
}

#[link_section = "data"]
#[no_mangle]
pub static mut ARCHIPELAGO_TEXT_BUFFER: [u8; 0x400] = [0; 0x400];

#[link_section = "data"]
#[no_mangle]
pub static mut ARCHIPELAGO_SLOT_NAME: [u8; 0x10] = [0; 0x10];

const AP_ITEM_BUFFER_SIZE: usize = 2;

extern "C" {
    static TITLE_LOADER_ADDR: u32;
    static mut ARCHIPELAGO_ITEM_SLOTS: [u8; AP_ITEM_BUFFER_SIZE];
    static mut ARCHIPELAGO_EXPECTED_INDEX: u16;
    static FRAME_COUNT: u32;
}

// const ITEM_MUTEX: WiiMutex = WiiMutex::new();
//
// struct ItemQueue {
// mutex: WiiMutex,
// slots: &'static mut [u8; AP_ITEM_BUFFER_SIZE],
// head_idx: u8,
// tail_idx: u8,
// receiving_item: bool,
// loaded_arc: u8,
// }
//
// impl ItemQueue {
// fn wrapping_inc(idx: u8) -> u8 {
// if idx as usize == AP_ITEM_BUFFER_SIZE - 1 {
// return 0;
// }
//
// idx + 1
// }
//
// fn try_acquire() -> Option<(&'static mut Self, WiiLockGuard<'static>)> {
// if let Some(g) = ITEM_MUTEX.try_lock() {
// return Some((unsafe { &mut ITEM_QUEUE }, g));
// }
//
// None
// }
//
// fn push_item(&mut self, item_id: u8) -> bool {
// let new_tail = ItemQueue::wrapping_inc(self.tail_idx);
// if new_tail == self.head_idx {
// return false;
// }
//
// unsafe {
// ARCHIPELAGO_ITEM_SLOTS[self.tail_idx as usize] = item_id;
// ARCHIPELAGO_EXPECTED_INDEX += 1;
// }
//
// self.tail_idx = new_tail;
// true
// }
//
// fn peek_item(&mut self) -> Option<u8> {
// if self.head_idx == self.tail_idx {
// return None;
// }
//
// let ret = unsafe { ARCHIPELAGO_ITEM_SLOTS[self.head_idx as usize] };
// Some(ret)
// }
//
// fn pop_item(&mut self) -> Option<u8> {
// if self.head_idx == self.tail_idx {
// return None;
// }
//
// let ret = unsafe { ARCHIPELAGO_ITEM_SLOTS[self.head_idx as usize] };
// unsafe {
// ARCHIPELAGO_ITEM_SLOTS[self.head_idx as usize] = EMPTY_SLOT;
// }
// Some(ret)
// }
// }
//
// #[no_mangle]
// static mut ITEM_QUEUE: ItemQueue = ItemQueue {
// mutex: WiiMutex::new(),
// slots: &mut ARCHIPELAGO_ITEM_SLOTS,
// head_idx: 0,
// tail_idx: 0,
// receiving_item: false,
// loaded_arc: 0,
// };

#[no_mangle]
extern "C" fn decrement_item_queue(item: *mut Item) {
    unsafe {
        if (*item).unkfield == AP_ITEM_MAGIC {
            // finished receiving an AP item
            (*item).unkfield = 0;
            ARCHIPELAGO_ITEM_SLOTS[0] = ARCHIPELAGO_ITEM_SLOTS[1];
            ARCHIPELAGO_ITEM_SLOTS[1] = EMPTY_SLOT;
            IS_GETTING_ITEM = false;
        }
    }
}

#[no_mangle]
static mut CURR_AP_ARC: u8 = EMPTY_SLOT;

#[no_mangle]
static mut IS_GETTING_ITEM: bool = false;

#[no_mangle]
static mut DID_DIE: bool = false;

const AP_ITEM_MAGIC: u8 = 0xAB;
const EMPTY_SLOT: u8 = 0x00;

const ACTION_FLAG_MASK: u32 = 0xFFFFFFFF; // 0x80040000

fn can_receive_items(link: &ActorLink) -> bool {
    match link.state & 0x00FFFFFF {
        0 | 0x5A2C88 | 0x5A328C | 0xB4F450 | 0x5A31AC | 0x5A336C | 0x9796BC => {
            return false;
        },
        _ => {},
    }

    match link.current_action {
        0..=13 | 0x78 => {},
        _ => {
            return false;
        },
    }

    // if link.actionflags & ACTION_FLAG_MASK == 0 {
    //    return false;
    // }

    let spawn_slave = get_spawn_slave();
    let stage = get_spawn_slave().name;
    // don't give items in boss stages or dungeon crest areas
    if stage[0] == b'B' {
        return false;
    }

    // don't give items in the post-Harp sealed temple before Song from Impa
    // (prevents accidentally deleting items due to the reload; kinda hacky)
    if stage[0..4] == [b'F', b'4', b'0', b'2'] {
        return spawn_slave.layer != 2 || SceneflagManager::check_global(10, 29);
    }

    minigame::SpecialMinigameState::is_current(minigame::SpecialMinigameState::StateNone)
}

pub fn try_place_item(item_id: u8) -> bool {
    unsafe {
        if ARCHIPELAGO_ITEM_SLOTS[0] == EMPTY_SLOT {
            ARCHIPELAGO_ITEM_SLOTS[0] = item_id;
            ARCHIPELAGO_EXPECTED_INDEX += 1;
            return true;
        }

        if ARCHIPELAGO_ITEM_SLOTS[1] == EMPTY_SLOT {
            ARCHIPELAGO_ITEM_SLOTS[1] = item_id;
            ARCHIPELAGO_EXPECTED_INDEX += 1;
            return true;
        }
    }

    false
}

#[no_mangle]
pub fn give_ap_rs() {
    if let Some(link) = player::as_ref() {
        // don't give items on the title screen!!
        if is_on_title_screen() {
            return;
        }
        let item_id = unsafe { ARCHIPELAGO_ITEM_SLOTS[0] };
        let getting_item = unsafe { IS_GETTING_ITEM };
        let current_item_arc = unsafe { CURR_AP_ARC };
        // is this hacky? yes. do I care? immensely, but I need to prevent bad things
        // from happening, okay
        let frame_count = unsafe { FRAME_COUNT };
        if file_manager::get_current_health() == 0 {
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
        if item_id == EMPTY_SLOT {
            return;
        }
        // is Link not receiving another item?
        // if not, can he safely get items?
        if !getting_item && can_receive_items(link) {
            let is_minor_item = can_remove_textbox(item_id.into());
            if is_minor_item {
                // just give the item directly, no need to load in any arcs
                item::set_bottle_pouch_slot(0xFFFFFFFF);
                item::set_number_of_items(0);
                // subtype 4 means no textbox
                let item_params = item::setup_item_params(item_id.into(), 4, 0, 0xFF, 1, 0xFF);
                let item = item::spawn_item(u32::MAX, item_params, 0, 0, 0, u32::MAX, 1);
                unsafe {
                    (*item).unkfield = AP_ITEM_MAGIC;
                    IS_GETTING_ITEM = true;
                };
                item::set_bottle_pouch_slot(u32::MAX);
                item::set_number_of_items(0);
            } else {
                if current_item_arc == 0xFF || current_item_arc == EMPTY_SLOT {
                    item_arc_loader::load_arcs_for_item(item_id.into());
                    unsafe {
                        CURR_AP_ARC = item_id;
                    };
                }
                if unsafe { CURR_AP_ARC } == item_id
                    && item_arc_loader::check_arcs_loaded(item_id.into())
                {
                    item::set_bottle_pouch_slot(0xFFFFFFFF);
                    item::set_number_of_items(0);
                    // subtype 5 means textbox
                    let item_params = item::setup_item_params(item_id.into(), 5, 0, 0xFF, 1, 0xFF);
                    let item = item::spawn_item(u32::MAX, item_params, 0, 0, 0, u32::MAX, 1);
                    unsafe {
                        (*item).unkfield = AP_ITEM_MAGIC;
                        CURR_AP_ARC = EMPTY_SLOT;
                        IS_GETTING_ITEM = true;
                    };
                    item::set_bottle_pouch_slot(u32::MAX);
                    item::set_number_of_items(0);
                    item_arc_loader::unload_arcs_for_item(item_id.into());
                }
            }
        }
    } else {
        // we should retry giving items if Link transitioned stages
        // before finishing any itemgets
        unsafe {
            IS_GETTING_ITEM = false;
            CURR_AP_ARC = EMPTY_SLOT;
        }
    }
}

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
        // a bunch of treasures
        | 165
        | 171
        | 173
        | 175
        | 176 => true,
        _ => false,
    }
}

#[no_mangle]
pub fn print_archipelago_text() -> u32 {
    let text_cstr = unsafe { ARCHIPELAGO_TEXT_BUFFER };
    let mut last_char = 0;
    if text_cstr[0] != 0 {
        let mut top_height = 438f32;
        match from_utf8(&text_cstr) {
            Ok(text) => {
                for char in text_cstr.iter() {
                    // We want to move the text box up for each newline so it's bottom-justified
                    // Ignore if last character was 0x02, as that means it's part of a tag
                    // processor control sequence
                    if *char == b'\n' && last_char != 0x02 {
                        top_height -= 14f32;
                    }
                    last_char = *char;
                }

                let mut console = Console::with_pos(0f32, top_height);
                console.set_bg_color(0x00000055);
                console.set_font_color(0xFFFFFFFF);
                console.set_font_size(0.4f32);
                let _ = console.write_str(text);
                console.draw(false);
            },
            Err(_) => {
                let mut console = Console::with_pos(0f32, top_height);
                console.set_bg_color(0x00000055);
                console.set_font_color(0xFFFFFFFF);
                console.set_font_size(0.4f32);
                let _ = console.write_str("Utf8 parse error.");
                console.draw(false);
            },
        }
    }

    // Return 1 to tell the game to continue running
    1
}
