from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from messages import (
    BTN_INLINE_VPN_PANEL,
    BTN_INLINE_GIFT,
    BTN_INLINE_REFERRAL,
    BTN_INLINE_HELP,
    BTN_INLINE_ABOUT,
    BTN_INLINE_BACK_TO_MAIN,
    BTN_INLINE_NEW_SUBSCRIPTION,
    BTN_INLINE_BACK_TO_VPN_PANEL,
    BTN_INLINE_CONFIGURE,
    BTN_INLINE_DEVICES,
    BTN_INLINE_PARAMS,
    BTN_INLINE_LTE,
    BTN_INLINE_PAY,
    BTN_INLINE_BACK_TO_SUBSCRIPTION,
    BTN_INLINE_CFG_INDIVIDUAL,
    BTN_INLINE_CFG_FAMILY,
    BTN_INLINE_CFG_MANUAL,
    BTN_INLINE_CFG_ISSUE,
    BTN_INLINE_CFG_OK,
    BTN_PAY_CARD,
    BTN_PAY_SBP,
    BTN_PAY_USDT,
    BTN_PAY_BONUS,
    BTN_PAY_TSTARS,
    BTN_PAY_BACK_PLAN,
    BTN_PAY_BACK_METHODS,
    BTN_PAY_SBP_CONFIRM,
    BTN_REPLY_MAIN_MENU,
    BTN_REPLY_HELP,
    format_subscription_button,
    format_subscription_portal_button,
    PAY_SBP_PERIODS,
    pay_sbp_button_text,
)

MAIN_MENU_PREFIX = "main_menu:"
VPN_PANEL_PREFIX = "vpn_panel:"


def inline_main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_INLINE_VPN_PANEL, callback_data=f"{MAIN_MENU_PREFIX}vpn_panel")],
            [InlineKeyboardButton(text=BTN_INLINE_GIFT, callback_data=f"{MAIN_MENU_PREFIX}gift")],
            [InlineKeyboardButton(text=BTN_INLINE_REFERRAL, callback_data=f"{MAIN_MENU_PREFIX}referral")],
            [
                InlineKeyboardButton(text=BTN_INLINE_HELP, callback_data=f"{MAIN_MENU_PREFIX}help"),
                InlineKeyboardButton(text=BTN_INLINE_ABOUT, callback_data=f"{MAIN_MENU_PREFIX}about"),
            ],
        ]
    )


def reply_main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_REPLY_MAIN_MENU), KeyboardButton(text=BTN_REPLY_HELP)],
        ],
        resize_keyboard=True,
    )


def back_to_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_INLINE_BACK_TO_MAIN, callback_data=f"{MAIN_MENU_PREFIX}back")],
        ]
    )


def vpn_panel_kb(subscription_id: str, days_left: int | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=format_subscription_button(subscription_id, days_left),
                    callback_data=f"{VPN_PANEL_PREFIX}active:{subscription_id}",
                )
            ],
            [InlineKeyboardButton(text=BTN_INLINE_NEW_SUBSCRIPTION, callback_data=f"{VPN_PANEL_PREFIX}new")],
            [InlineKeyboardButton(text=BTN_INLINE_BACK_TO_MAIN, callback_data=f"{MAIN_MENU_PREFIX}back")],
        ]
    )


def subscription_detail_kb(subscription_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=format_subscription_portal_button(subscription_id),
                    callback_data=f"{VPN_PANEL_PREFIX}portal:{subscription_id}",
                )
            ],
            [InlineKeyboardButton(text=BTN_INLINE_CONFIGURE, callback_data=f"{VPN_PANEL_PREFIX}configure:{subscription_id}")],
            [InlineKeyboardButton(text=BTN_INLINE_DEVICES, callback_data=f"{VPN_PANEL_PREFIX}devices:{subscription_id}")],
            [InlineKeyboardButton(text=BTN_INLINE_PARAMS, callback_data=f"{VPN_PANEL_PREFIX}params:{subscription_id}")],
            [InlineKeyboardButton(text=BTN_INLINE_LTE, callback_data=f"{VPN_PANEL_PREFIX}lte:{subscription_id}")],
            [InlineKeyboardButton(text=BTN_INLINE_PAY, callback_data=f"{VPN_PANEL_PREFIX}pay:{subscription_id}")],
            [InlineKeyboardButton(text=BTN_INLINE_BACK_TO_VPN_PANEL, callback_data=f"{VPN_PANEL_PREFIX}back_list")],
        ]
    )


