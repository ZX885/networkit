# NetworkIt — архитектура

Связанные документы: `CLAUDE.md` (правила проекта), `docs/ANALYSIS.md` (разбор legacy), `docs/SPEC.md` (модели, API, права), `docs/DESIGN_SYSTEM.md` (UI). Фрагменты кода ниже — **эскизы для обсуждения**, в проект они не добавлялись.

## 1. Принципы (из CLAUDE.md, уточнённые решениями заказчика)

1. Стек не меняем: Django + DRF + PostgreSQL; React на чистом JS/JSX (функциональные компоненты и hooks), Vite. Библиотеки — только из списка в §10.
2. Права и приватность — **на сервере** (permissions, queryset-ы, сериализаторы). Фронтенд только отображает то, что отдал сервер.
3. Пользовательский текст никогда не вставляется как HTML (`dangerouslySetInnerHTML` запрещён).
4. Секреты только в `.env`, не коммитятся.
5. Код простой: тонкие views, логика в `services.py`/`selectors.py`, короткие комментарии, имена в коде на английском.
6. Работа малыми шагами (этапы 1–13 из SPEC §8), каждый — отдельная ветка и PR.

## 2. Общая схема

```
DEV
 Браузер ──► Vite dev server :5173 ──(proxy /api, /media)──► Django runserver :8000 ──► PostgreSQL :5432
            (React, HMR)                                      (/admin/ открывается напрямую на :8000)
            письма: консоль Django

PROD (один домен, один VPS)
 Браузер ──HTTPS──► Nginx
                     ├─ /            → frontend/dist (статические файлы, SPA-fallback на index.html)
                     ├─ /api/, /admin/ → Gunicorn (unix-socket) → Django ──► PostgreSQL
                     ├─ /static/     → whitenoise внутри Django (CSS админки), кэш
                     └─ /media/      → MEDIA_ROOT на диске (аватары), напрямую Nginx-ом
```
Один домен = нет CORS, cookie `sessionid`/`csrftoken` first-party, `django-cors-headers` не нужен.

В dev Vite-прокси по умолчанию (`changeOrigin: false`) передаёт `Host: localhost:5173` и `Origin: http://localhost:5173` — они совпадают, и проверка Origin в Django CSRF проходит; на всякий случай `CSRF_TRUSTED_ORIGINS` включает `http://localhost:5173`. Проверить на этапе 5a [нужна проверка в рантайме].

## 3. Backend: структура папок

Имя пакета проекта `backend/backend/` уже существует — не переименовываем (CLAUDE.md). Новых Django-приложений кроме `users`, `profiles`, `messaging` не создаём; общий код — в подпакете `backend/backend/api/`.

