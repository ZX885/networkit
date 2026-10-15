# Деплой демо-версии: Railway (backend) + Vercel (frontend)

Демо только с **тестовыми данными**. Схема:

```
браузер → https://networkit-wine.vercel.app            (Vercel: сайт, frontend/)
        → /api/...  Vercel проксирует (rewrite) →  https://<сервис>.up.railway.app/api/...
                                                      (Railway: Django + gunicorn)
                                                      → PostgreSQL (Railway, внутренний адрес)
```

Админка Django **не** проксируется через Vercel: она открывается на домене Railway.

Файлы в репозитории: `railway.json` (сборка и запуск), `frontend/vercel.json` (rewrite), `backend/config/settings/prod.py` (боевые настройки), `backend/.env.example` (список переменных).

## 0. Перед началом

- [ ] Код, который нужно задеплоить, лежит в ветке на GitHub (сейчас работа идёт в `step-b3a-auth-api`: её нужно закоммитить, запушить и, как правило, влить в `main`). Railway деплоит ту ветку, которую вы выберете.
- [ ] Репозиторий **приватный** (Settings → General → Danger Zone → Change visibility). В репозиторий не попадают `.env` и секреты (проверьте `git status`).
- [ ] Данные только тестовые. Реальных людей, их почт и паролей в демо быть не должно.

## 1. Railway: проект и база

1. railway.com → **New Project** → **Deploy PostgreSQL**. Появится сервис базы (по умолчанию называется `Postgres`).
2. В проекте: **+ New** → **GitHub Repo** → выберите репозиторий `ZX885/networkit`.
   - Права: при первом подключении Railway просит установить GitHub App. Выдайте доступ **только этому репозиторию** (Only select repositories), а не всем.
   - Ветка: **Settings → Source → Branch** — ветка, из которой деплоите (обычно `main`).
   - **Root directory не нужен**: `Pipfile` и `railway.json` лежат в корне репозитория. Не задавайте `backend` — тогда Railway не найдёт `Pipfile`.
3. Сборщик — Railpack (по умолчанию). Dockerfile не нужен. Параметры сборки и запуска берутся из `railway.json` (см. раздел 8, если нужно ввести их руками).

Первый деплой упадёт или не пройдёт healthcheck, пока не заданы переменные: это нормально. Задайте их (раздел 2) и сделайте Redeploy.

## 2. Переменные окружения сервиса Django

Сервис Django → **Variables**. Значения секретов не коммитьте и не вставляйте в чаты.

| Переменная | Значение | Зачем |
|---|---|---|
| `SECRET_KEY` | **новый** ключ, не из вашего локального `.env` | подпись сессий и токенов. Сгенерировать: `python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"` |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (ссылка на переменную сервиса базы; если база названа иначе, подставьте её имя) | **внутренний** адрес (`…postgres.railway.internal`). **Не** `DATABASE_PUBLIC_URL`: публичный адрес базы не используем и нигде не публикуем |
| `DJANGO_SETTINGS_MODULE` | `config.settings.prod` | `manage.py` по умолчанию берёт dev-настройки; в консоли Railway без этой переменной команды пойдут с dev |
| `ALLOWED_HOSTS` | `<сервис>.up.railway.app,healthcheck.railway.app` | домен сервиса (см. раздел 3) **и** `healthcheck.railway.app`, иначе проверка здоровья получит 400 |
| `SITE_URL` | `https://networkit-wine.vercel.app` | адрес сайта: **https, без слэша в конце**. Из него строятся ссылки в письмах |
| `CSRF_TRUSTED_ORIGINS` | можно не задавать | по умолчанию равен `SITE_URL`. Если задаёте — тоже без слэша в конце, через запятую |
| `NUM_PROXIES` | `2` (по умолчанию) | сколько прокси перед Django: Vercel + Railway. См. раздел 6 |
| `DEMO_LOG_VERIFY_LINKS` | `True` | только для демо без SMTP, см. раздел 5. Иначе не задавайте |
| `ADMIN_URL` | например `staff-k8f3x/` | путь админки. По умолчанию `admin/`; на любом доступном из интернета сайте лучше сменить |
| `HSTS_SECONDS` | `0` (по умолчанию) | HSTS выключен. Включайте (например `31536000`) только когда уверены, что HTTPS работает везде |
| `EMAIL_HOST` и др. | не задавайте для демо | настоящий SMTP; без него prod стартует только при `DEMO_LOG_VERIFY_LINKS=True` |

