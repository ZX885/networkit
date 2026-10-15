# NetworkIt

Платформа-нетворкинг: профили, поиск людей, избранное, личные сообщения. Сначала Узбекистан.

- **backend/** — Django + Django REST Framework + PostgreSQL (приложения в `backend/apps`, настройки в `backend/config`).
- **frontend/** — React (JavaScript, JSX) + Vite.
- **networkit-backend/** — старый сайт на Supabase, только для чтения.
- **docs/** — анализ, ТЗ, архитектура, дизайн-система.

## Что нужно установить

Python 3.14, Pipenv, Node.js 20+, PostgreSQL 17.

## Backend

1. **База данных.** В PostgreSQL создайте пользователя (с правом `CREATEDB`: он нужен для тестов) и пустую базу. Имя базы чувствительно к регистру.
2. **Зависимости.** В корне проекта (рядом с `Pipfile`) создайте и активируйте виртуальное окружение, затем:
   ```bash
   pipenv install
   ```
   Если окружение `networkit/` уже создано и активировано, `pipenv` использует его.
3. **Файл `.env`.** Скопируйте шаблон и заполните значения (файл в git не попадает):
   ```bash
   cp backend/.env.example backend/.env
   ```
   Переменные: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL` (формат `postgres://пользователь:пароль@127.0.0.1:5432/база`), `SITE_URL`, а также `CSRF_TRUSTED_ORIGINS`, `NUM_PROXIES`, `DEFAULT_FROM_EMAIL` (на сервере ещё `EMAIL_*`). Описание — в `backend/.env.example`.
4. **Таблицы и кэш** (один раз для новой базы):
   ```bash
   cd backend
   python manage.py migrate
   python manage.py createcachetable
   ```
   `createcachetable` создаёт таблицу `django_cache`: в ней хранятся счётчики лимитов запросов (вход, регистрация). Без неё запросы к API вернут ошибку 500. Эту команду нужно выполнить и на боевом сервере.
5. **Запуск:**
   ```bash
   python manage.py runserver 8100
   ```
   Сервер: http://127.0.0.1:8100 (порт 8100 — по умолчанию для NetworkIt, чтобы не конфликтовать с другими проектами на 8000). Если `.env` отсутствует или PostgreSQL недоступен, команда остановится с объяснением.

Настройки: `config/settings/dev.py` (по умолчанию для `manage.py`) и `config/settings/prod.py` (по умолчанию для wsgi/asgi; в нём `DEBUG=False`, а `ALLOWED_HOSTS` и `SITE_URL` обязательны).

### Письма и подтверждение почты в dev

В dev письма не отправляются, а печатаются в консоль, где запущен `runserver` (в письме ссылка `…/verify-email/<токен>`). Ссылка дублируется в лог одной строкой с префиксом `DEMO link:` (в консольном письме длинные строки переносятся). На сервере письма идут через SMTP (`EMAIL_*` в `.env`).

Деплой демо-версии (Railway + Vercel): [docs/DEPLOY.md](docs/DEPLOY.md).

### API: ручная проверка регистрации и входа

Backend и frontend запущены; запросы идут через Vite-прокси (`http://localhost:5173/api/...`), как будет делать браузер. Пример для bash (в PowerShell используйте `curl.exe`):

```bash
BASE=http://localhost:5173
JAR=/tmp/nk-cookies.txt
H_JSON='Content-Type: application/json'
H_ORIGIN='Origin: http://localhost:5173'

# 1. Получить cookie csrftoken (и запомнить токен)
curl -s -c $JAR -H "$H_ORIGIN" $BASE/api/auth/csrf/ -o /dev/null -w "csrf: %{http_code}\n"
TOKEN=$(grep csrftoken $JAR | awk '{print $7}')

# 2. Регистрация (всегда 201; письмо печатается в консоль runserver)
curl -s -b $JAR -c $JAR -H "$H_JSON" -H "$H_ORIGIN" -H "X-CSRFToken: $TOKEN" $BASE/api/auth/register/ -d '{
  "email": "me@example.com", "password": "S3cure-pass-77", "username": "mycheck",
  "first_name": "Jane", "last_name": "Doe", "date_of_birth": "2000-05-20",
  "country": "UZ", "city": "Tashkent", "status": "student", "field": "computer_science",
  "accepted_terms": true }'

# 3. Скопировать токен из ссылки в письме (консоль runserver) и подтвердить почту
curl -s -b $JAR -c $JAR -H "$H_JSON" -H "$H_ORIGIN" -H "X-CSRFToken: $TOKEN" $BASE/api/auth/verify-email/ -d '{"token": "ВСТАВЬТЕ_ТОКЕН"}'

# 4. Вход (после входа Django меняет csrftoken — читаем новый)
curl -s -b $JAR -c $JAR -H "$H_JSON" -H "$H_ORIGIN" -H "X-CSRFToken: $TOKEN" $BASE/api/auth/login/ -d '{"email": "me@example.com", "password": "S3cure-pass-77"}'
TOKEN=$(grep csrftoken $JAR | awk '{print $7}')

# 5. Свой профиль и его изменение
curl -s -b $JAR $BASE/api/me/
curl -s -b $JAR -c $JAR -X PATCH -H "$H_JSON" -H "$H_ORIGIN" -H "X-CSRFToken: $TOKEN" $BASE/api/me/ -d '{"city": "Samarkand"}'

# 6. Выход
curl -s -b $JAR -c $JAR -X POST -H "$H_ORIGIN" -H "X-CSRFToken: $TOKEN" $BASE/api/auth/logout/ -w "logout: %{http_code}\n"
```

Что должно получиться: запросы без заголовка `X-CSRFToken` или с чужим `Origin` получают `403` и `{"error": {"code": "csrf_failed", …}}`; `/api/me/` без входа — `401`.

После проверки тестовый аккаунт можно удалить: `python manage.py shell -c "from apps.users.models import User; User.objects.filter(email='me@example.com').delete()"` (профиль удалится вместе с ним).

### Демо-профили для поиска (seed)

Для ручной проверки поиска и страницы профиля можно создать вымышленных пользователей:

```bash
cd backend
python manage.py seed_demo_profiles --count 20      # создаёт демо-профили (почта demo-N@example.invalid)
python manage.py seed_demo_profiles --delete        # удаляет только созданных этой командой
```

Пользователи подтверждены, пароль у них не задан (войти под ними нельзя): смотреть их можно под своим аккаунтом. У части скрыты город, вуз и участие в поиске, часть младше 18 лет (без контактов). Повторный запуск добавляет новых, нумерация продолжается.

**На сервере (Railway):** при `DEBUG=False` команда без флага не запускается. Запускайте её там только для демонстрации с флагом `--i-know-this-is-a-demo` (`python backend/manage.py seed_demo_profiles --count 20 --i-know-this-is-a-demo`), а после показа обязательно удалите демо-данные: `python backend/manage.py seed_demo_profiles --delete --i-know-this-is-a-demo`.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Сайт: http://localhost:5173. Запросы `/api/...` Vite передаёт на Django (`http://127.0.0.1:8100`; другой адрес — переменная `DEV_API_TARGET` в `frontend/.env.development`, пример в `frontend/.env.development.example`), поэтому backend должен быть запущен.

## Проверка

```bash
cd backend
python manage.py check          # конфигурация и подключение к БД
python manage.py test           # тесты (создаётся временная база test_<имя>)
curl http://127.0.0.1:8100/api/health/       # {"status": "ok"}  (при запущенном runserver)
curl http://localhost:5173/api/health/       # то же через прокси Vite (при запущенных обоих серверах)
```

Для frontend: `npm run lint`, `npm run build`, `npm run format -- --check`.