```
backend/
├─ manage.py
├─ .env.example                  # шаблон переменных (без секретов), коммитится
├─ backend/                      # пакет проекта
│  ├─ settings.py                # единый файл; значения из окружения через django-environ
│  ├─ urls.py                    # /admin/, /api/ (include), /media/ в dev
│  ├─ wsgi.py, asgi.py
│  └─ api/                       # общее для всех приложений (НЕ Django-app)
│     ├─ urls.py                 # собирает users/profiles/messaging urls под /api/
│     ├─ exceptions.py           # exception_handler → единый формат ошибок (SPEC §3.0)
│     ├─ pagination.py           # PageNumber (12/24) и курсор для сообщений
│     ├─ permissions.py          # IsNotBanned, IsOwner
│     └─ throttles.py            # scoped-throttle классы
├─ users/                        # учётная запись и аутентификация
│  ├─ models.py, managers.py     # User (вход по email)
│  ├─ serializers.py, views.py, urls.py
│  ├─ services.py                # регистрация (User+Profile в транзакции), вход, смена email/пароля, удаление
│  ├─ tokens.py                  # подписанные токены (django.core.signing) для verify/email-change
│  ├─ emails.py + templates/users/email/*.txt   # тексты писем
│  ├─ admin.py                   # бан/разбан
│  ├─ management/commands/purge_unverified.py
│  └─ tests/
├─ profiles/                     # профиль, приватность, поиск, избранное, блокировки, жалобы
│  ├─ models.py                  # Profile, SavedProfile, Block, Report
│  ├─ choices.py                 # справочники (страны, направления, интересы…) — единственный источник
│  ├─ validators.py              # username, имена, возраст, контакты
│  ├─ serializers/               # own.py, public.py, card.py, write.py, mini.py — по одному представлению
│  ├─ selectors.py               # visible_profiles_for(user): ЕДИНОЕ место правил «бан/блок/не подтверждён/не в поиске»
│  ├─ filters.py                 # django-filter FilterSet для поиска (с учётом приватности)
│  ├─ avatar.py                  # проверка и обработка изображения (Pillow)
│  ├─ views.py, urls.py, admin.py
│  └─ tests/
├─ messaging/                    # диалоги и сообщения
│  ├─ models.py                  # Conversation, Message
│  ├─ services.py                # конечный автомат статусов: create_request, accept, decline, send_message
│  ├─ serializers.py, views.py, urls.py
│  └─ tests/
├─ media/                        # загруженные файлы (в .gitignore)
└─ staticfiles/                  # collectstatic (в .gitignore)
```
Зависимости между приложениями — только в одну сторону: `messaging → profiles → users`. Циклов нет (правила блокировки живут в `profiles.selectors`, их используют и поиск, и сообщения).

Назначение слоёв:
| Слой | Что делает | Чего не делает |
|---|---|---|
| `models.py` | поля, constraints, индексы, простые свойства (`age`, `is_minor`) | бизнес-сценарии |
| `serializers/` | **что именно уходит наружу и что принимается**; приватность реализована здесь | запросы к БД сверх `to_representation` |
| `selectors.py` | queryset-ы «кого пользователь вправе видеть» | запись |
| `services.py` | сценарии с несколькими шагами/транзакциями | HTTP |
| `views.py` | тонкий адаптер: permission → selector/service → serializer | логика правил |
| `tests/` | тесты рядом с приложением | — |

## 4. Frontend: структура папок

Текущий каркас: Vite 8 + React 19, `src/App.jsx`, `main.jsx`, `index.css`, демо-ассеты (удалим на этапе 5a).

