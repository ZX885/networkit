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
   Переменные: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL` (формат `postgres://пользователь:пароль@127.0.0.1:5432/база`), `SITE_URL`. Описание — в `backend/.env.example`.
4. **Запуск:**
   ```bash
   cd backend
   python manage.py runserver
   ```
   Сервер: http://127.0.0.1:8000. Если `.env` отсутствует или PostgreSQL недоступен, команда остановится с объяснением.

Настройки: `config/settings/dev.py` (по умолчанию для `manage.py`) и `config/settings/prod.py` (по умолчанию для wsgi/asgi; в нём `DEBUG=False`, а `ALLOWED_HOSTS` и `SITE_URL` обязательны).

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Сайт: http://localhost:5173. Запросы `/api/...` Vite передаёт на Django (`http://127.0.0.1:8000`), поэтому backend должен быть запущен.

## Проверка

```bash
cd backend
python manage.py check          # конфигурация и подключение к БД
python manage.py test           # тесты (создаётся временная база test_<имя>)
curl http://127.0.0.1:8000/api/health/       # {"status": "ok"}  (при запущенном runserver)
curl http://localhost:5173/api/health/       # то же через прокси Vite (при запущенных обоих серверах)
```

Для frontend: `npm run lint`, `npm run build`, `npm run format -- --check`.
