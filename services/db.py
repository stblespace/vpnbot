import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

DB_PATH = Path("data/subscriptions.db")


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_code TEXT NOT NULL,
                period_code TEXT NOT NULL,
                price INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _row_to_dict(row: tuple) -> Dict[str, Any]:
    keys = ["id", "user_id", "plan_code", "period_code", "price", "created_at", "expires_at"]
    return dict(zip(keys, row))


def create_subscription(
    user_id: int,
    plan_code: str,
    period_code: str,
    price: int,
    expires_at: datetime,
) -> Dict[str, Any]:
    now = datetime.utcnow()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """
            INSERT INTO subscriptions (user_id, plan_code, period_code, price, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                plan_code,
                period_code,
                price,
                now.isoformat(),
                expires_at.isoformat(),
            ),
        )
        subscription_id = cur.lastrowid
        conn.commit()
    return {
        "id": subscription_id,
        "user_id": user_id,
        "plan_code": plan_code,
        "period_code": period_code,
        "price": price,
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
    }


def get_latest_subscription(user_id: int) -> Optional[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            """
            SELECT id, user_id, plan_code, period_code, price, created_at, expires_at
            FROM subscriptions
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
    if row:
        return _row_to_dict(row)
    return None


def get_subscription_by_id(subscription_id: int) -> Optional[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            """
            SELECT id, user_id, plan_code, period_code, price, created_at, expires_at
            FROM subscriptions
            WHERE id = ?
            LIMIT 1
            """,
            (subscription_id,),
        ).fetchone()
    if row:
        return _row_to_dict(row)
    return None


def days_left(expires_at: str) -> Optional[int]:
    try:
        expires = datetime.fromisoformat(expires_at)
    except ValueError:
        return None
    delta = expires - datetime.utcnow()
    if delta.total_seconds() < 0:
        return 0
    return delta.days + (1 if delta.seconds > 0 else 0)
