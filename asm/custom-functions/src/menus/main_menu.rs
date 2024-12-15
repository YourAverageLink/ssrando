use super::action_menu::ActionMenu;
use super::display_menu::DisplayMenu;
use super::warp_menu::WarpMenu;
use crate::system::button::*;
use crate::utils::char_writer::TextWriterBase;
use crate::utils::graphics::draw_rect;
use crate::utils::menu::SimpleMenu;

use wchar::wchz;

use core::ptr::addr_of_mut;

#[derive(Clone, Copy, PartialEq, Eq)]
enum MenuState {
    Off,
    MenuSelect,
    DisplayMenu,
    WarpMenu,
    ActionMenu,
}

impl MenuState {
    fn from_u32(num: u32) -> MenuState {
        match num {
            0 => MenuState::DisplayMenu,
            1 => MenuState::WarpMenu,
            2 => MenuState::ActionMenu,
            _ => MenuState::MenuSelect,
        }
    }
}

pub struct MainMenu {
    state:       MenuState,
    cursor:      u32,
    force_close: bool,
}

#[link_section = "data"]
#[no_mangle]
pub static mut MAIN_MENU: MainMenu = MainMenu {
    state:       MenuState::Off,
    cursor:      0,
    force_close: false,
};

impl super::Menu for MainMenu {
    fn enable() {
        if MainMenu::is_active() {
            return;
        };

        if is_down(Buttons::DPAD_RIGHT | Buttons::TWO) {
            unsafe { MAIN_MENU.state = MenuState::MenuSelect };
        }
    }
    fn disable() {
        unsafe { MAIN_MENU.force_close = true };
        // Removes possible interaction with the game
        set_buttons_not_pressed(
            Buttons::B
                | Buttons::A
                | Buttons::DPAD_RIGHT
                | Buttons::DPAD_DOWN
                | Buttons::DPAD_LEFT
                | Buttons::DPAD_UP
                | Buttons::TWO,
        );
    }
    fn input() {
        let main_menu = unsafe { &mut *addr_of_mut!(MAIN_MENU) };
        match main_menu.state {
            // MenuState::Off => {},
            MenuState::MenuSelect => {
                if is_pressed(B) {
                    main_menu.state = MenuState::Off;
                    set_buttons_not_pressed(B);
                } else if is_pressed(A) {
                    main_menu.state = MenuState::from_u32(main_menu.cursor);
                    match main_menu.state {
                        MenuState::DisplayMenu => DisplayMenu::enable(),
                        MenuState::WarpMenu => WarpMenu::enable(),
                        MenuState::ActionMenu => ActionMenu::enable(),
                        _ => {},
                    };
                }
            },
            MenuState::DisplayMenu => DisplayMenu::input(),
            MenuState::WarpMenu => WarpMenu::input(),
            MenuState::ActionMenu => ActionMenu::input(),
            _ => {},
        }
    }
    fn display() {
        let main_menu = unsafe { &mut *addr_of_mut!(MAIN_MENU) };

        // Draw the input Guide
        if MainMenu::is_active() {
            draw_rect(0f32, 0f32, 640f32, 480f32, 0.0f32, 0x000000C0);
            let mut writer = TextWriterBase::new();
            writer.set_font_color(0xFFFFFFFF, 0xFFFFFFFF);
            writer.set_position(10f32, 420f32);
            writer.print_symbol(wchz!(u16, "\x20"));
            writer.print(wchz!(u16, "Select\t"));
            writer.print_symbol(wchz!(u16, "\x21"));
            writer.print(wchz!(u16, "Back\t"));
            writer.print_symbol(wchz!(u16, "\x2F\x30"));
            writer.print(wchz!(u16, "Up/Down\t"));
            writer.print_symbol(wchz!(u16, "\x31\x32"));
            writer.print(wchz!(u16, "Change Value"));
        }

        match main_menu.state {
            MenuState::Off => {},
            MenuState::MenuSelect => {
                let mut menu: SimpleMenu<5> = SimpleMenu::new();
                menu.set_heading("Main Menu Select");
                menu.set_cursor(main_menu.cursor);
                menu.add_entry("On Screen Display");
                menu.add_entry("Warp");
                menu.add_entry("Actions");
                menu.draw();

                main_menu.cursor = menu.move_cursor();
            },
            MenuState::DisplayMenu => {
                DisplayMenu::display();
                if !DisplayMenu::is_active() {
                    main_menu.state = MenuState::MenuSelect;
                }
            },
            MenuState::WarpMenu => {
                WarpMenu::display();
                if !WarpMenu::is_active() {
                    main_menu.state = MenuState::MenuSelect;
                }
            },
            MenuState::ActionMenu => {
                ActionMenu::display();
                if !ActionMenu::is_active() {
                    main_menu.state = MenuState::MenuSelect;
                }
            },
        }
        if main_menu.force_close {
            main_menu.force_close = false;
            main_menu.state = MenuState::Off;
        }
    }
    fn is_active() -> bool {
        unsafe { MAIN_MENU.state != MenuState::Off }
    }
}
