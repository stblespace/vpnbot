import logging
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta

from keyboards import *
from fsm.user_state import UserMenuState
from messages import *
from services.pg_repo import (
    AsyncSessionLocal,
    create_or_extend_subscription,
    days_left,
    get_latest_subscription,
    get_subscription_by_id,
)

router = Router()
logger = logging.getLogger(__name__)


async def _subscription_context(user_id: int) -> tuple:
    async with AsyncSessionLocal() as session:
        existing = await get_latest_subscription(session, user_id)
    if existing:
        sub_id = str(existing["id"])
        days = days_left(existing["expires_at"])
        return existing, sub_id, days if days is not None else DEFAULT_SUBSCRIPTION_DAYS_LEFT
    return None, DEFAULT_SUBSCRIPTION_ID, DEFAULT_SUBSCRIPTION_DAYS_LEFT


def _expiry_from_period(period_code: str) -> datetime:
    meta = get_period_meta(period_code)
    days = meta.get("duration_days", 30)
    return datetime.utcnow() + timedelta(days=days)


async def _subscription_detail_payload(subscription_id: str) -> tuple:
    record = None
    if subscription_id.isdigit():
        async with AsyncSessionLocal() as session:
            record = await get_subscription_by_id(session, int(subscription_id))
    if record:
        days = days_left(record["expires_at"]) or 0
        plan_text = plan_label(record["plan_code"])
    else:
        days = DEFAULT_SUBSCRIPTION_DAYS_LEFT
        plan_text = DEFAULT_SUBSCRIPTION_PLAN
    return plan_text, days


async def send_banner_or_stub(message: Message) -> None:
    if WELCOME_BANNER_URL:
        await message.answer_photo(WELCOME_BANNER_URL)
    else:
        await message.answer(BANNER_STUB_TEXT)


async def send_main_menu(message: Message) -> None:
    await message.answer(MAIN_MENU_TEXT, reply_markup=inline_main_menu_kb())


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.set_state(UserMenuState.main_menu)
    await message.answer(AFTER_MAIN_MENU_PROMPT, reply_markup=reply_main_kb())
    await send_banner_or_stub(message)
    await send_main_menu(message)


@router.message(F.text == "Помощь")
async def reply_help(message: Message, state: FSMContext) -> None:
    await state.set_state(UserMenuState.help)
    await message.answer(HELP_TEXT, reply_markup=back_to_main_kb())


@router.message(F.text == "Главное меню")
async def reply_main_menu(message: Message, state: FSMContext) -> None:
    await state.set_state(UserMenuState.main_menu)
    await send_banner_or_stub(message)
    await send_main_menu(message)


@router.callback_query(F.data.startswith(MAIN_MENU_PREFIX))
async def inline_menu_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    action = callback.data[len(MAIN_MENU_PREFIX):]

    if action == "vpn_panel":
        await state.set_state(UserMenuState.vpn_panel)
        _, sub_id, days_left_value = await _subscription_context(callback.from_user.id)
        await callback.message.edit_text(
            VPN_PANEL_TEXT,
            reply_markup=vpn_panel_kb(sub_id, days_left_value),
        )
    elif action == "gift":
        await state.set_state(UserMenuState.gift)
        await callback.message.edit_text(GIFT_TEXT, reply_markup=back_to_main_kb())
    elif action == "referral":
        await state.set_state(UserMenuState.referral)
        await callback.message.edit_text(REFERRAL_TEXT, reply_markup=back_to_main_kb())
    elif action == "help":
        await state.set_state(UserMenuState.help)
        await callback.message.edit_text(HELP_TEXT, reply_markup=back_to_main_kb())
    elif action == "about":
        await state.set_state(UserMenuState.about)
        await callback.message.edit_text(ABOUT_TEXT, reply_markup=back_to_main_kb())
    elif action == "back":
        await state.set_state(UserMenuState.main_menu)
        await callback.message.edit_text(MAIN_MENU_TEXT, reply_markup=inline_main_menu_kb())


