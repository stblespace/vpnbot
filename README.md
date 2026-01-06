# VPN SaaS (VLESS + Xray + Telegram Mini App)

Каноничный гайд и конфиги для продакшен-сборки сервиса на домене `stabelspace.ru` с двумя серверами:
- **Backend-сервер**: FastAPI, PostgreSQL, Telegram Mini App (static), Nginx, HTTPS, Docker Compose.
- **VPN-сервер**: Xray с VLESS + Reality. Никакого Nginx/HTTPS — только Xray.

## Архитектура и инварианты
- Бот: создаёт пользователя и подписку, продлевает/отменяет, **не** знает о серверах и **не** строит конфиги.
- Mini App: клиент показывает статус подписки, админка делает CRUD серверов, VPN-логики внутри нет.
- Backend: единственный источник истины, хранит пользователей/подписки/серверы и собирает VLESS-ссылки на лету.
- Xray: принимает любой UUID, не знает о подписках, работает только на Reality параметрах.
- Разделение по серверам: `stabelspace.ru` (Nginx+FastAPI+static) и отдельный хост с Xray без прокси.

## Готовые конфиги
- Xray Reality: `docs/canonical/xray-config.json` — слушает 443/tcp, принимает любой UUID, Reality shortId/SNI из БД.
- Nginx фронта: `docs/canonical/nginx/nginx.conf` — `/app` → static, `/api` и `/sub` → FastAPI, отключён кэш HTML/JS/CSS, HTTPS + редирект с HTTP.
- Docker Compose для backend-сервера: `docs/canonical/docker-compose.yml` — Postgres + FastAPI + Nginx, static монтируется volume, без копирования в образ.
- Для совместного доступа бота и backend к одной БД сервисы `db` и `backend` подключены к внешней сети `backend_default` (создаётся один раз: `docker network create backend_default`).

## База данных (ядро)
- `users`: `id`, `tg_id`, `uuid`, `is_active`, `role`.
- `subscriptions`: `id`, `user_id`, `token` (уникален), `expires_at`, `is_active`.
- `servers`: `id`, `country_code`, `name`, `host`, `port`, `protocol` (`vless`), `network` (`tcp|ws|xhttp`), `public_key`, `sni`, `short_id`, `enabled`, `created_at`.
- Все связи один-ко-многим: `users -> subscriptions`, `servers` автономны.

## Каноничная логика backend
1. `GET /sub/{token}`:
   - Проверка подписки: токен существует, `is_active=true`, `expires_at > now`, пользователь `is_active=true`; иначе `403`.
   - Берутся только `servers.enabled=true`; если ни одного — `403`.
   - Для каждого сервера строится VLESS URI:  
     `vless://<user.uuid>@<server.host>:<server.port>?encryption=none&security=reality&fp=chrome&pbk=<server.public_key>&sni=<server.sni>&sid=<server.short_id>&type=<server.network>#<server.country_code>`.
2. `/api` Mini App:
   - Авторизация только по подписи Telegram (header `X-Telegram-Init-Data`).
   - Роль `admin` даётся по `users.role='admin'` или попаданию в `ADMIN_TG_IDS`.
   - Админские CRUD по `servers`, пользовательское чтение `/api/me/subscription`.
3. Строгие проверки:
   - Подписка истекла → `403`.
   - `enabled=false` серверы не участвуют.
   - Нет активных серверов → `403`.

## Telegram Mini App (webapp/)
- Каноничная структура:
  - `webapp/client/` — пользовательская страница (статус, ссылка на подписку).
  - `webapp/admin/` — админка CRUD серверов.
  - `webapp/shared/` — общий JS (API-клиент, проверки подписи).
  - `webapp/assets/` — статика.
- Cache-busting:
  - Имя файлов с хешем/версией (`app.20240301.js`) или query (`app.js?v=$(date +%s)`), ссылки в HTML обновляются при каждом релизе.
  - Nginx отдаёт `Cache-Control: no-store` для HTML/JS/CSS (см. `docs/canonical/nginx/nginx.conf`).
  - Mini App всегда загружается из `https://stabelspace.ru/app/...`; любые изменения в каталоге webapp применяются мгновенно благодаря volume.

## Xray (VPN-сервер, без Nginx)
1. Сгенерировать ключи Reality:
   ```bash
   xray x25519
   # => Private key: <privateKey>
   # => Public key:  <publicKey>  # сохранить в servers.public_key
   ```
2. Выбрать SNI/дестинацию: домен с реальным TLS-сертификатом (часто `www.cloudflare.com` или ваш внешний домен), он идёт в `realitySettings.serverNames[]`, `realitySettings.dest` и в поле `servers.sni`.
3. Сгенерировать `shortId`: 8–16 hex-символов, например `openssl rand -hex 4` → писать в `servers.short_id` и в `shortIds[]`.
4. Заполнить `docs/canonical/xray-config.json`:
   - `clients: []` — Xray принимает любой UUID; авторизация/лимиты делаются на backend через выдачу подписок.
   - `privateKey` — на VPN-сервере; `publicKey` → в БД (pbk в ссылках).
   - `dest` и `serverNames` должны совпадать с SNI.