```
frontend/
├─ index.html                    # <div id="root">, подключает /theme-init.js (синхронно, до CSS)
├─ vite.config.js                # plugin-react + proxy: /api, /media → http://127.0.0.1:8000
├─ .prettierrc                   # настройки Prettier
├─ public/
│  ├─ theme-init.js              # до отрисовки выставляет data-theme (нет «вспышки» тёмной/светлой темы; внешний файл → CSP без inline-скриптов)
│  └─ favicon.svg
└─ src/
   ├─ main.jsx                   # createRoot, импорт шрифтов (@fontsource) и стилей
   ├─ App.jsx                    # провайдеры (Theme → Toast → Auth → Meta) + роутер
   ├─ routes.jsx                 # таблица маршрутов, ProtectedRoute, GuestRoute
   ├─ api/                       # ВСЕ запросы к серверу
   │  ├─ apiClient.js            # fetch-обёртка, CSRF, ApiError
   │  ├─ auth.js, profiles.js, saved.js, messages.js, moderation.js (blocks/reports), meta.js
   ├─ context/                   # глобальное состояние
   │  ├─ AuthContext.jsx, ThemeContext.jsx, ToastContext.jsx, MetaContext.jsx
   ├─ hooks/                     # useApi.js, useDebounce.js, usePolling.js, useMediaQuery.js, useDocumentTitle.js
   ├─ texts/                     # ВСЕ тексты интерфейса (подготовка к i18n)
   │  ├─ en.js                   # объект { 'auth.login.title': 'Welcome back', … }
   │  ├─ errors.js               # код ошибки API → ключ текста
   │  └─ index.js                # функция t(key, vars)
   ├─ styles/
   │  ├─ tokens.css              # переменные (светлая и тёмная тема) — DESIGN_SYSTEM
   │  ├─ base.css                # reset, типографика, фокус, reduced-motion
   │  └─ utilities.css           # .visually-hidden, .container и т.п.
   ├─ components/
   │  ├─ ui/                     # базовые элементы без знания о предметной области (Button, Field, Modal…)
   │  ├─ layout/                 # AppLayout, Sidebar, TopNav, PageHeader, Footer
   │  ├─ profile/                # ProfileCard, ProfileView, ProfileForm-секции, PrivacyToggles, AvatarUploader
   │  └─ messaging/              # ConversationList, ChatWindow, MessageBubble, MessageComposer, RequestBanner
   ├─ pages/
   │  ├─ public/                 # LandingPage, NotFoundPage
   │  ├─ auth/                   # LoginPage, RegisterPage (+ steps/), VerifyEmailPage, ForgotPasswordPage, ResetPasswordPage, ConfirmEmailChangePage
   │  ├─ discover/               # DiscoverPage
   │  ├─ profile/                # ProfilePage (/u/:username), MyProfilePage, EditProfilePage
   │  ├─ messages/               # MessagesPage
   │  ├─ saved/                  # SavedPage
   │  └─ settings/               # SettingsPage (+ вкладки Account/Privacy/Security/Blocked/Danger)
   └─ utils/                     # format.js (даты), clientValidators.js (подсказки; истина — на сервере), constants.js (брейкпоинты, интервалы опроса)
```
Правила слоёв фронтенда:
- `components/ui/*` ничего не знает о API и профилях; принимает данные через props.
- `components/profile|messaging/*` — предметные компоненты, **не вызывают `fetch`**; действия приходят колбэками.
- `pages/*` — «контейнеры»: вызывают функции из `api/`, держат состояние экрана, собирают компоненты.
- Импорты только «вниз»: `pages → components → ui/utils/texts`; `api` не импортирует компоненты.

## 5. Соглашения об именах

### Backend (Python/Django)
| Что | Правило | Пример |
|---|---|---|
| Файлы, функции, переменные | `snake_case` | `visible_profiles_for` |
| Классы | `PascalCase`, модели в единственном числе | `Conversation` |
| Сериализаторы | `<Model><View>Serializer` | `ProfilePublicSerializer`, `ProfileOwnSerializer`, `ProfileCardSerializer` |
| Permissions | `Is…` | `IsNotBanned` |
| Коды справочников и ошибок | `snake_case` латиницей | `computer_science`, `request_pending` |
| URL | `kebab-case`, множественное число для коллекций | `/api/conversations/`, `/api/auth/password-reset/` |
| Имена URL (`name=`) | `app-resource-action` | `messaging-conversation-accept` |
| Тесты | `test_<что>_<условие>` в файлах `test_<тема>.py` | `test_public_profile_hides_university_when_flag_off` |
| Константы | `UPPER_SNAKE` | `MIN_AGE = 16` |
| Коммит миграции | миграция в одном коммите с изменением модели | |

### Frontend (JS/JSX)
| Что | Правило | Пример |
|---|---|---|
| Компоненты | `PascalCase.jsx`, имя файла = имя компонента, **default export** | `ProfileCard.jsx` |
| CSS компонента | CSS Modules `Name.module.css`, классы `camelCase` | `styles.cardTitle` |
| Хуки | `useXxx.js`, named export | `useDebounce` |
| Контексты | `XContext.jsx` экспортирует `XProvider` и `useX` | `useAuth()` |
| API-функции | глагол + сущность | `getProfile`, `searchProfiles`, `sendMessage` |
| Ключи текстов | `область.экран.элемент` | `auth.login.submit` |
| Константы | `UPPER_SNAKE` | `POLL_CHAT_MS` |
| Переменные состояния | `[x, setX]`; булевы — `isX/hasX` | `isLoading` |
| События | `onX` (props), `handleX` (внутри) | `onSave`, `handleSubmit` |