Что намеренно **не** включено: `SECURE_SSL_REDIRECT` (за прокси он ломает проверки здоровья). HTTPS обеспечивают Vercel и Railway.

## 3. Домен Railway и подстановка в `vercel.json`

1. Сервис Django → **Settings → Networking → Generate Domain**. Получится адрес вида `networkit-production-xxxx.up.railway.app`.
2. Добавьте этот домен (без `https://`) в `ALLOWED_HOSTS` (раздел 2) и сделайте Redeploy.
3. В `frontend/vercel.json` замените `REPLACE_WITH_RAILWAY_DOMAIN` на этот домен **без** `https://` и без слэша:
   `"destination": "https://networkit-production-xxxx.up.railway.app/api/:path*"`
4. Закоммитьте и запушьте. Vercel задеплоит frontend заново (Root Directory в Vercel — `frontend`, как сейчас).
5. Порядок правил в `vercel.json` важен: сначала `/api/...` на Railway, потом всё остальное (кроме `/api/`) на `/index.html`. Благодаря второму правилу прямое открытие `/me`, `/verify-email/<токен>` и обновление страницы не дают 404. Статические файлы (`/assets/...`) Vercel отдаёт раньше rewrite. Не включайте в Vercel `trailingSlash: false` / «Remove trailing slash»: адреса Django заканчиваются слэшем.

## 4. Суперпользователь (один раз)

Нужен для входа в админку. Команду выполняют **внутри сервиса** (через `railway run` она пойдёт с вашего компьютера, а внутренний адрес базы оттуда недоступен).

1. Установите Railway CLI (документация: docs.railway.com/cli), затем `railway login` и `railway link` (выберите проект и сервис Django).
2. `railway ssh` — откроется оболочка внутри контейнера сервиса.
3. В ней:
   ```bash
   python backend/manage.py createsuperuser
   ```
   Введите email и пароль (не используйте пароли от других сайтов). Если `railway ssh` недоступен на вашем тарифе или в версии CLI, выполните ту же команду другим способом из документации Railway (например, одноразовый сервис с командой запуска). Если что-то не получилось — напишите, разберём по ошибке.
4. Админка откроется по адресу `https://<сервис>.up.railway.app/<ADMIN_URL>` (по умолчанию `/admin/`).

## 5. Письма без SMTP: демо-режим

SMTP не настроен, поэтому при `DEMO_LOG_VERIFY_LINKS=True` письма печатаются в лог сервера, а ссылка подтверждения дополнительно пишется **одной строкой** с префиксом `DEMO link:`.

- Где смотреть: сервис Django → **Deployments** → последний деплой → **Deploy Logs** → поиск `DEMO link`.
- Скопируйте ссылку целиком и откройте её в браузере (она ведёт на `SITE_URL`, то есть на Vercel).
- **Альтернатива без ссылки**: подтвердить тестовый аккаунт командой (в `railway ssh`):
  ```bash
  python backend/manage.py verify_user test@example.com
  ```
  Команда ставит дату подтверждения почты; повторный запуск безопасен.

> ⚠️ **`DEMO_LOG_VERIFY_LINKS` нельзя включать на боевом сайте.** Ссылка подтверждения в логе — это доступ к аккаунту человека, а логи видят все, у кого есть доступ к проекту Railway. Для настоящих пользователей настройте SMTP (`EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`) и уберите эту переменную.

## 6. NUM_PROXIES: как проверить значение вручную

От `NUM_PROXIES` зависит, какой IP считается адресом клиента (по нему работают лимиты попыток входа). Перед Django стоят две прокси (Vercel и Railway), поэтому по умолчанию `2`. Проверка с двух **разных сетей** (например, компьютер на домашнем Wi-Fi и телефон на мобильном интернете):

