#![no_std]
#![feature(split_array)]
#![feature(allocator_api)]
#![feature(ascii_char)]
#![feature(format_args_nl)]
#![feature(slice_ptr_get)]
#![feature(slice_partition_dedup)]
#![feature(waker_getters)]
#![feature(noop_waker)]
#![allow(dead_code)]
#![deny(clippy::no_mangle_with_rust_abi)]
#![deny(improper_ctypes)]
#![deny(improper_ctypes_definitions)]

extern crate alloc;

mod game;
mod rando;
mod rvl_mem;
mod rvl_os;
mod system;
mod utils;

use alloc::boxed::Box;

use crate::rando::networking::{ServerProgress, SOCK_STATUS};
use crate::system::button;
use crate::utils::char_writer::TagProcessor;
use crate::utils::console::Console;
use core::fmt::Write;

#[macro_export]
macro_rules! print {
    ($($arg:tt)*) => {{
        $crate::utils::printf::debug_print(format_args!($($arg)*));
    }};
}

#[macro_export]
macro_rules! println {
    () => {
        $crate::print!("\n")
    };
    ($($arg:tt)*) => {{
        $crate::utils::printf::debug_print(format_args_nl!($($arg)*));
    }};
}

// Not actually mutable but needs to be to show up in custom_symbols
#[no_mangle]
#[link_section = "data"]
pub static mut SHOULD_PRINT_AP_BUFFER: bool = false;

#[no_mangle]
#[link_section = "data"]
pub static mut BUFFER_TAG_PROCESSOR: Option<Box<TagProcessor>> = None;

static mut INIT_CONNECTION_TIMER: u8 = 255;

// A Common Place where Custom code can be injected to run once per frame
// Returns whether or not to stop (1 == continue)
#[no_mangle]
fn custom_main_additions() -> u32 {
    unsafe {
        if INIT_CONNECTION_TIMER == 0 {
            crate::rando::networking::run_net_init();
            INIT_CONNECTION_TIMER = 255;
            if BUFFER_TAG_PROCESSOR.is_none() {
                // Create our own tag processor; subtype 27 means text defaults to white
                BUFFER_TAG_PROCESSOR = Some(Box::new(TagProcessor::with_window_subtype(27)));
            }
        } else if !SOCK_STATUS.active {
            INIT_CONNECTION_TIMER -= 1;
        }

        display_socket_status();
        if button::is_pressed(button::Z | button::C) {
            // Toggle IP display
            SOCK_STATUS.show_ip ^= true;
        }
    }

    rando::multiworld::give_ap_rs();
    if unsafe { SHOULD_PRINT_AP_BUFFER } {
        return crate::rando::multiworld::print_archipelago_text();
    }

    return 1;
}

fn display_socket_status() {
    let status = unsafe { &SOCK_STATUS };
    if status.last_error_code != 0 {
        let mut console = Console::with_pos(0f32, 0f32);
        console.set_bg_color(0x00000055);
        console.set_font_color(0xFFFFFFFF);
        console.set_font_size(0.5f32);
        let _ = console.write_fmt(format_args!(
            "Network code failed with error code {}",
            status.last_error_code
        ));
        match status.last_error_code {
            -10 => {
                let _ = console
                    .write_str("\n(network is busy)\nThis usually requires reopening the game.");
            },
            _ => {},
        }
        match status.progress {
            ServerProgress::None => {
                let _ = console.write_str("\nCouldn't create socket, try reopening the game");
            },
            ServerProgress::CreatedUDP => {
                let _ = console
                    .write_str("\nCreated UDP socket but couldn't bind, try reopening the game");
            },
            ServerProgress::BoundSocket => {
                let _ = console.write_str("\nBound UDP socket, make sure AP client is working,\n then try waiting for a connection");
            },
            _ => {
                let _ = console.write_str("\nConnection was active, try waiting for a reconnect");
            },
        }
        console.draw(false);
    } else if status.active && status.show_ip {
        let mut console = Console::with_pos(0f32, 0f32);
        console.set_bg_color(0x00000055);
        console.set_font_color(0xFFFFFFFF);
        console.set_font_size(0.5f32);
        if unsafe { rando::networking::EMULATOR_MODE } {
            if status.progress != ServerProgress::ConnectionEstablished {
                let _ = console.write_str("Waiting for connection from AP client");
            } else {
                let _ = console.write_str("Type /console 127.0.0.1 if connection was lost");
            }
        } else {
            if status.progress != ServerProgress::ConnectionEstablished {
                let _ = console.write_str("Waiting for connection from AP client\n");
            }
            let _ = console.write_fmt(format_args!("Type /console {}", status.ip));
        }
        console.draw(false);
    }
    // else if status.num_requests > 0 {
    // let mut console = Console::with_pos(0f32, 0f32);
    // console.set_bg_color(0x00000055);
    // console.set_font_color(0xFFFFFFFF);
    // console.set_font_size(0.5f32);
    // let _ = console.write_fmt(format_args!(
    // "Received {} requests so far",
    // status.num_requests
    // ));
    // console.draw(false);
    // }
}

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    // println!("{}", info);
    loop {}
}