Язык: имена в коде — английские; документы и комментарии к сложным местам — русские (CLAUDE.md). Прочие тексты UI — только через `texts/`.

## 6. Фронтенд: где живёт состояние и запросы

| Вид состояния | Где хранится | Примеры |
|---|---|---|
| Серверные данные экрана | локально в странице через `useApi` (`{data, error, isLoading, reload}`) | список поиска, профиль, диалоги |
| Сессия пользователя | `AuthContext` | `user`, `status` |
| Тема | `ThemeContext` (+ `localStorage['nk_theme']` в `try/catch`) | `system/light/dark` |
| Уведомления UI | `ToastContext` | тосты |
| Справочники | `MetaContext`: один запрос `/api/meta/` при старте, кэш в памяти | страны, направления, лимиты |
| Фильтры поиска и страница | **URL** (`useSearchParams`) | `/discover?country=UZ&page=2` |
| Состояние формы | `useState` в форме/мастере (`RegisterPage` держит данные 8 шагов в одном объекте) | |
| Счётчики сообщений | `usePolling` внутри `AppLayout` (30 с) и `ChatWindow` (5 с, только при видимой вкладке) | |

Что **не** храним на клиенте: токены, пароли, данные профиля, сообщения — ни в `localStorage`, ни в `sessionStorage`. В `localStorage` допускается только выбор темы (и, при желании, история поиска с ключом по `username` — как в legacy `nklocal_search_history_`).

Правила запросов:
1. Только через `api/*.js` → `apiClient`. Компоненты и страницы не используют `fetch` напрямую.
2. Ошибка — всегда `ApiError` (`status`, `code`, `message`, `fields`, `nonFieldErrors`, `retryAfter`). Форма раскладывает `fields` по полям, общие ошибки — тост по `texts/errors.js`.
3. Параллельные запросы отменяются через `AbortController` (`signal` в `useApi`) — исправление гонки в поиске (F-16).
4. Кнопки отправки блокируются на время запроса (`isSubmitting`), чтобы исключить дубли (F-8).
5. После успешной мутации экран обновляет локальные данные ответом сервера или вызывает `reload()`.

## 7. AuthContext и apiClient (CSRF)

### 7.1 Cookie и заголовки
- `sessionid` — HttpOnly (JS не читает), `SameSite=Lax`, `Secure` на проде.
- `csrftoken` — **не** HttpOnly (`CSRF_COOKIE_HTTPONLY = False`), JS читает его и отправляет в заголовке `X-CSRFToken` для POST/PUT/PATCH/DELETE. Безопасно, потому что токен CSRF — не секрет сессии.
- `GET /api/auth/csrf/` помечен `@ensure_csrf_cookie`; после логина Django ротирует токен и обновляет cookie.