@router.callback_query(F.data.startswith(VPN_PANEL_PREFIX))
async def vpn_panel_actions(callback: CallbackQuery, state: FSMContext) -> None:
    action = callback.data[len(VPN_PANEL_PREFIX):]

    if action.startswith("active:"):
        subscription_id = action.split(":", maxsplit=1)[1] or DEFAULT_SUBSCRIPTION_ID
        await state.set_state(UserMenuState.subscription)
        plan_text, days_value = await _subscription_detail_payload(subscription_id)
        await callback.answer()
        await callback.message.edit_text(
            format_subscription_detail_text(
                subscription_id=subscription_id,
                days_left=days_value,
                plan=plan_text,
                link=DEFAULT_SUBSCRIPTION_LINK,
            ),
            reply_markup=subscription_detail_kb(subscription_id),
        )
    elif action == "new":
        await callback.answer(NEW_SUBSCRIPTION_STUB, show_alert=True)
    elif action == "back_list":
        await state.set_state(UserMenuState.vpn_panel)
        await callback.answer()
        _, sub_id, days_left_value = await _subscription_context(callback.from_user.id)
        await callback.message.edit_text(
            VPN_PANEL_TEXT,
            reply_markup=vpn_panel_kb(sub_id, days_left_value),
        )
    elif action.startswith("configure:"):
        subscription_id = action.split(":", maxsplit=1)[1] or DEFAULT_SUBSCRIPTION_ID
        await state.set_state(UserMenuState.configure)
        await callback.answer()
        await callback.message.edit_text(
            format_configure_subscription_text(subscription_id),
            reply_markup=configure_subscription_kb(subscription_id),
        )
    elif action.startswith("cfg_manual:"):
        await callback.answer(FEATURE_IN_DEV_STUB, show_alert=True)
    elif action.startswith("cfg_issue:"):
        await callback.answer(FEATURE_IN_DEV_STUB, show_alert=True)
    elif action.startswith("cfg_ok:"):
        await callback.answer("Отлично! Если понадобится помощь, нажмите «Не получается подключить».", show_alert=True)
    elif action.startswith("pay:"):
        subscription_id = action.split(":", maxsplit=1)[1] or DEFAULT_SUBSCRIPTION_ID
        await state.set_state(UserMenuState.pay)
        await callback.answer()
        await callback.message.edit_text(
            format_pay_subscription_text(subscription_id),
            reply_markup=pay_subscription_kb(subscription_id),
        )
    elif action.startswith("pay_ind:"):
        subscription_id = action.split(":", maxsplit=1)[1] or DEFAULT_SUBSCRIPTION_ID
        await callback.answer()
        await callback.message.edit_text(
            format_pay_plan_selected_text("ind"),
            reply_markup=pay_methods_kb(subscription_id, "ind"),
        )
    elif action.startswith("pay_family:"):
        subscription_id = action.split(":", maxsplit=1)[1] or DEFAULT_SUBSCRIPTION_ID
        await callback.answer()
        await callback.message.edit_text(
            format_pay_plan_selected_text("family"),
            reply_markup=pay_methods_kb(subscription_id, "family"),
        )
    elif action.startswith("pay_sbp:"):
        parts = action.split(":")
        plan_code = parts[1] if len(parts) > 1 else "ind"
        subscription_id = parts[2] if len(parts) > 2 else DEFAULT_SUBSCRIPTION_ID
        await callback.answer()
        await callback.message.edit_text(
            format_pay_sbp_text(plan_code),
            reply_markup=pay_sbp_kb(subscription_id, plan_code),
        )
    elif action.startswith("pay_sbp_period:"):
        parts = action.split(":")
        period = parts[1] if len(parts) > 1 else ""
        plan_code = parts[2] if len(parts) > 2 else "ind"
        subscription_id = parts[3] if len(parts) > 3 else DEFAULT_SUBSCRIPTION_ID
        await callback.answer()
        await callback.message.edit_text(
            format_pay_sbp_summary(plan_code, period),
            reply_markup=pay_sbp_confirm_kb(subscription_id, plan_code, period),
        )
    elif action.startswith("pay_sbp_back:"):
        parts = action.split(":")
        plan_code = parts[1] if len(parts) > 1 else "ind"
        subscription_id = parts[2] if len(parts) > 2 else DEFAULT_SUBSCRIPTION_ID
        await callback.answer()
        await callback.message.edit_text(
            format_pay_plan_selected_text(plan_code),
            reply_markup=pay_methods_kb(subscription_id, plan_code),
        )
    elif action.startswith("pay_sbp_confirm:"):
        parts = action.split(":")
        period_code = parts[1] if len(parts) > 1 else "1"
        plan_code = parts[2] if len(parts) > 2 else "ind"
        subscription_id = parts[3] if len(parts) > 3 else DEFAULT_SUBSCRIPTION_ID
        meta = get_period_meta(period_code)
        price = meta.get("price_value", 0)
        await callback.answer()
        await callback.message.answer(
            format_pay_sbp_payment_text(price),
            reply_markup=pay_sbp_payment_kb(price, period_code, plan_code, subscription_id),
        )
    elif action.startswith("pay_sbp_finalize:"):
        parts = action.split(":")
        period_code = parts[1] if len(parts) > 1 else "1"
        plan_code = parts[2] if len(parts) > 2 else "ind"
        user_subscription_id = parts[3] if len(parts) > 3 else DEFAULT_SUBSCRIPTION_ID
        meta = get_period_meta(period_code)
        price = meta.get("price_value", 0)
        expires = _expiry_from_period(period_code)
        async with AsyncSessionLocal() as session:
            record = await create_or_extend_subscription(session, callback.from_user.id, expires_at=expires)
        logger.info(
            "Подписка оформлена через меню",
            extra={
                "tg_id": callback.from_user.id,
                "subscription_id": record["id"],
                "token_prefix": record["token"][:6],
                "expires_at": record["expires_at"],
            },
        )
        remaining_days = days_left(record["expires_at"]) or 0
        remaining_hours = max(0, int((expires - datetime.utcnow()).total_seconds() // 3600))
        remaining_text = f"{remaining_days} дн {remaining_hours % 24} ч"
        await state.set_state(UserMenuState.subscription)
        await callback.answer("Баланс пополнен на {:.2f} RUB".format(price), show_alert=True)
        await callback.message.answer(
            format_payment_success_text(str(record["id"]), expires.strftime("%d.%m.%y %H:%M (MSK)"), remaining_text),
            reply_markup=subscription_detail_kb(str(record["id"])),
        )
    elif action.startswith("pay_card:") or action.startswith("pay_usdt:") or action.startswith("pay_bonus:") or action.startswith("pay_tstars:"):
        await callback.answer(PAY_METHOD_STUB, show_alert=True)
    elif action.startswith("pay_back_plan:"):
        parts = action.split(":")
        subscription_id = parts[2] if len(parts) > 2 else DEFAULT_SUBSCRIPTION_ID
        await callback.answer()
        await callback.message.edit_text(
            format_pay_subscription_text(subscription_id),
            reply_markup=pay_subscription_kb(subscription_id),
        )
    elif action.startswith("back_detail:"):
        subscription_id = action.split(":", maxsplit=1)[1] or DEFAULT_SUBSCRIPTION_ID
        await state.set_state(UserMenuState.subscription)
        plan_text, days_value = _subscription_detail_payload(subscription_id)
        await callback.answer()
        await callback.message.edit_text(
            format_subscription_detail_text(
                subscription_id=subscription_id,
                days_left=days_value,
                plan=plan_text,
                link=DEFAULT_SUBSCRIPTION_LINK,
            ),
            reply_markup=subscription_detail_kb(subscription_id),
        )
    elif any(action.startswith(prefix) for prefix in ("portal:", "devices:", "params:", "lte:", "pay:")):
        await callback.answer(FEATURE_IN_DEV_STUB, show_alert=True)
    else:
        await callback.answer()