5. Запустить Xray (systemd или `docker run`) только с этим конфигом на 443/tcp. Никаких доп. прокси и TLS-терминации.

## Backend-сервер (Docker + Compose + Nginx)
1. Предварительно: A-запись `stabelspace.ru` → backend-сервер; открыт 80/443.
2. TLS: выпуск/обновление Let's Encrypt webroot в `/etc/letsencrypt` с `--webroot-path=/var/www/letsencrypt` (смонтировано в Nginx).
3. Подготовить `backend/.env` (пример):
   ```
   DATABASE_URL=postgresql+asyncpg://vpn_user:vpn_pass@db:5432/vpn_subscriptions
   BASE_SUB_URL=https://stabelspace.ru/sub
   WEBAPP_URL=https://stabelspace.ru/app
   BOT_TOKEN=<telegram_bot_token>
   ADMIN_TG_IDS=1366106514
   LOG_LEVEL=INFO
   ```
4. Запуск/перезапуск из корня репозитория:
   ```bash
   docker compose -f docs/canonical/docker-compose.yml up -d --build   # первый запуск/обновление кода
   docker compose -f docs/canonical/docker-compose.yml restart backend # плавный рестарт backend
   docker compose -f docs/canonical/docker-compose.yml restart nginx   # после обновления конфигов Nginx/сертов
   docker compose -f docs/canonical/docker-compose.yml logs -f backend # просмотр логов
   ```
5. Почему volume для webapp: `../../backend/webapp` монтируется в `/usr/share/nginx/html/app` (см. compose), поэтому любые изменения статики видны сразу без rebuild образов.
6. Если используется bot из корневого `docker-compose.yml`, убедитесь что сеть `backend_default` создана (`docker network create backend_default`), чтобы bot и backend делили одну БД.

## Деплой по шагам
1) **Backend-сервер**  
   - Клонировать репозиторий, заполнить `backend/.env`.  
   - Получить/обновить сертификаты Let's Encrypt (webroot `/var/www/letsencrypt`, certs `/etc/letsencrypt`).  
   - `docker compose -f docs/canonical/docker-compose.yml up -d --build`.  
   - Проверка: `curl -I https://stabelspace.ru/healthz` (200), `/api/docs` доступно, `/app` отдаёт статику без кэша.

2) **VPN-сервер**  
   - Установить Xray, сгенерировать Reality ключи и shortId, выбрать SNI.  
   - Прописать значения в `docs/canonical/xray-config.json`, скопировать на сервер, запустить Xray на 443.  
   - Добавить запись сервера в БД через админку Mini App (`public_key`, `sni`, `short_id`, `host`, `port`, `network`, `country_code`, `enabled=true`). Xray не перезапускается при смене UUID — он принимает любые.

## Рабочие сценарии
- **Добавить сервер (админка Mini App)**: открыть `https://stabelspace.ru/app/admin/`, создать запись с полями из схемы БД. `enabled=false` исключает сервер из выдачи.
- **Выдать подписку пользователю**: бот создаёт `users` (uuid) и `subscriptions` (token, expires_at); ссылка для пользователя — `${BASE_SUB_URL}/{token}`.
- **Пользователь подключается**: в Telegram получает ссылку, импортирует в клиент (v2rayN, Shadowrocket, Nekoray, Clash и т.д.), клиент опрашивает `/sub/{token}`, backend отдаёт список VLESS URI с Reality параметрами.

## Обновление фронта без rebuild
- Обновить файлы в `backend/webapp` (rsync/git pull).
- Обновить версии файлов в HTML (`app.js?v=...` или новые имена файлов).
- `docker compose -f docs/canonical/docker-compose.yml restart nginx` — подхватит статику и конфиг.

## Неподдерживаемые фичи (задано архитектурой)
- Биллинг и автоматические списания.
- Учёт/квотирование трафика.
- Авто-масштабирование Xray и управление инстансами.
- Автогенерация клиентов/конфигов ботом — только подписки.

## Почему так
- Разделение ролей упрощает безопасность: Xray не хранит и не проверяет подписки, backend контролирует доступ по токену.
- `clients=[]` в Xray позволяет не перезапускать его при создании новых UUID; безопасность держится на Reality + секретности токенов.
- Webroot+volume для Mini App гарантирует отсутствие кэша и мгновенное применение правок.
- Nginx управляет TLS и маршрутизацией на одном сервере, VPN-сервер остаётся чистым и устойчивым к лишним зависимостям.