### 7.2 Эскиз `api/apiClient.js`
```js
export class ApiError extends Error {
  constructor(status, error = {}) {
    super(error.message || 'Request failed')
    this.status = status
    this.code = error.code || 'unknown'
    this.fields = error.fields || {}              // { username: [{code, message}] }
    this.nonFieldErrors = error.non_field_errors || []
    this.retryAfter = error.retry_after ?? null
  }
}

let csrfPromise = null
export function ensureCsrf() {
  csrfPromise ??= fetch('/api/auth/csrf/', { credentials: 'same-origin' })
  return csrfPromise
}
const getCookie = (name) =>
  document.cookie.split('; ').find((c) => c.startsWith(name + '='))?.split('=')[1]

let onUnauthorized = () => {}                     // подписывается AuthContext
export const setUnauthorizedHandler = (fn) => { onUnauthorized = fn }

async function request(method, path, { params, body, formData, signal } = {}, retried = false) {
  const unsafe = !['GET', 'HEAD'].includes(method)
  if (unsafe) await ensureCsrf()
  const url = '/api' + path + (params ? '?' + new URLSearchParams(params) : '')
  const headers = {}
  if (body) headers['Content-Type'] = 'application/json'
  if (unsafe) headers['X-CSRFToken'] = getCookie('csrftoken')
  let res
  try {
    res = await fetch(url, { method, headers, credentials: 'same-origin', signal,
      body: formData ?? (body ? JSON.stringify(body) : undefined) })
  } catch (e) {
    if (e.name === 'AbortError') throw e
    throw new ApiError(0, { code: 'network_error' })
  }
  if (res.status === 204) return null
  const data = await res.json().catch(() => null)
  if (res.ok) return data
  const err = new ApiError(res.status, data?.error)
  if (err.code === 'csrf_failed' && !retried) { csrfPromise = null; return request(method, path, arguments[2], true) }
  if (err.status === 401 || err.code === 'account_banned') onUnauthorized(err)
  throw err
}
export const api = {
  get: (p, o) => request('GET', p, o),
  post: (p, body, o) => request('POST', p, { ...o, body }),
  put: (p, body, o) => request('PUT', p, { ...o, body }),
  patch: (p, body, o) => request('PATCH', p, { ...o, body }),
  delete: (p, o) => request('DELETE', p, o),
  upload: (p, formData, o) => request('PUT', p, { ...o, formData }),   // аватар
}
```
Принципы: один формат ошибок; повтор ровно один раз при `csrf_failed`; нет токенов в JS-хранилищах; `Content-Type` для `FormData` не выставляется (браузер добавит boundary).

### 7.3 `AuthContext`
Состояния `status`: `'loading' | 'authenticated' | 'anonymous' | 'error'` (последнее — сеть/сервер недоступны: экран «Try again», а не молчаливая пустая страница, исправление F-5).

```
AuthProvider
  при монтировании: ensureCsrf() → getMe()
      200 → status='authenticated', user=Own
      401 → status='anonymous'
      прочее/сеть → status='error'
  setUnauthorizedHandler(() => сбросить user, status='anonymous', перейти на /login?next=…)
  value: { status, user, login(email, password), register(payload), logout(), refreshMe(), setUser(own) }
  login → api.post('/auth/login/') → setUser(ответ)       // ответ = Own-профиль
  logout → api.post('/auth/logout/') → user=null           // независимо от успеха
```
Маршруты: `ProtectedRoute` (пока `loading` — спиннер; `anonymous` → `/login`), `GuestRoute` (авторизованного уводит на `/discover`). Права **не** проверяются на клиенте как защита — это только навигация; сервер отвечает 401/403/404.

## 8. Переменные окружения

`backend/.env` (локально; в git — только `backend/.env.example`):

| Переменная | Назначение | dev | prod |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | ключ подписи | случайная строка | уникальная, ≥50 символов |
| `DJANGO_DEBUG` | режим отладки (по умолчанию `False`) | `True` | `False` |
| `DJANGO_ALLOWED_HOSTS` | допустимые хосты | `localhost,127.0.0.1` | домен |
| `DATABASE_URL` | PostgreSQL | `postgres://user:pass@localhost:5432/networkit` | то же, на VPS |
| `CSRF_TRUSTED_ORIGINS` | доверенные origin | `http://localhost:5173` | `https://домен` |
| `SITE_URL` | база ссылок в письмах (маршруты фронтенда) | `http://localhost:5173` | `https://домен` |
| `EMAIL_URL` | почта (формат django-environ) | `consolemail://` | `smtp+tls://user:pass@host:587` |
| `DEFAULT_FROM_EMAIL` | отправитель | `NetworkIt <noreply@localhost>` | адрес домена |
| `MEDIA_ROOT`, `STATIC_ROOT` | пути файлов | `backend/media`, `backend/staticfiles` | абсолютные пути на VPS |
| `SESSION_COOKIE_AGE` | срок сессии, с | `1209600` | `1209600` |
| `SECURE_HSTS_SECONDS` | HSTS | `0` | `31536000` после проверки HTTPS |