1. С компьютера сделайте подряд 6 неверных входов (лимит входа — 5 в минуту). Анонимные POST требуют CSRF, поэтому сначала берём токен:
   ```bash
   SITE=https://networkit-wine.vercel.app
   JAR=$(mktemp)
   curl -s -c "$JAR" -o /dev/null "$SITE/api/auth/csrf/"
   TOKEN=$(grep csrftoken "$JAR" | awk '{print $NF}')
   for i in 1 2 3 4 5 6; do
     curl -s -o /dev/null -w "%{http_code}\n" -b "$JAR" -X POST "$SITE/api/auth/login/" \
       -H "Content-Type: application/json" -H "Origin: $SITE" -H "X-CSRFToken: $TOKEN" \
       -d '{"email":"nobody@example.com","password":"wrong-password"}'
   done
   ```
   Ожидаем: пять ответов `401` (неверные данные) и шестой `429`. Если везде `403` — проверьте `CSRF_TRUSTED_ORIGINS` / `SITE_URL`.
2. **Сразу** с телефона (другая сеть) сделайте один неверный вход через форму. Ожидаем **не 429**, а обычную ошибку «неверный email или пароль».
3. Как читать результат:
   - у телефона тоже `429` → `NUM_PROXIES` слишком мало: все пользователи выглядят как один IP (адрес прокси). Увеличьте на 1;
   - на компьютере `429` так и не наступил за 10+ попыток → слишком много: клиент может подставить свой заголовок `X-Forwarded-For` и обходить лимит. Уменьшите на 1;
   - 429 только у того, кто делает попытки → значение верное.

## 7. Чеклист после деплоя

- [ ] **Health**: `https://<сервис>.up.railway.app/api/health/` отвечает `{"status": "ok"}`.
- [ ] **Обязательно: регистрация и вход через домен Vercel** (`https://networkit-wine.vercel.app`, **не** через домен Railway). Так проверяются CSRF и cookie через rewrite. В DevTools → Network: запросы `/api/...` идут на домен Vercel, нет `403 csrf_failed`, в ответах приходят cookie `csrftoken` и `sessionid` с флагом Secure, после перезагрузки страницы вход сохраняется.
- [ ] Подтверждение почты (ссылка из лога или `verify_user`, раздел 5): экран «Email confirmed»; повторное открытие той же ссылки показывает «invalid».
- [ ] Вход после подтверждения → `/discover`, выход.
- [ ] Прямое открытие и обновление страниц `/me`, `/discover`, `/verify-email/…` не даёт 404.
- [ ] `/<ADMIN_URL>` на домене Railway: вход суперпользователем, оформление (CSS) на месте.
- [ ] Лимиты: проверка из раздела 6.
- [ ] **Загрузка файлов через rewrite Vercel (отложено на шаг B4).** Когда появится загрузка аватара (до 5 МБ), нужно проверить, что запрос такого размера проходит через rewrite Vercel к Railway (у Vercel есть собственные ограничения на размер запроса, и для внешних rewrite я их не проверял). Если не проходит — решение выбираем в B4 (например, прямой адрес API для загрузки или иное хранилище).

## 8. Если сборка или деплой упали

**Где смотреть логи**: сервис Django → **Deployments** → нужный деплой → **Build Logs** (установка зависимостей, `collectstatic`) и **Deploy Logs** (pre-deploy `migrate`, запуск gunicorn, healthcheck). Ошибки запросов — вкладка **HTTP Logs**.

Три самых вероятных причины:

