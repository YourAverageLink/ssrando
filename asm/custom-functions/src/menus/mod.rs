use self::main_menu::MainMenu;

mod action_menu;
mod display_menu;
mod main_menu;
mod warp_menu;

pub trait Menu {
    fn enable();
    fn disable();
    fn input();
    fn display();
    fn is_active() -> bool;
}

pub fn update() {
    MainMenu::enable();
    if MainMenu::is_active() {
        MainMenu::display();
        MainMenu::input();
    }
}

pub fn is_active() -> bool {
    MainMenu::is_active()
}