Frontend: переменные не нужны (запросы идут на относительный `/api`). Необязательная `frontend/.env.development.local` (не коммитится): адрес прокси, если Django не на `127.0.0.1:8000`.

Правило: ни одного секрета в коде; текущий `SECRET_KEY` в `backend/backend/settings.py` — dev-заглушка, переносится в `.env` на этапе 1.

## 9. Конфигурация backend (ключевое)

**DRF:** `SessionAuthentication` (проверяет CSRF); `DEFAULT_PERMISSION_CLASSES = [IsAuthenticated, IsNotBanned]` (публичные view явно ставят `AllowAny`); рендерер только JSON (browsable API выключен на проде); `EXCEPTION_HANDLER` из `api/exceptions.py`; `DjangoFilterBackend`; пагинация и throttle-классы из SPEC §3.0.
**Безопасность (prod):** `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`, HSTS, `X_FRAME_OPTIONS = 'DENY'`, `SECURE_CONTENT_TYPE_NOSNIFF`. CSP-заголовок ставит Nginx: `default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self'; style-src-attr 'unsafe-inline'; font-src 'self'; frame-ancestors 'none'` (шрифты самохостятся через @fontsource, внешних CDN нет; inline-скриптов нет — поэтому `theme-init.js` внешний файл).
**Throttling и кэш:** серверов Gunicorn несколько процессов, поэтому локальная память (`LocMemCache`) даёт неточные счётчики; используем **кэш в БД** (`DatabaseCache`, `python manage.py createcachetable`) — без Redis (его нет в списке разрешённых). Тесты переопределяют ставки.
**Почта:** `EMAIL_URL` через `env.email()`; шаблоны писем — простой текст (`templates/users/email/*.txt`). Подтверждение email и смена email — подписанные токены `django.core.signing` с солью по назначению и сроком (3 дня); сброс пароля — стандартный `default_token_generator`.
**Файлы:** `MEDIA_ROOT` вне каталога с кодом; ограничения `DATA_UPLOAD_MAX_MEMORY_SIZE`/`FILE_UPLOAD_MAX_MEMORY_SIZE` ≈ 6 МБ; Nginx `client_max_body_size 6m`; `Image.MAX_IMAGE_PIXELS` ограничен (защита от «бомб»); в `/media/` Nginx отдаёт `X-Content-Type-Options: nosniff` и не исполняет скрипты.
**БД:** PostgreSQL обязателен уже в dev/тестах (используются `ArrayField`, CheckConstraint с regex).
**Версии:** в venv установлен Django 6.1.2; `Pipfile` — Python 3.14. Совместимость `psycopg`/`Pillow`/`gunicorn` с этой связкой проверить на этапе 1 [нужна проверка в рантайме].

## 10. Библиотеки (решение 7) и что прошу согласовать сверх списка

| Слой | Библиотеки |
|---|---|
| Backend | `djangorestframework` (стек), `psycopg`, `django-environ`, `Pillow`, `django-filter`, `gunicorn`, `whitenoise` |
| Frontend | `react-router-dom`, `@fontsource/inter`, `@fontsource/sora` (или `@fontsource-variable/*` — Q-A3), `prettier` (dev) |
| Не нужны | `django-cors-headers` (один домен), JWT, Redis, Sentry, react-query, lucide-react (см. Q-A1), тест-раннеры для фронтенда (см. Q-A2) |

## 11. Деплой на VPS (решение 12)