1. **Версия Python.** `Pipfile` требует 3.14, а Railpack официально поддерживает не все версии и ставит Python готовым бинарником. Признак: в Build Logs ошибка установки Python (mise / «no precompiled python»). Что делать: задать переменную `RAILPACK_PYTHON_VERSION=3.13`; если `pipenv` ругается на несовпадение с `python_version` в `Pipfile`, нужно сменить `[requires]` на `3.13` (и обновить `Pipfile.lock`). Это изменение делается только по вашей команде; на ваш локальный Python оно не влияет.
2. **ALLOWED_HOSTS.** Признак: healthcheck «failed with service unavailable» / `400`, в логах `DisallowedHost`. Проверьте, что в `ALLOWED_HOSTS` есть и домен сервиса, и `healthcheck.railway.app`, без пробелов и без `https://`.
3. **Healthcheck и запуск приложения.** Признак: «Healthcheck failed» после успешной сборки. В Deploy Logs ищите исключение при старте: `DEBUG=True` в окружении, `SITE_URL` не начинается с `https://`, нет `SECRET_KEY` / `DATABASE_URL`, нет ни `EMAIL_HOST`, ни `DEMO_LOG_VERIFY_LINKS=True`, не прошёл `migrate` (база недоступна — проверьте, что `DATABASE_URL` ссылается на внутренний адрес). Проверка идёт на `/api/health/` в течение 60 секунд (`healthcheckTimeout`).

Отдельно: если `collectstatic` падает в сборке с «не задана переменная окружения», значит переменные сервиса не заданы (боевые настройки читаются и при сборке).

## 9. Откат

Сервис Django → **Deployments** → выберите предыдущий успешный деплой → меню **⋮** → **Rollback** (или **Redeploy**). Откат откатывает код, но **не миграции базы**: если новый деплой применил миграцию, перед откатом убедитесь, что старый код с ней совместим. Для frontend: Vercel → Deployments → нужный деплой → **Promote to Production**.

## 10. Настройки Railway вручную (запасной вариант)

> ⚠️ **Проверить до 2026-12-01.** `railway.json` (Config as Code) в документации Railway помечен устаревшим: файлы старого формата работают до 2026-12-01, дальше Railway рекомендует свой Infrastructure as Code. До этой даты проверьте, что деплой всё ещё подхватывает `railway.json`, либо перенесите значения ниже в настройки сервиса (Settings → Build / Deploy).

| Поле | Значение |
|---|---|
| Builder | Railpack |
| Build Command | `python backend/manage.py collectstatic --noinput --settings=config.settings.prod` |
| Pre-deploy Command | `python backend/manage.py migrate --noinput --settings=config.settings.prod && python backend/manage.py createcachetable --settings=config.settings.prod` |
| Start Command | `gunicorn config.wsgi:application --chdir backend --workers 2 --bind 0.0.0.0:$PORT --timeout 30` |
| Healthcheck Path | `/api/health/` (таймаут 60 с) |
| Restart Policy | On Failure, 3 попытки |

## 11. Предупреждения

- **Только тестовые данные.** Не вносите реальные данные людей.
- **Не публикуйте публичный адрес базы** (`DATABASE_PUBLIC_URL`, TCP Proxy) и не вставляйте его в чаты и репозиторий. Приложению нужен только внутренний адрес.
- **Репозиторий приватный**, секреты (`SECRET_KEY`, пароли) живут только в Variables Railway.
- **`DEMO_LOG_VERIFY_LINKS` — только демо** (раздел 5).
- Gunicorn не запускается на Windows: локально проверяйте `python manage.py check`, `check --deploy` и `collectstatic`, а запуск — на Railway.
- Разработка локально не меняется: `manage.py` по-прежнему использует dev-настройки и ваш `backend/.env`. Локальный запуск backend: `python manage.py runserver 8100` (frontend проксирует `/api` на `http://127.0.0.1:8100`, адрес можно сменить через `DEV_API_TARGET`, см. `frontend/.env.development.example`).

### Про `check --deploy`

Команда с боевыми настройками (значения через окружение, `SKIP_DOTENV=1`) оставляет два предупреждения, и это сознательно:

- `security.W004` (нет HSTS): `HSTS_SECONDS=0` по умолчанию. Включите, когда убедитесь, что сайт работает по HTTPS без проблем.
- `security.W008` (нет `SECURE_SSL_REDIRECT`): редирект выключен намеренно, он ломает healthcheck за прокси; HTTPS-доступ обеспечивают Vercel и Railway.
