from aiogram.fsm.state import StatesGroup, State


class UserMenuState(StatesGroup):
    main_menu = State()
    vpn_panel = State()
    subscription = State()
    configure = State()
    pay = State()
    gift = State()
    referral = State()
    help = State()
    about = State()