Состав: Ubuntu LTS, PostgreSQL, Python-venv с Gunicorn под `systemd` (unit `networkit.service`, unix-socket), Nginx, сертификат Let's Encrypt (certbot), cron.
Этапы деплоя: `git pull` → `pipenv install` → `python manage.py migrate` → `collectstatic` → `createcachetable` → `npm ci && npm run build` (папка `frontend/dist`) → `systemctl restart networkit`.
Nginx: HTTP→HTTPS редирект; `location /api/ {}` и `/admin/` → Gunicorn; `/media/` → alias; `/` → `dist` с `try_files $uri /index.html`; заголовки безопасности и CSP; gzip/brotli для статики; долгий кэш для хэшированных файлов `assets/*`, `no-cache` для `index.html`.
Эксплуатация: ежедневный `pg_dump` (+ копия `media/`), проверка восстановления; ежедневный cron `python manage.py purge_unverified`; ротация логов; обновления безопасности ОС; отдельный пользователь БД с минимальными правами; файрвол (22/80/443).

## 12. Стратегия тестов

### 12.1 Backend (обязательно)
Инструмент: встроенный `manage.py test`, `rest_framework.test.APITestCase`; фабрики — простые функции в `tests/factories.py` (без сторонних библиотек). БД — PostgreSQL. В `settings` для тестов: быстрый хэшер паролей, почта в памяти, повышенные лимиты throttle.

**Обязательное покрытие (блокирует merge этапа):**
1. **Права.** Тест по таблице SPEC §2: для каждого endpoint × роль (аноним, пользователь, не-участник, забаненный, не подтверждённый) ожидаемые 401/403/404/2xx. POST/PUT/PATCH/DELETE без `X-CSRFToken` → 403 (`APIClient(enforce_csrf_checks=True)`).
2. **Приватность.** Для Public/Card/Mini/Own проверяется **точный набор ключей** (`assertEqual(set(data), ALLOWED)`), поэтому новое поле не «утекает» молча. Комбинации флагов `show_*`; возраст 16–17 (контакты всегда `null`, включение отклоняется); `email`, `date_of_birth`, `gender`, `is_banned`, privacy-флаги чужих — отсутствуют; скрытое = `null`, неотличимо от пустого.
3. **Видимость.** Профили забаненных, неподтверждённых, `show_in_search=false`, заблокированных (в обе стороны) отсутствуют в поиске, избранном, списках диалогов; прямой профиль забаненного/заблокированного → 404.
4. **Оракулы поиска.** Скрытый вуз не находится по `q`; скрытая страна/город не находятся фильтрами (SPEC §6.3).
5. **Сообщения.** Таблица состояний SPEC §7.3 целиком, маскирование отказа, лимиты, одновременное создание двух запросов (гонка → один диалог, второй 409), чужой диалог → 404.
6. **Аутентификация.** Одинаковый ответ регистрации для занятого email; порядок проверок логина (сначала пароль, потом `email_not_verified`/`account_banned`); истечение токенов; сброс пароля и бан сбрасывают сессии; удаление аккаунта удаляет файл аватара.
7. **Валидация.** Граничные значения таблицы SPEC §5: возраст (в день 16-летия — ok, накануне — нет), username (regex, зарезервированные), аватар (поддельный PNG, SVG, >5 МБ, слишком большие пиксели, EXIF удалён).
8. **Запросы.** `assertNumQueries` на поиске и списке диалогов (нет N+1).

Каждый исправленный баг получает регрессионный тест. Процентной цели покрытия нет — важен чек-лист выше.

### 12.2 Frontend
Библиотек для тестов в списке нет, поэтому на MVP: `npm run lint` (oxlint), `npm run build`, `npx prettier --check .` и **ручные чек-листы** по критериям SPEC §8 (мобильный 360 px, планшет 768, десктоп 1280; светлая и тёмная тема; клавиатура; медленная сеть). Автотесты компонентов (Vitest + Testing Library) — по Q-A2.

### 12.3 Перед каждым коммитом/PR
```
python manage.py makemigrations --check --dry-run
python manage.py test
npm run lint && npm run build && npx prettier --check .
```

## 13. Ветки и порядок коммитов