def configure_subscription_kb(subscription_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_INLINE_CFG_MANUAL, callback_data=f"{VPN_PANEL_PREFIX}cfg_manual:{subscription_id}")],
            [InlineKeyboardButton(text=BTN_INLINE_CFG_ISSUE, callback_data=f"{VPN_PANEL_PREFIX}cfg_issue:{subscription_id}")],
            [InlineKeyboardButton(text=BTN_INLINE_CFG_OK, callback_data=f"{VPN_PANEL_PREFIX}cfg_ok:{subscription_id}")],
            [InlineKeyboardButton(text=BTN_INLINE_BACK_TO_SUBSCRIPTION, callback_data=f"{VPN_PANEL_PREFIX}back_detail:{subscription_id}")],
        ]
    )


def pay_subscription_kb(subscription_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_INLINE_CFG_INDIVIDUAL, callback_data=f"{VPN_PANEL_PREFIX}pay_ind:{subscription_id}")],
            [InlineKeyboardButton(text=BTN_INLINE_CFG_FAMILY, callback_data=f"{VPN_PANEL_PREFIX}pay_family:{subscription_id}")],
            [InlineKeyboardButton(text=BTN_INLINE_BACK_TO_SUBSCRIPTION, callback_data=f"{VPN_PANEL_PREFIX}back_detail:{subscription_id}")],
        ]
    )


def pay_methods_kb(subscription_id: str, plan_code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_PAY_CARD, callback_data=f"{VPN_PANEL_PREFIX}pay_card:{plan_code}:{subscription_id}")],
            [InlineKeyboardButton(text=BTN_PAY_SBP, callback_data=f"{VPN_PANEL_PREFIX}pay_sbp:{plan_code}:{subscription_id}")],
            [InlineKeyboardButton(text=BTN_PAY_USDT, callback_data=f"{VPN_PANEL_PREFIX}pay_usdt:{plan_code}:{subscription_id}")],
            [InlineKeyboardButton(text=BTN_PAY_BONUS, callback_data=f"{VPN_PANEL_PREFIX}pay_bonus:{plan_code}:{subscription_id}")],
            [InlineKeyboardButton(text=BTN_PAY_TSTARS, callback_data=f"{VPN_PANEL_PREFIX}pay_tstars:{plan_code}:{subscription_id}")],
            [InlineKeyboardButton(text=BTN_PAY_BACK_PLAN, callback_data=f"{VPN_PANEL_PREFIX}pay_back_plan:{plan_code}:{subscription_id}")],
        ]
    )


def pay_sbp_kb(subscription_id: str, plan_code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            *[
                [InlineKeyboardButton(text=label, callback_data=f"{VPN_PANEL_PREFIX}pay_sbp_period:{period}:{plan_code}:{subscription_id}")]
                for period, label in PAY_SBP_PERIODS
            ],
            [InlineKeyboardButton(text=BTN_PAY_BACK_METHODS, callback_data=f"{VPN_PANEL_PREFIX}pay_sbp_back:{plan_code}:{subscription_id}")],
        ]
    )


def pay_sbp_confirm_kb(subscription_id: str, plan_code: str, period_code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_PAY_SBP_CONFIRM, callback_data=f"{VPN_PANEL_PREFIX}pay_sbp_confirm:{period_code}:{plan_code}:{subscription_id}")],
            [InlineKeyboardButton(text=BTN_PAY_BACK_METHODS, callback_data=f"{VPN_PANEL_PREFIX}pay_sbp_back:{plan_code}:{subscription_id}")],
        ]
    )


def pay_sbp_payment_kb(price: int, period_code: str, plan_code: str, subscription_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=pay_sbp_button_text(price),
                    callback_data=f"{VPN_PANEL_PREFIX}pay_sbp_finalize:{period_code}:{plan_code}:{subscription_id}",
                )
            ]
        ]
    )
