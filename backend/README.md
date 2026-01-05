# Backend подписок для VLESS/Xray

Минимальный продакшен-ориентированный backend, который выдает подписку `/sub/{token}` для клиентов v2rayN, v2RayTun, Nekoray и Clash-совместимых клиентов. Конфиги генерируются на лету: в базе нет сохраненных файлов, только пользователи, подписки и список серверов.

## Что такое подписка
- Клиент опрашивает HTTP-адрес `GET /sub/{token}`.
- `token` уникален для подписки, не содержит персональных данных и должен быть негоден к подбору.
- Ответ `text/plain`, по одной VLESS-ссылке на строку. Каждая строка строится по данным из таблицы `servers`.
- При изменении серверов или статуса подписки ответ меняется автоматически — достаточно обновить подписку в клиенте.

## Быстрый старт
```bash
cd backend
cp .env.example .env  # при необходимости поправьте значения
docker compose up -d --build
```
- Backend поднимется на `http://localhost:8000`.
- Документация FastAPI: `http://localhost:8000/docs`.

## Переменные окружения
- `DATABASE_URL` — строка подключения `postgresql+asyncpg://...`.
- `BASE_SUB_URL` — базовый URL для формирования ссылок (используется ботом).
- `BOT_TOKEN` — токен бота для проверки подписи Telegram Mini App.
- `ADMIN_TG_IDS` — список Telegram ID через запятую, временно считаются администраторами.
- `LOG_LEVEL` — уровень логов (`INFO` по умолчанию).

## Структура
```
backend/
  app/
    api/subscription.py   # endpoint /sub/{token}
    services/             # бизнес-логика и генерация конфигов
    models/               # SQLAlchemy модели User/Subscription/Server
    db/session.py         # engine и фабрика сессий
    config.py             # настройки из окружения
    main.py               # сборка FastAPI
  Dockerfile
  docker-compose.yml
  .env.example
  requirements.txt
```

## Модели данных
- **users**: `id`, `tg_id` (Telegram ID), `uuid` (используется в VLESS ссылках), `is_active`.
- **subscriptions**: `id`, `user_id`, `token` (уникальный), `expires_at`, `is_active`.
- **servers**: `id`, `country_code`, `host`, `port`, `protocol` (`vless`), `network` (`tcp|ws|xhttp`), `public_key`, `sni`, `enabled`.

## Как работает генерация
- При запросе по токену сервис:
  1. Проверяет, что подписка и пользователь активны и не истекли.
  2. Берет все сервера с `enabled=true`.
  3. Для каждого сервера собирает VLESS URI вида  
     `vless://<UUID>@<host>:<port>?encryption=none&security=reality&pbk=<PUBLIC_KEY>&sni=<SNI>&fp=chrome&type=<network>#<COUNTRY>`.
- Никакие конфиги не хранятся на диске.

## Добавление серверов
1. Подключитесь к БД (например, `psql`).
2. Вставьте запись:
```sql
INSERT INTO servers (country_code, name, host, port, protocol, network, public_key, sni, enabled)
VALUES ('DE', 'Germany', 'de.example.com', 443, 'vless', 'tcp', '<PUBLIC_KEY>', 'de.example.com', true);
```
3. Клиенты увидят новый сервер после очередного обновления подписки.
4. Поле `created_at` заполняется автоматически (timezone aware). Если добавляете колонку в существующей БД — требуется миграция (TODO: alembic).

## Создание пользователя и подписки
1. Создайте пользователя:
```sql
INSERT INTO users (tg_id, uuid, is_active) VALUES (123456789, gen_random_uuid(), true) RETURNING id;
```
2. Создайте токен (можно использовать `app/services/token_generator.py`) и подпишите пользователя:
```sql
INSERT INTO subscriptions (user_id, token, expires_at, is_active)
VALUES (<USER_ID>, '<TOKEN>', NOW() + interval '30 days', true);
```
3. Ссылка для клиента: `${BASE_SUB_URL}/{TOKEN}`.

## Интеграция с Telegram-ботом
- Бот генерирует и показывает пользователю `BASE_SUB_URL/{token}`.
- Бот **не** строит конфиги — только выдает ссылку и управляет жизненным циклом подписки в БД.
- Для выпуска нового токена используйте `generate_subscription_token()` или аналогичную логику в боте.

## Эндпоинты мини-приложения (Telegram WebApp)
- `POST /api/auth/telegram` — принимает `{"initData": "<строка initData>"}`, проверяет подпись, создает пользователя при необходимости и возвращает роль (`admin`/`user`).
- `GET /api/me/subscription` — требует заголовок `X-Telegram-Init-Data` с `initData`, возвращает статус подписки и ссылку.
- Админские CRUD по серверам (требуют роль admin, определенную по `role` пользователя или `ADMIN_TG_IDS`):
  - `GET /api/admin/servers`
  - `POST /api/admin/servers`
  - `PUT/PATCH/DELETE /api/admin/servers/{id}`

TODO: добавить проверку срока действия `auth_date` из initData и полноценные миграции схемы.

## TODO / дальнейшее развитие
- Добавить миграции (alembic) и управление схемой.
- Добавить API для админ-панели (CRUD по серверам/пользователям).
- Расширить поддержку параметров (ws-path, alpn, flow и т.д.) через конфигурацию серверов.

## Архитектурные инварианты (важно)
- Бот: только создаёт/продлевает подписки и пользователей, не знает ничего о серверах и не генерирует конфиги.
- Mini App: только читает `/api/me/subscription` и отображает sub_url, бизнес-логики VPN нет.
- Backend: единственный источник истины, генерирует конфиги на лету, решает, активна ли подписка.
- Xray: ничего не знает о подписках, работает только с UUID/Reality ключами.

## Ограничения (что система НЕ делает)
- Нет биллинга и списаний — оформление подписки сейчас без платежей (TODO).
- Нет учёта трафика.
- Нет автоскейла/управления Xray.
- Нет мобильных приложений — только Telegram Mini App.

## Жизненный цикл подписки
- Подписка имеет `expires_at` и `is_active`. Если срок вышел или флаг `is_active=false`, выдача `/sub/{token}` возвращает 403.
- Фоновая задача раз в сутки деактивирует все истёкшие подписки.
- Пользователь с `is_active=false` в Mini App получает статус `no_subscription`.
- Серверы с `enabled=false` не попадают в подписку; если активных серверов нет, `/sub/{token}` вернет 403.

## Админка (Mini App, admin.html)
- Доступ только при `role=admin` (определяется через `/api/auth/telegram`).
- CRUD по серверам через `/api/admin/servers`.
- Поля сервера: `country_code`, `name`, `host`, `port`, `protocol`, `network`, `public_key`, `sni`, `enabled`, `created_at`.
- Изменения серверов применяются мгновенно: новые `enabled=true` появляются в подписке, `enabled=false` исчезают; если нет активных серверов, `/sub/{token}` отдаст 403.