**Ветки:** `main` — всегда рабочая. Один этап SPEC §8 = одна ветка `feature/NN-кратко` (например `feature/04-auth-api`); исправления — `fix/кратко`; документы — `docs/кратко`. Прямые коммиты в `main` — только для мелких правок документов.
**Pull request** = один этап; описание содержит чек-лист критериев приёмки этапа и результат команд из §12.3. Слияние — squash с сообщением вида `feat: auth API (stage 4)`; до слияния внутри ветки история остаётся из мелких коммитов.
**Порядок коммитов внутри этапа (малые, ≤ ~400 строк диффа):**
1. `chore:` зависимости, настройки (`.gitignore`, `.env.example`, конфиги);
2. `feat(models):` модель + миграция в одном коммите (применённые миграции не редактируем);
3. `test:` тесты прав/приватности для будущего API (или вместе со следующим коммитом);
4. `feat(api):` serializers → selectors/services → views → urls;
5. `feat(ui):` api-функции → компоненты → страница → тексты в `texts/`;
6. `docs:` обновление SPEC/ARCHITECTURE, если контракт изменился (сначала меняем SPEC, потом код).
**Формат сообщения:** `тип(область): суть` в повелительном наклонении, английский; типы `feat, fix, refactor, test, docs, chore, style`. Тег `v0.1.0` — после этапа 13.
**Никогда не коммитим:** `.env`, `media/`, `staticfiles/`, `node_modules/`, `dist/`, `__pycache__/`, `*.pyc`, дампы БД, ключи.
**Первый коммит нового процесса:** документы `docs/*.md` + `CLAUDE.md` (сейчас не отслеживаются git).

## 14. Вопросы ко мне

1. **Q-A1. Иконки.** В legacy ~30 иконок lucide через CDN. В списке библиотек `lucide-react` нет. Варианты: (а) добавить `lucide-react`; (б) скопировать нужные SVG (лицензия ISC) в `components/ui/Icon.jsx` без зависимости. Рекомендую (б). Что выбираем?
2. **Q-A2. Тесты фронтенда.** Разрешаешь `vitest` + `@testing-library/react` (dev-зависимости) для критичных мест (`apiClient`, `AuthContext`, формы)? Рекомендую да; иначе — только ручные чек-листы.
3. **Q-A3. Шрифты.** `@fontsource/inter` + `@fontsource/sora` (статические веса: Inter 400/500/600/700, Sora 700/800) или variable-пакеты (`@fontsource-variable/*`, один файл на шрифт)? Рекомендую variable (меньше запросов).
4. **Q-A4. Prettier.** Стиль: одинарные кавычки; точки с запятой — да или нет (шаблон Vite без `;`, legacy `app.js` с `;`)? Ширина строки 100?
5. **Q-A5. Роутер.** `createBrowserRouter` (data router) или простой `<BrowserRouter>` + `<Routes>` (проще для обучения)? Рекомендую второй.
6. **Q-A6. Язык коммитов и PR:** английский (как в §13) или русский?
7. **Q-A7. settings.py:** оставляем один файл с окружением или делаем пакет `settings/{base,dev,prod}.py`? Рекомендую один файл (проще), без переименований.
8. **Q-A8. Хранилище throttling:** кэш в БД на одном VPS — устраивает (Redis не добавляем)?
9. **Q-A9. Журналирование/мониторинг:** достаточно логов Gunicorn/Nginx и `journalctl`, без внешних сервисов?
10. **Q-A10. Домен и провайдер почты** известны? Влияет на `SITE_URL`, SPF/DKIM и этап 13.
11. **Q-A11. Pipenv.** Основной менеджер пакетов — Pipenv (`Pipfile` уже есть, `[packages]` пока пуст) — подтверждаешь? На VPS ставим тем же.
12. **Q-A12. Python 3.14** в Pipfile: оставляем или берём стабильную LTS-связку (например, Python 3.12/3.13), если колёса `Pillow`/`psycopg` под 3.14 не готовы? Решим после проверки на этапе 1.
