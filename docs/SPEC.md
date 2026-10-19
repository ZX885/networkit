# NetworkIt — техническое задание (SPEC)

Статус: черновик для согласования. Основа: `CLAUDE.md`, `docs/ANALYSIS.md`, 13 принятых решений заказчика (ниже — «Решения»). Старый сайт `networkit-backend/` — только источник идей. Архитектура — `docs/ARCHITECTURE.md`, визуальная система — `docs/DESIGN_SYSTEM.md`.

Состояние каркаса на дату написания (проверено чтением): Django 6.1.2 в venv `networkit/`, `Pipfile` без пакетов (Python 3.14), `users` не подключён к `INSTALLED_APPS`, БД SQLite, DRF не установлен; `frontend/` — Vite + React 19 без роутера, `vite.config.js` без прокси.

## 0. Решения (входные данные)

| № | Решение | Следствие в ТЗ |
|---|---|---|
| 1 | Возраст 16+; у 16–17 контакты никогда не публичны | §5 валидация возраста, §6 приватность |
| 2 | Город виден, контакты скрыты по умолчанию | §6 умолчания |
| 3 | Телефон не собираем | поля `phone` нет |
| 4 | Сессии Django + CSRF, один домен | §3 cookie, CSRF |
| 5 | Подтверждение почты включено | §3 регистрация/вход |
| 6 | Интерфейс на английском, тексты в одном месте | коды ошибок + ключи текстов |
| 7 | Разрешённые библиотеки | см. ARCHITECTURE §10 |
| 8 | Страна — ISO-код; направление — список + «Other»; вуз — текст | §1, §5 |
| 9 | Первое сообщение — запрос; есть блокировка | §7 |
| 10 | Чистая база | миграции с нуля |
| 11 | Тёмная тема, по умолчанию системная | DESIGN_SYSTEM §6 |
| 12 | Деплой на VPS | ARCHITECTURE §11 |
| 13 | Модерация жалоб через Django Admin | §2, §3.14 |

Объём MVP: регистрация и вход, профиль, поиск, аватар, избранное, базовые личные сообщения (с запросами и блокировкой), адаптивный дизайн, деплой. **Вне MVP:** уведомления, админ-API, realtime (WebSocket/SSE), верификация телефона, редактирование/удаление сообщений, вложения в чате, i18n (только подготовка), смена username и даты рождения.

---

## 1. Модели данных

Обозначения доступа: **O** — владелец; **P\*** — любой авторизованный пользователь, но с учётом приватности (§6); **U** — любой авторизованный; **S** — staff (только Django Admin); **sys** — только сервер. «Запись API» — что может менять клиент.

### 1.1 `users.User` (кастомная модель, создаётся до первой миграции)
`AbstractBaseUser + PermissionsMixin`, `USERNAME_FIELD = "email"`.

| Поле | Тип | Ограничения | Чтение | Запись API |
|---|---|---|---|---|
| id | BigAutoField PK | — | sys (наружу не отдаётся) | — |
| email | EmailField(254) | UNIQUE по `Lower(email)` (UniqueConstraint), хранится в нижнем регистре | O, S | регистрация; смена через подтверждение |
| password | CharField(128) | хэш Django (PBKDF2/Argon2 по настройкам) | — | регистрация, смена, сброс |
| pending_email | EmailField(254) null | новый email до подтверждения | O | через `/auth/email/change/` |
| email_verified_at | DateTimeField null | null = не подтверждён | O (как `email_verified`) | sys |
| is_banned | BooleanField | default False | O (как 403), S | **только S** |
| banned_at, ban_reason | DateTime null, CharField(200) | служебные | S | S |
| is_staff, is_superuser, is_active | Boolean | стандарт Django; `is_active=False` только у удалённых/технических | S | S |
| date_joined, last_login | DateTime | стандарт | S | sys |

### 1.2 `profiles.Profile` (1:1 с User, `related_name="profile"`)

| Поле | Тип | Ограничения | Чтение | Запись API |
|---|---|---|---|---|
| user | OneToOne(User, CASCADE) | PK-связь | sys | — |
| username | CharField(30) | UNIQUE, нижний регистр, regex §5, не в списке зарезервированных; CheckConstraint по regex | P (публичный идентификатор) | только при регистрации (в MVP неизменяем) |
| first_name | CharField(60) | 1–60 | P | O |
| last_name | CharField(60) | 1–60 | P | O |
| date_of_birth | DateField | возраст ≥16 на момент регистрации, ≤100 | **O только** | только при регистрации |
| gender | CharField(20) blank | choices: `male, female, non_binary, undisclosed` | **O только** | O |
| country | CharField(2) | ISO 3166-1 alpha-2 из списка §1.8 | P\* (`show_location`) | O |
| region | CharField(100) blank | | P\* (`show_location`) | O |
| city | CharField(100) | 1–100 | P\* (`show_location`) | O |
| status | CharField(12) | `student` / `professional` | P | O |
| school | CharField(100) blank | | P | O |
| university | CharField(120) blank | свободный текст | P\* (`show_university`) | O |
| field | CharField(40) | код из списка §1.8 (включая `other`) | P | O |
| year_level | CharField(40) blank | | P | O |
| bio | TextField | ≤300 символов | P | O |
| interests | ArrayField(CharField(30)) | коды из списка, ≤10, без дублей | P | O |
| languages | ArrayField(CharField(30)) | коды из списка, ≤10 | P | O |
| goals | ArrayField(CharField(30)) | коды из списка, ≤8 | P | O |
| telegram, instagram, whatsapp, linkedin, public_email | CharField/EmailField blank | форматы §5; **не принимаются для 16–17** | P\* (`show_contacts`, только 18+) | O (только 18+) |
| avatar | ImageField(upload_to="avatars/") null | §5; имя — uuid, формат WebP | P (как `avatar_url`) | O через `/me/avatar/` |
| show_location | Boolean | **default True** | O | O |
| show_university | Boolean | default True | O | O |
| show_contacts | Boolean | **default False** | O | O (только 18+, иначе принудительно False) |
| show_in_search | Boolean | default True | O | O |
| show_join_date | Boolean | default True | O | O |
| created_at, updated_at | DateTime | `auto_now_add` / `auto_now` | P\* (`show_join_date`) / O | sys |

Индексы: `country`, `field`, `status`, `(show_in_search)`, GIN по `interests/languages/goals` (для фильтров по содержимому массива), позже `pg_trgm` по имени/логину (вне MVP, при росте).
Приватность хранится полями профиля (а не отдельной таблицей): фильтры поиска обходятся без JOIN.

### 1.3 `profiles.SavedProfile`
| Поле | Тип | Ограничения | Доступ |
|---|---|---|---|
| owner | FK(User, CASCADE) | | O |
| saved_user | FK(User, CASCADE) | `owner ≠ saved_user` (CheckConstraint) | O |
| created_at | DateTime | | O |
UNIQUE(owner, saved_user), индекс `(owner, -created_at)`. Чужие закладки не видны никому (даже S — только в Admin, только чтение). `related_name`: `saved_profiles` (у владельца), `saved_by` (у сохранённого). Лимит — `SAVED_MAX = 200` закладок на человека (настройка, в `/api/meta/` как `limits.saved_max`).

### 1.4 `moderation.Block`
Приложение `apps/moderation` (а не `profiles`): блокировки и жалобы затрагивают поиск, избранное, диалоги и админку, а отдельное приложение не создаёт циклов импорта (`profiles` и `messaging` импортируют только `moderation/rules.py`).
| Поле | Тип | Ограничения | Доступ |
|---|---|---|---|
| blocker | FK(User, CASCADE), `related_name="blocks_made"` | | O |
| blocked | FK(User, CASCADE), `related_name="blocks_received"` | `blocker ≠ blocked` (CheckConstraint) | O (blocker видит список) |
| created_at | DateTime | | |
UNIQUE(blocker, blocked), индексы `(blocked, blocker)` и `(blocker, -created_at)`. Блокировка действует **в обе стороны**; блокируемый список и факт блокировки **не видит** (§7.2, §7.4). Лимит — `BLOCKS_MAX = 200` блокировок на человека (настройка, в `/api/meta/` как `limits.blocks_max`).

### 1.5 `moderation.Report`
| Поле | Тип | Ограничения | Чтение | Запись |
|---|---|---|---|---|
| reporter | FK(User, SET_NULL) null | | S | создаётся API |
| target | FK(User, CASCADE), `related_name="reports_received"` | `≠ reporter` (CheckConstraint) | S | API |
| conversation | FK(messaging.Conversation, SET_NULL) null | жалоба на диалог: ссылка, а не копия текста | S | API |
| reason | CharField(20) | `fake_profile, spam, inappropriate, harassment, underage, other` | S | API |
| details | CharField(1000) blank | ≤1000 (`limits.details_max`) | S | API |
| status | CharField(12) | `open, dismissed, actioned`, default `open` | S | S |
| staff_note | CharField(500) blank | | S | S |
| handled_by | FK(User, SET_NULL) null; handled_at DateTime null | ставятся автоматически при смене статуса | S | sys |
| created_at | DateTime | | S | sys |
UniqueConstraint(reporter, target) при `status=open` (нельзя спамить повторными жалобами). Пользователь отправленные жалобы не читает. Читать жалобы (включая текст) могут только суперпользователи (§3.14).

### 1.6 `messaging.Conversation`
| Поле | Тип | Ограничения | Доступ |
|---|---|---|---|
| id | UUID PK | непредсказуемый | участник |
| user_a, user_b | FK(User, CASCADE) | `user_a_id < user_b_id` (CheckConstraint), UNIQUE(user_a, user_b) | участник |
| initiator | FK(User, CASCADE) | один из двух участников (CheckConstraint) | участник |
| status | CharField(10) | `pending, accepted, declined` | участник (с маскированием, §7) |
| decided_at | DateTime null | момент accept/decline | участник |
| last_message_at | DateTime null | обновляется при отправке | участник |
| created_at | DateTime | | участник |
«Заблокирован» — не значение поля, а вычисляется по таблице `Block` (§7).

### 1.7 `messaging.Message`
| Поле | Тип | Ограничения | Доступ |
|---|---|---|---|
| id | BigAutoField PK | возрастает → курсор | участник |
| conversation | FK(Conversation, CASCADE) | | участник |
| sender | FK(User, CASCADE) | один из участников | участник |
| body | TextField | 1–4000 (первое сообщение-запрос — ≤500), после `strip` не пусто | участник |
| created_at | DateTime | индекс (conversation, created_at) | участник |
| seen_at | DateTime null | ставит только получатель через `/read/` | участник |
Сообщения не редактируются и не удаляются клиентом (вне MVP). **Владельцы сайта (суперпользователи, `is_superuser`) могут читать переписку в Django Admin** — модели `Conversation` и `Message` зарегистрированы только для чтения и только для суперпользователя (обычный staff модуль не видит; добавлять, менять и удалять нельзя). Текст сообщения виден только в карточке сообщения; просмотр не пишет `LogEntry`, а приложение не выводит тела сообщений в логи и трейсбеки (ошибки по `/api/conversations/` логируются без текста исключения). **Это нужно указать в Privacy Policy** (переписка не защищена сквозным шифрованием и может просматриваться администрацией).

### 1.8 Справочники (источник — `profiles/choices.py`, отдаются через `GET /api/meta/`)
- **status:** `student`, `professional`.
- **gender:** `male`, `female`, `non_binary`, `undisclosed`.
- **field** (36 значений legacy `FLDS`, app.js:390) + `other`: Accounting, Architecture, Artificial Intelligence, Biology, Biotechnology, Business Administration, Chemistry, Civil Engineering, Computer Science, Data Science, Design, Economics, Education, Electrical Engineering, Entrepreneurship, Environmental Science, Finance, History, International Relations, Journalism, Law, Literature, Marketing, Mathematics, Mechanical Engineering, Medicine, Music, Neuroscience, Nursing, Philosophy, Physics, Political Science, Psychology, Public Health, Sociology, Software Engineering. Код — `snake_case` от названия (`computer_science`).
- **interests** (25, `INTS`, app.js:206), **languages** (27, `LAS`, app.js:207) — переносятся как есть, коды `snake_case`; расширение набора — Q-3.
- **goals** — единый список вместо двух расходящихся (`GLS` app.js:208 и `GOALS` app.js:391): `friends`, `study_partners`, `project_collaborators`, `startup_cofounders`, `mentorship`, `research_collaboration`, `internship_opportunities`, `career_networking`, `cv_portfolio`, `college_prep` (10).
- **country:** ISO-коды; стартовый набор — 63 страны из `CTRS` (app.js:209) + Kyrgyzstan, Tajikistan, Turkmenistan (Q-3). Метки — английские, из `/meta/`.

---

## 2. Матрица прав

Роли: **Аноним** — нет сессии (в т.ч. не подтвердивший email: войти не может). **Пользователь** — вошёл, email подтверждён, не забанен. **Участник диалога** — пользователь, входящий в конкретный `Conversation`. **Забаненный** — `is_banned=True`: вход запрещён, живые сессии удаляются при бане, любой запрос → `403 account_banned`. **Staff** — `is_staff`; работает только в Django Admin (`/admin/`), в API права как у обычного пользователя (админ-API вне MVP).

Условные обозначения: ✅ можно · ❌ нельзя (код ответа) · 🔒 с условием (в скобках).

| Ресурс / действие | Аноним | Пользователь | Участник диалога | Забаненный | Staff |
|---|---|---|---|---|---|
| `GET /meta/`, `GET /stats/`, `GET /auth/csrf/`, `username-available` | ✅ | ✅ | ✅ | ✅ (csrf) / ❌ | ✅ |
| Регистрация, вход, сброс пароля, подтверждение email | ✅ | ❌ 403 `already_authenticated` | — | вход ❌ 403 `account_banned` | ✅ |
| Свой профиль `GET/PATCH /me/`, privacy, avatar | ❌ 401 | ✅ (O) | ✅ | ❌ 403 | ✅ (как O) |
| Удаление своего аккаунта | ❌ 401 | ✅ (пароль) | ✅ | ❌ 403 | ✅ |
| Поиск `GET /profiles/` | ❌ 401 | ✅ (приватность §6) | ✅ | ❌ 403 | ✅ |
| Чужой профиль `GET /profiles/{username}/` | ❌ 401 | 🔒 (не забанен, не заблокирован, не self-block) | ✅ | ❌ 403 | ✅ |
| Избранное (list/put/delete) | ❌ 401 | ✅ (только своё) | ✅ | ❌ 403 | ✅ |
| Жалоба `POST /reports/` | ❌ 401 | ✅ (не на себя) | ✅ | ❌ 403 | ✅ |
| Чтение жалоб, смена статуса, бан | ❌ | ❌ 404 | ❌ | ❌ | ✅ (только Admin) |
| Блокировки (list/put/delete) | ❌ 401 | ✅ (свои) | ✅ | ❌ 403 | ✅ |
| Создать запрос на переписку | ❌ 401 | 🔒 (§7: нет блокировки, нет активного диалога, лимиты) | — | ❌ 403 | ✅ |
| Список диалогов | ❌ 401 | ✅ (только свои) | ✅ | ❌ 403 | ✅ |
| Чтение диалога/сообщений | ❌ 401 | ❌ 404 (чужой диалог) | ✅ | ❌ 403 | ❌ 404 в API |
| accept / decline | ❌ 401 | ❌ 404 | 🔒 только получатель, статус `pending` | ❌ 403 | ❌ |
| Отправка сообщения | ❌ 401 | ❌ 404 | 🔒 по таблице §7.3 | ❌ 403 | 🔒 |
| `read` (пометить прочитанным) | ❌ 401 | ❌ 404 | ✅ (только входящие) | ❌ 403 | — |
| Django Admin | ❌ | ❌ | ❌ | ❌ | ✅ |

Принципы: (1) «чужой объект» всегда отвечает **404**, а не 403, чтобы не подтверждать существование; (2) права проверяются на сервере в `permission_classes` и `get_queryset()`; (3) `IsNotBanned` — глобальный permission для всех авторизованных endpoint'ов; (4) неподтверждённый email = не может получить сессию.

---

## 3. Контракт API

### 3.0 Общие соглашения
- Базовый путь `/api/`, JSON (`Content-Type: application/json`), кроме загрузки аватара (`multipart/form-data`). Версию в URL не вводим.
- Аутентификация — cookie `sessionid` (HttpOnly, SameSite=Lax, Secure на проде). Для **небезопасных методов** (POST/PUT/PATCH/DELETE) обязателен заголовок `X-CSRFToken` со значением cookie `csrftoken`. Первый вызов приложения — `GET /api/auth/csrf/`.
- Время — ISO 8601 UTC (`2026-10-10T08:15:30Z`). Идентификаторы пользователей наружу не отдаются; публичный ключ — `username`. Диалоги — UUID.
- Тексты для UI живут во фронтенде (`src/texts`), ключ — поле `code` ошибки; `message` — английский запасной текст.

**Единый формат ошибок** (все не-2xx):
```json
{
  "error": {
    "code": "validation_error",
    "message": "Please correct the highlighted fields.",
    "fields": {
      "username": [{"code": "taken", "message": "This username is already taken."}],
      "date_of_birth": [{"code": "too_young", "message": "You must be at least 16 years old."}]
    },
    "non_field_errors": []
  }
}
```
Для ошибок не по полям `fields` и `non_field_errors` отсутствуют:
```json
{"error": {"code": "account_banned", "message": "This account has been suspended."}}
```
Коды HTTP: 400 `validation_error`/`invalid_credentials`/`invalid_token`; 401 `not_authenticated`; 403 `permission_denied`, `csrf_failed`, `email_not_verified`, `account_banned`, `accept_required`, `conversation_closed`, `already_authenticated`; 404 `not_found`; 405 `method_not_allowed`; 409 `conversation_exists`, `request_pending`, `incoming_request_exists`, `invalid_state`; 413 `file_too_large`; 415 `unsupported_media_type`; 429 `throttled` (+ заголовок `Retry-After`, поле `retry_after` в секундах); 500 `server_error` (без деталей).

**Пагинация (списки):** `PageNumberPagination`; параметры `page` (с 1), `page_size` (по умолчанию 12, максимум 24).
```json
{"count": 57, "next": "/api/profiles/?page=2", "previous": null, "results": [ ... ]}
```
Выход за диапазон страниц → 404 `not_found` (стандарт DRF). **Сообщения** — курсорная выдача (§3.12).

**Throttling** (DRF `ScopedRateThrottle` + общие; ключ — IP для анонима, user id для авторизованного; хранилище — кэш БД, ARCHITECTURE §9):

| Scope | Лимит | Применяется к |
|---|---|---|
| `anon` | 60/min | все анонимные |
| `user` | 300/min | все авторизованные |
| `login` | 5/min и 30/hour по IP; +10/hour по email | `/auth/login/` |
| `register` | 5/hour по IP | `/auth/register/` |
| `email_flow` | 5/hour по IP и 5/day по адресу email из тела запроса (`email` или `new_email`; считается и для несуществующих адресов) | `password-reset`, `email/change` (`resend-verification` — отдельный лимит `register`) |
| `account_password` | 10/hour на пользователя, общая корзина | проверки пароля: `password/change`, `email/change`, `DELETE /api/me/` |
| `token_confirm` | 30/hour по IP | `password-reset/confirm`, `email/change/confirm` |
| `username_check` | 30/min | `username-available` |
| `search` | 60/min | `GET /profiles/` |
| `saved` | 60/min | `PUT/DELETE /saved/{username}/` |
| `avatar` | 10/hour | `PUT /me/avatar/` |
| `report` | 10/day | `POST /reports/` |
| `message_request` | 10/day на пользователя | `POST /conversations/` (429). Отдельно: не более `PENDING_REQUESTS_MAX` = 20 одновременно висящих исходящих запросов (**409 `pending_requests_limit_reached`**, а не 429: это состояние, а не частота) |
| `message_send` | 30/min (`message_send`) и 500/day (`message_send_day`) | `POST /conversations/{id}/messages/` |
| `block` | 30/hour | `PUT /blocks/{username}/` |

Ответ 429:
```json
{"error": {"code": "throttled", "message": "Too many requests. Try again in 42 seconds.", "retry_after": 42}}
```

### 3.1 Служебные
| Метод | URL | Доступ | Описание |
|---|---|---|---|
| GET | `/api/auth/csrf/` | аноним+ | Устанавливает cookie `csrftoken`. Ответ `204`. |
| GET | `/api/meta/` | аноним+ | Справочники (кэшируемо). |
| GET | `/api/stats/` | аноним+ | Счётчики лендинга. |

`GET /api/meta/` → 200:
```json
{
  "countries": [{"code": "UZ", "label": "Uzbekistan"}],
  "fields": [{"code": "computer_science", "label": "Computer Science"}, {"code": "other", "label": "Other"}],
  "statuses": [{"code": "student", "label": "Student"}, {"code": "professional", "label": "Professional"}],
  "genders": [{"code": "undisclosed", "label": "Prefer not to say"}],
  "interests": [{"code": "ai", "label": "Artificial Intelligence"}],
  "languages": [{"code": "uzbek", "label": "Uzbek"}],
  "goals": [{"code": "study_partners", "label": "Study partners"}],
  "cities": [{"code": "tashkent", "label": "Tashkent"}, {"code": "samarkand", "label": "Samarkand"}],
  "country_cities_default": "UZ",
  "report_reasons": [],
  "limits": {"bio_max": 300, "min_age": 13, "adult_age": 18, "interests_max": 10, "languages_max": 10, "goals_max": 8, "saved_max": 200, "message_max": 4000, "request_max": 500}
}
```
`cities` — справочник городов Узбекистана (12 городов, `profiles/choices.py: UZ_CITIES`; код — название в нижнем регистре, метка — английское название), `country_cities_default` — страна, для которой клиент показывает этот список. «Other» в справочник не входит (это вариант интерфейса: свободный текст). Ответ публичный и кэшируемый (`Cache-Control: public, max-age=3600`, `ETag`, на `If-None-Match` — `304`). `report_reasons` — причины жалоб (`[{code, label}]`: `fake_profile, spam, inappropriate, harassment, underage, other`), `limits.blocks_max` (200) и `limits.details_max` (1000); остальные лимиты (`message_max`, `avatar_max_mb` и др.) добавятся вместе с соответствующими функциями.
`GET /api/stats/` → `{"members": 120, "fields": 14, "countries": 6}` (считаются только подтверждённые, не забаненные профили; клиент округляет для показа, как в legacy `updateHeroStats`).

### 3.2 Регистрация и подтверждение почты
**POST `/api/auth/register/`** — аноним. Тело:
```json
{
  "email": "jane@example.com", "password": "S3cure-pass!",
  "username": "janedoe", "first_name": "Jane", "last_name": "Doe",
  "date_of_birth": "2002-03-14", "gender": "female",
  "country": "UZ", "region": "Tashkent", "city": "Tashkent",
  "status": "student", "school": "", "university": "WIUT",
  "field": "computer_science", "year_level": "2nd year",
  "bio": "Building things.", "interests": ["ai"], "languages": ["english", "uzbek"], "goals": ["study_partners"],
  "contacts": {"telegram": "janedoe", "instagram": "", "whatsapp": "", "linkedin": "", "public_email": ""},
  "accepted_terms": true
}
```
Ответ `201` (всегда одинаковый, даже если email уже занят — защита от перебора адресов):
```json
{"status": "verification_sent", "email": "jane@example.com"}
```
Поведение: в одной транзакции создаются `User` (без `email_verified_at`) и `Profile`; письмо со ссылкой `{SITE_URL}/verify-email/{token}`; токен — подпись `django.core.signing` (срок 3 дня). Если email уже зарегистрирован: письмо «у вас уже есть аккаунт» вместо нового аккаунта; если не подтверждён — повторное письмо подтверждения. Ошибки: 400 `validation_error` (поля §5), 429.
Контакты для 16–17: `contacts` с непустыми значениями → 400, поле `contacts`, код `not_allowed_for_minors`.
Неподтверждённые аккаунты удаляются командой `purge_unverified` через 7 дней.

**POST `/api/auth/verify-email/`** — аноним. `{"token": "..."}` → `200 {"status": "verified"}`; 400 `invalid_token` (просрочен/подделан/уже использован — одинаковый ответ). Сессию не создаёт (пользователь идёт на `/login`).

**POST `/api/auth/resend-verification/`** — аноним. `{"email": "..."}` → всегда `202 {"status": "sent"}`.

### 3.3 Вход, выход
**POST `/api/auth/login/`** — аноним. `{"email": "jane@example.com", "password": "..."}` → `200` Own-профиль (§3.5) + cookie сессии (ключ сессии пересоздаётся).
Ошибки: 400 `invalid_credentials` (один текст для неверной пары); 403 `email_not_verified` и 403 `account_banned` — **только после** верного пароля (чтобы не раскрывать существование аккаунта); 403 `already_authenticated`; 429.
**POST `/api/auth/logout/`** — пользователь → `204`; сессия уничтожается.
Срок сессии — 14 дней (`SESSION_COOKIE_AGE`), без скользящего продления.

### 3.4 Пароль и email
| Метод | URL | Доступ | Тело | Ответ |
|---|---|---|---|---|
| POST | `/api/auth/password-reset/` | аноним (вошедшему тоже можно) | `{"email"}` | всегда `202 {"status":"sent"}`: одинаково для существующих, несуществующих, неподтверждённых и забаненных адресов; письмо уходит только существующему, подтверждённому и незабаненному пользователю |
| POST | `/api/auth/password-reset/confirm/` | аноним (вошедшему тоже можно) | `{"uid","token","new_password"}` | `200 {"status":"password_changed"}`; 400 `invalid_token` (одинаково для просроченной, подделанной и использованной ссылки, неизвестного uid, забаненного и неподтверждённого пользователя); слабый или негодный новый пароль — 400 `validation_error` по полю `new_password`, ссылка остаётся рабочей; все сессии пользователя удаляются; на почту уходит уведомление «Your password was changed» |
| POST | `/api/auth/password/change/` | пользователь | `{"old_password","new_password"}` | `204`; текущая сессия остаётся, остальные удаляются; 400 поле `old_password` код `incorrect`; новый пароль проверяется так же, как при регистрации (сила не ниже Medium, сходство с email и именем, частые пароли); уведомление «Your password was changed» на почту; новый пароль не может совпадать со старым (400 поле `new_password` код `same_as_old`) |
| POST | `/api/auth/email/change/` | пользователь | `{"new_email","password"}` | `202 {"status":"verification_sent"}`; 400 поле `password` код `incorrect`; адрес нормализуется (`strip` + нижний регистр) и пишется в `pending_email`; письмо со ссылкой на новый адрес, уведомление на старый. Если адрес занят или совпадает с текущим, ответ тот же (занятому адресу уходит письмо «адрес уже используется», `pending_email` не пишется) |
| POST | `/api/auth/email/change/confirm/` | аноним или пользователь | `{"token"}` | `200 {"status":"email_changed"}`: email меняется, `email_verified_at = now`, `pending_email` очищается, сессии остаются, на ПРЕЖНИЙ адрес уходит уведомление «Your email was changed»; любая проблема с токеном — 400 `invalid_token` |
| GET | `/api/auth/username-available/?username=janedoe` | аноним | — | `{"available": true}`; невалидный формат → `{"available": false, "reason": "invalid_format"}` |

**Токены (`django.core.signing`, без хранения в базе, `apps/users/tokens.py`).** Подтверждение почты: соль `users.verify-email`, 3 дня. Сброс пароля: соль `users.password-reset`, **1 час**, в токене uid, email и отпечаток хэша пароля, поэтому после смены пароля или email старые ссылки перестают работать; ссылка `{SITE_URL}/reset-password/{uid}/{token}` (`uid` — `urlsafe_base64(pk)`). Смена email: соль `users.confirm-email-change`, **3 дня**, в токене uid и новый адрес; применяется, только пока `pending_email` совпадает с ним (одноразовость; новый запрос отменяет прежнюю ссылку); ссылка `{SITE_URL}/confirm-email-change/{token}`. Ссылки пишутся в лог одной строкой `DEMO link:` при `DEBUG` или `DEMO_LOG_VERIFY_LINKS`. Письма отправляются синхронно; выравнивание времени ответа при реальной почте (для существующего и несуществующего адреса) — задача на потом.

**Логи.** Ошибки по `/api/auth/login/`, `/api/auth/register/`, `/api/auth/password-reset/`, `/api/auth/password/`, `/api/auth/email/`, `/api/me/` и `/api/conversations/` логируются без текста исключения (`PRIVATE_PATH_PREFIXES`): пароли, токены и адреса в журнал не попадают.

### 3.5 Свой профиль
**GET `/api/me/`** — пользователь → `200` Own-профиль:
```json
{
  "email": "jane@example.com", "email_verified": true, "pending_email": null,
  "username": "janedoe", "first_name": "Jane", "last_name": "Doe",
  "date_of_birth": "2002-03-14", "age": 24, "is_minor": false, "gender": "female",
  "country": "UZ", "country_label": "Uzbekistan", "region": "Tashkent", "city": "Tashkent",
  "status": "student", "status_label": "Student", "school": "", "university": "WIUT",
  "field": "computer_science", "field_label": "Computer Science", "year_level": "2nd year",
  "bio": "Building things.", "interests": ["ai"], "languages": ["english", "uzbek"], "goals": ["study_partners"],
  "contacts": {"telegram": "janedoe", "instagram": "", "whatsapp": "", "linkedin": "", "public_email": ""},
  "avatar_url": "/media/avatars/3f2a....webp",
  "privacy": {"show_location": true, "show_university": true, "show_contacts": false, "show_in_search": true, "show_join_date": true},
  "created_at": "2026-10-10T08:15:30Z"
}
```
**PATCH `/api/me/`** — владелец. Частичное обновление. Изменяемые: `first_name, last_name, gender, country, region, city, status, school, university, field, year_level, bio, interests, languages, goals, contacts`. Отклоняются (read-only, ответ 400 `read_only_field`, запрос не применяется целиком): `username, date_of_birth, email, email_verified, age, is_minor, is_banned, created_at, avatar_url, privacy, country_label, field_label, status_label`. Неизвестные ключи (например, `phone`, `field_other` — их нет) молча игнорируются. Значения `interests/languages/goals` проверяются по справочнику (`invalid_choice`), без повторов (`duplicate`) и в пределах лимитов 10/10/8 (`too_many`). → `200` Own-профиль.
**DELETE `/api/me/`** — владелец. `{"password": "..."}` → `204`; в одной транзакции удаляются пользователь и все его сессии, затем срабатывает точка расширения для файла аватара (`delete_account_files`, B4b); текущая сессия закрывается. Ошибка: 400 поле `password` код `incorrect`; сотрудник или суперпользователь (`is_staff`/`is_superuser`) удалить себя через API не может — 403; без входа — 401; лимит — `account_password`. **Каскад по коду:** `Profile`; `SavedProfile` (его закладки и закладки на него); `Conversation` (как `user_a`, `user_b` и `initiator`) вместе с `Message` у обеих сторон; `Block` в обе стороны и `Report` на него (`target`) — удаляются; `Report` от него (`reporter`), `Report.handled_by` и `Report.conversation` — `SET_NULL`; записи `LogEntry` админки удаляются. Сообщения удалённого человека у собеседника не сохраняются (решение заказчика).
**PUT `/api/me/avatar/`** — владелец, `multipart/form-data`, поле `file`. → `200 {"avatar_url": "/media/avatars/<uuid>.webp"}`; старый файл удаляется. Ошибки: 400 `invalid_image`, 413 `file_too_large`, 415 `unsupported_media_type`.
**DELETE `/api/me/avatar/`** → `204`.
**GET/PATCH `/api/me/privacy/`** — владелец; тело/ответ `{"show_location":…, "show_university":…, "show_contacts":…, "show_in_search":…, "show_join_date":…}` (в PATCH любые из пяти). Младше 18 лет: `show_contacts: true` → 400 `not_allowed_for_minors` (поле `show_contacts`), а в ответах `show_contacts` всегда `false`.

### 3.6 Публичные профили и поиск
Формат **Card** (поиск, избранное):
```json
{
  "username": "janedoe", "first_name": "Jane", "last_name": "Doe", "avatar_url": null,
  "field": "computer_science", "field_label": "Computer Science",
  "status": "student", "status_label": "Student",
  "city": "Tashkent", "country": "UZ", "country_label": "Uzbekistan",
  "bio": "Building things.", "interests": ["ai", "design"],
  "is_saved": false
}
```
`city`, `country`, `country_label` равны `null`, если у человека `show_location=false`. `school` в Card не передаётся. Всё, что показывается о человеке, решает `apps/profiles/visibility.py` (`ProfileVisibility`): правило меняется в одном месте.

**GET `/api/profiles/`** — пользователь. Параметры: `q` (≤100, иначе 400 `too_long`), `country`, `city`, `field`, `status`, `goal`, `language`, `page`, `page_size`.
- Фильтры — точное совпадение по кодам; неизвестный код → 400 `invalid_choice`. Пустое значение игнорируется. Реализовано без `django-filter` (`apps/profiles/search.py`).
- `q` разбивается на слова (до 8), каждое должно совпасть (AND) хотя бы с одним из: `first_name`, `last_name`, `username` (подстрока, без учёта регистра), название направления (поиск идёт по **меткам справочника**: слово ищется в метках, найденные коды сравниваются с `field`; частичное слово подходит: «comput» → Computer Science), `university` (только `show_university=true`), `city`/`region` (только `show_location=true`). Символы `%` и `_` ищутся как обычные.
- `country` применяется только к профилям с `show_location=true` (в интерфейсе фильтр стран пока скрыт флагом, API его поддерживает).
- `city` — код города из `cities` (неизвестный код → 400 `invalid_choice`). Город профиля (свободный текст `Profile.city`) сравнивается с **названием города из справочника** через `Lower(Trim(city))`: регистр и пробелы по краям не важны («samarkand», «Samarkand », «SAMARKAND» находятся одним фильтром). Только среди `show_location=true`. **Профили с городом «Other»** (любой город вне справочника, в том числе бывшие Khiva, Kokand, Margilan и др.: профили в базе не меняются) фильтром `city` **не находятся**: их можно найти только текстовым поиском `q` (по `city`/`region`, тоже только при `show_location=true`). Синонимы и альтернативные написания («Toshkent») не поддерживаются.
- Исключаются: сам пользователь, забаненные, неактивные, неподтверждённые, `show_in_search=false`.
- `page_size`: по умолчанию 12; больше 24 **обрезается до 24** (без ошибки); `0` и нечисловое значение — 12. Страница за пределами — 404 `not_found`.
- Сортировка — новые первыми (`-created_at`, затем `-id`). Throttle `search`: 60/min на пользователя.
- → пагинированный список Card.

**GET `/api/profiles/{username}/`** — пользователь. Формат **Public** (§6.1): Card + `region`, `school`, `university`, `year_level`, `languages`, `goals`, `contacts`, `joined` (`"2026-09"`). Скрытое поле — `null`, а не пропуск (`contacts` — объект из пяти ключей либо `null`). 404, если профиля нет / он забанен / неактивен / не подтвердил почту. Профиль со `show_in_search=false` и свой собственный открываются по прямой ссылке (как в legacy). Поля `blocked_by_me` и `conversation` появятся вместе с блокировками и диалогами (B6, B9); `is_saved` пока всегда `false`.
**GET `/api/saved/`** — пользователь → пагинированные Card (как в поиске: те же поля и правила приватности, `is_saved=true`). Новые закладки первыми. Забаненные, неактивные и неподтверждённые пропадают (и возвращаются после разбана); `show_in_search=false` закладку **не** скрывает.
**PUT `/api/saved/{username}/`** → `204`, идемпотентно (повтор уже сохранённого ничего не меняет и не проверяет лимит). Свой username — 400 `cannot_target_self`; нет такого, забанен, неактивен, не подтвердил почту или нет профиля — 404 `not_found`. Больше `SAVED_MAX` (200) видимых закладок — 409 `saved_limit_reached`. Проверка лимита и вставка идут в одной транзакции под блокировкой строки владельца, параллельные запросы лимит не обходят. Считаются только видимые закладки (как в списке: скрытые из списка нельзя было бы убрать).
**DELETE `/api/saved/{username}/`** → `204` всегда (даже если закладки не было и даже для недоступного или неизвестного username: убрать закладку можно всегда).
`is_saved` в Card (поиск) и Public считается по данным текущего пользователя: один запрос на страницу списка, один `exists()` в профиле; закладки других людей на него не влияют; у своего профиля — `false`.

### 3.7 Блокировки и жалобы
| Метод | URL | Доступ | Тело | Ответ |
|---|---|---|---|---|
| GET | `/api/blocks/` | пользователь | — | пагинированные мини-карточки `{username, first_name, last_name, avatar_url}` (только те, кого заблокировал я; новые первыми) |
| PUT | `/api/blocks/{username}/` | пользователь | — | `204`; идемпотентно; на себя — 400 `cannot_target_self`; нет такого, забанен или не подтвердил почту — 404; сверх лимита — 409 `blocks_limit_reached`. Заблокировать того, кто заблокировал вас, можно: ответ тот же |
| DELETE | `/api/blocks/{username}/` | пользователь | — | `204` всегда (идемпотентно, в том числе для недоступного человека) |
| POST | `/api/reports/` | пользователь | `{"username","reason","details","conversation_id"?}` | `201 {"status":"received"}`; дубль открытой жалобы — тоже `201` (без раскрытия; если в дубле есть `conversation_id`, он дописывается к открытой жалобе); на себя — 400 `cannot_target_self`; неизвестный человек — 404; `reason` не из справочника — 400 `invalid_choice`; `details` > 1000 — 400 `too_long`; `conversation_id` чужого диалога, диалога с другим человеком или неверный — 404 |

Лимиты запросов: блокировки (PUT и DELETE вместе) — 30 в час на пользователя (scope `block`); жалобы — 10 в сутки (scope `report`). Причины жалоб (`report_reasons`) и числа `limits.blocks_max`, `limits.details_max` приходят из `/api/meta/`. Тексты жалоб и сообщений не попадают в логи и трейсбеки: ошибки по `/api/reports/`, `/api/blocks/` и `/api/conversations/` логируются без текста исключения (`config/exceptions.py`).

**Действие блокировки.** Все проверки собраны в `apps/moderation/rules.py` (`are_blocked`, `exclude_blocked`, `hidden_by_me`, `blocked_pair` — подзапросы `Exists`, число SQL-запросов не зависит от числа блокировок). При блокировке в **любую** сторону: человека нет в `GET /api/profiles/` и `GET /api/saved/` (закладка остаётся в базе и возвращается после разблокировки), `GET /api/profiles/{username}/` и `PUT /api/saved/{username}/` отвечают 404, `POST /api/conversations/` — 404 («такого человека нет»: проверка стоит раньше «диалог уже есть»). Диалоги — §7.2.

**Жалоба.** Пожаловаться можно на любого человека с профилем и активным аккаунтом, в том числе на заблокировавшего вас и на забаненного (иначе ответ раскрыл бы блокировку или бан). Жалоба на диалог прикрепляет ссылку на диалог (не копию текста): суперпользователь открывает переписку в админке (только чтение).

### 3.8 Диалоги (запросы на переписку)
Формат **Conversation** (все поля всегда есть; ничего лишнего: нет email, даты рождения и т.п.):
```json
{
  "id": "6f1c2c0e-8d3e-4a6f-9d58-3a2a1d6c9f10",
  "other_user": {"username": "alex", "first_name": "Alex", "last_name": "Kim", "avatar_url": null, "field_label": "Design"},
  "status": "pending", "initiated_by_me": true,
  "last_message": {"body": "Hi! I saw your project...", "sender_is_me": true, "created_at": "2026-10-10T09:00:00Z"},
  "unread_count": 0, "last_message_at": "2026-10-10T09:00:00Z", "created_at": "2026-10-10T09:00:00Z"
}
```
Имя собеседника берётся через `ProfileVisibility.name()` (одно место, где можно изменить показ имён). `status` — с точки зрения зрителя: у **инициатора** `declined` всегда показывается как `pending` (отказ не сообщается). Чужой диалог, несуществующий UUID и диалог с недоступным собеседником (забанен, неактивен, не подтверждён) → 404. Данные при бане собеседника сохраняются.

| Метод | URL | Тело | Ответ |
|---|---|---|---|
| GET | `/api/conversations/?box=chats\|requests\|sent` | — | пагинированный список Conversation, порядок `-last_message_at`. `chats` (по умолчанию) — принятые; `requests` — входящие `pending`; `sent` — мои исходящие запросы (`pending` и `declined`, оба как `pending`). Что отклонил я сам, не показывается ни в одном `box`. Неизвестный `box` → 400 |
| POST | `/api/conversations/` | `{"username","body"}` | `201 {"conversation": {...}, "message": {...}}` — диалог `pending` и первое сообщение в одной транзакции |
| GET | `/api/conversations/{id}/` | — | Conversation (участник) |
| POST | `/api/conversations/{id}/accept/`, `/decline/` | — | `200` Conversation. Только получатель и только из `pending`, иначе 409 `invalid_state` (инициатору — всегда `invalid_state`, чтобы отказ оставался замаскированным; решение окончательное) |
| GET | `/api/conversations/summary/` | — | `{"unread_messages": 3, "pending_requests": 1}` (для бейджей, опрос раз в 30 с). Непрочитанные считаются только по принятым диалогам |

`POST /api/conversations/`: `body` после замены `\r\n → \n` и `strip` — 1…`request_max` (500) символов (400 `required` / `too_long`). Текст хранится как есть, без HTML-обработки. Правило «можно ли начать диалог» — одна функция `apps/messaging/rules.py: can_start_conversation(sender, target)` (сейчас: цель видима — активна, не забанена, почта подтверждена, есть профиль; не я сам; `show_in_search=false` не мешает; ограничений по возрасту нет — их добавлять в этой функции). Ошибки: 400 `validation_error`; 400 `cannot_target_self`; 404 `not_found` (цели нет, забанена, неактивна, не подтверждена); 409 `conversation_exists` (уже `accepted`; в теле `conversation_id`); 409 `request_pending` (вы уже отправляли запрос, в том числе отклонённый; `conversation_id`); 409 `incoming_request_exists` (цель уже прислала запрос — примите его; `conversation_id`); 403 `conversation_closed` (вы сами отклонили входящий запрос от этого человека); 409 `pending_requests_limit_reached`; 429 (лимит новых запросов в сутки). Гонка встречных запросов решается ограничением `UNIQUE(user_a, user_b)`: проигравший получает 409, не 500. **Лимит висящих (20):** считаются `pending` всегда, а `declined` — только `DECLINED_COUNTS_DAYS` (7) дней после `decided_at`; иначе освободившийся слот выдал бы отказ.

### 3.9 Сообщения
Формат **Message**:
```json
{"id": 1042, "sender_is_me": false, "body": "Hello!", "created_at": "2026-10-10T09:05:00Z", "seen_at": null}
```
| Метод | URL | Доступ | Описание |
|---|---|---|---|
| GET | `/api/conversations/{id}/messages/` | участник | Курсорная выдача по возрастанию `id`. Параметры: `limit` (по умолчанию 30, максимум 50; кривое или нулевое значение — 30), `before=<id>` (более старые), `after=<id>` (более новые — для опроса); кривой `before`/`after` → 400. Ответ: `{"results":[Message…], "has_more_older": true}`. Сообщения запроса в `pending` читают оба участника |
| POST | `/api/conversations/{id}/messages/` | участник по §7.3 | `{"body": "..."}` (1…`message_max` = 4000 после `strip`) → `201` Message. Ошибки: 400 `validation_error`; `accepted` — оба участника; `pending` — получатель 403 `accept_required`, инициатор 409 `request_pending`; `declined` — получатель 403 `conversation_closed` («You can't send messages to this user.»), **инициатор 409 `request_pending`** (маскирование); 429. Обновляет `last_message_at` |
| POST | `/api/conversations/{id}/read/` | участник | Помечает входящие `seen_at=now`, ответ `200 {"updated": 3}`. Только в `accepted`: в `pending`/`declined` ответ `{"updated": 0}` и ничего не помечается (иначе инициатор по `seen_at` узнал бы, что получатель открыл запрос до решения) |

### 3.10 Фронтовые маршруты, на которые ссылаются письма
`/verify-email/:token`, `/reset-password/:uid/:token`, `/confirm-email-change/:token`. Базовый адрес берётся из `SITE_URL`.

### 3.11 Пример: приватность в ответе
Пользователь `maria` (18+, `show_location=true`, `show_university=false`, `show_contacts=false`):
```json
{"username":"maria","first_name":"Maria","last_name":"S.","city":"Samarkand","country":"UZ","university":null,"contacts":null,"joined":"2026-09"}
```
(`university` и `contacts` — `null` независимо от того, пусты они или скрыты.)

### 3.12 Заметки по сообщениям
Опрос чата: открытый чат — `GET …/messages/?after=<last_id>` каждые 5 с (только при видимой вкладке); общий бейдж — `GET /conversations/summary/` раз в 30 с. Realtime — вне MVP.

### 3.13 Идемпотентность и повторы
PUT/DELETE избранного и блокировок идемпотентны. `POST …/messages/` не идемпотентен; фронтенд блокирует кнопку до ответа (исправление F-8 из ANALYSIS).

### 3.14 Django Admin (staff)
Модели: User (бан/разбан, сброс `email_verified_at`; действие «Ban» ставит `is_banned`, `banned_at` и удаляет сессии пользователя; колонка «Open reports» — число открытых жалоб на человека, один запрос с агрегатом, без N+1), Profile (просмотр, без DOB в списке), SavedProfile (только чтение). `Conversation`/`Message` — только чтение и только для суперпользователей (§1.7).

**Модерация (`apps/moderation`) — только суперпользователи** (обычный staff модуль не видит, права через `user_permissions` не помогают):
- `Report`: список сначала жалобы `underage` и `harassment`, затем остальные, внутри группы новые первыми; фильтры «priority» (urgent/other), `status`, `reason`; поиск по email и username цели и автора; колонка «Open on this person» — число открытых жалоб на ту же цель. Текст жалобы, автор, цель и причина **не редактируются**; меняются только `status` и `staff_note`, а `handled_by`/`handled_at` ставятся автоматически (при возврате в `open` очищаются). В карточке: число открытых жалоб на цель и список других жалоб на неё — только дата, причина и статус (без чужих текстов и авторов); ссылка на диалог (только чтение). Действия: «Mark dismissed», «Mark actioned», «Ban target user» (ставит `is_banned`/`banned_at` на цели, завершает её сессии, жалобы → `actioned`; суперпользователей не банит). Добавлять и удалять жалобы нельзя.
- `Block`: только чтение.
Просмотр жалоб не пишет `LogEntry`.

---

## 4. Роли и состояния аккаунта

| Состояние | Вход | API | Видим в поиске |
|---|---|---|---|
| Не подтверждён email | ❌ `email_not_verified` | нет сессии | нет |
| Активен | ✅ | ✅ | по `show_in_search` |
| Забанен | ❌ `account_banned` | ❌ 403 | нет; профиль → 404; диалоги скрыты у собеседников |
| Удалён | — | — | нет, данные удалены каскадом |

---

## 5. Правила валидации

Единые для API (сериализаторы) и БД (где возможно — CheckConstraint). Сообщения об ошибках — коды (`code`), тексты — во фронтенде.

| Поле | Правило | Код ошибки |
|---|---|---|
| email | валидный формат, ≤254, нормализация: `strip` + нижний регистр, уникален без учёта регистра | `invalid`, `taken` (при регистрации не раскрывается — см. §3.2) |
| password | ≥8 символов, ≤128; Django-валидаторы: не слишком похож на email/имя, не из списка распространённых, не только цифры; **сила не ниже Medium** (см. ниже) | `too_short`, `too_common`, `entirely_numeric`, `too_similar`, `too_weak` |
| username | `^[a-z][a-z0-9_]{2,29}$` (3–30, начинается с буквы, только строчные латинские, цифры, `_`); приводится к нижнему регистру; нет `__`; не из зарезервированных (`admin`, `api`, `me`, `settings`, `login`, `register`, `support`, `staff`, `networkit`, …) | `invalid_format`, `reserved`, `taken` |
| first_name / last_name | 1–60 после `strip`; только буквы Unicode, пробел, дефис, апостроф, точка; без `<`, `>`, управляющих символов | `required`, `too_long`, `invalid_characters` |
| date_of_birth | формат `YYYY-MM-DD`; не в будущем; возраст на дату регистрации **≥16** и ≤100 | `invalid`, `too_young`, `too_old` |
| gender | один из справочника | `invalid_choice` |
| country | код ISO из справочника | `invalid_choice` |
| region / city | `strip`; region ≤100; city 1–100 | `too_long`, `required` |
| status | `student` / `professional` | `invalid_choice` |
| school / year_level | ≤100 / ≤40 | `too_long` |
| university | свободный текст ≤120, без `<` `>` | `too_long`, `invalid_characters` |
| field | код справочника или `other` | `invalid_choice` |
| bio | ≤300 символов, переводы строк сохраняются (`\r\n`→`\n`) | `too_long` |
| interests / languages / goals | список кодов справочника, без дублей; максимум 10 / 10 / 8 | `invalid_choice`, `duplicate`, `too_many` |
| telegram | `^@?[A-Za-z0-9_]{5,32}$` → хранится без `@` | `invalid` |
| instagram | `^@?[A-Za-z0-9._]{1,30}$` → без `@` | `invalid` |
| whatsapp | международный номер `^\+[1-9][0-9]{6,14}$` | `invalid` |
| linkedin | URL `https://(www.)?linkedin.com/in/<slug>` или только slug; хранится нормализованным URL | `invalid` |
| public_email | валидный email ≤254 | `invalid` |
| contacts (любое) у 16–17 | не принимаются | `not_allowed_for_minors` |
| avatar | форматы **JPEG, PNG, WebP** — определяются по содержимому (Pillow), не по расширению и `Content-Type`; размер файла ≤5 МБ; размеры ≥128×128 и ≤4000×4000 пикселей; GIF/SVG/HEIC/прочее отклоняются. Обработка: проверка `Image.verify()`, исправление ориентации по EXIF, **удаление метаданных (EXIF/GPS)**, центрированная обрезка в квадрат, уменьшение до 512×512, сохранение WebP (quality ≈85), имя — случайный UUID | `invalid_image`, `file_too_large`, `unsupported_media_type`, `image_too_small`, `image_too_large` |
| message.body | после `strip` 1–4000 символов; запрос (первое сообщение) 1–500 | `required`, `too_long` |
| report.reason / details | reason из справочника; details ≤1000 | `invalid_choice`, `too_long` |
| q (поиск) | ≤100 символов; `%` и `_` экранируются; пусто = без фильтра | `too_long` |
| page_size | 1–24 | `invalid` |
| accepted_terms | `true` обязательно при регистрации | `required` |

Все строки перед проверкой проходят `strip`; значения HTML не санитизируются на сервере (хранятся как текст) — безопасность вывода обеспечивает React (никакого `dangerouslySetInnerHTML`) и ограничения формата выше.

---

**Сила пароля (Weak / Medium / Strong).** Слабый пароль отклоняется, принимаются Medium и Strong. Формула единая для сервера (`apps/users/password_strength.py`, валидатор `apps.users.password_validators.PasswordStrengthValidator` в `AUTH_PASSWORD_VALIDATORS`) и frontend (`frontend/src/lib/passwordStrength.js`). Длина считается в кодовых точках Unicode; классы символов: строчные, заглавные, цифры, прочие (пробел, знаки, иероглифы, эмодзи).
- **Weak:** длина < 8, или классов < 2, или разных символов < 4 (`aaaaaaa1` — Weak).
- **Strong:** (длина ≥ 12 и классов ≥ 3) или (длина ≥ 16 и классов ≥ 2).
- **Medium:** всё остальное.
Внутри Django код ошибки `password_too_weak`, клиенту приходит `too_weak` (как `password_too_short` → `too_short`). Текст ошибки не содержит пароля. Таблица проверочных паролей: `backend/apps/users/tests/password_cases.json` (её читают тесты Django и проверка frontend).

## 6. Правила приватности

### 6.1 Какие поля в каких представлениях

| Поле | Own (`/me/`) | Public (`/profiles/{username}/`) | Card (поиск, избранное) | Мини-карточка (диалог, блокировки) |
|---|---|---|---|---|
| email, pending_email, email_verified | ✅ | ❌ никогда | ❌ | ❌ |
| date_of_birth, age, is_minor, gender | ✅ | ❌ никогда | ❌ | ❌ |
| is_banned, id, служебные поля | ❌ (бан → 403) | ❌ | ❌ | ❌ |
| privacy (флаги) | ✅ | ❌ (флаги чужих не видны) | ❌ | ❌ |
| username, first_name, last_name, avatar_url | ✅ | ✅ | ✅ | ✅ |
| field/field_label, status, bio, interests | ✅ | ✅ | ✅ | field_label |
| school, year_level, languages, goals | ✅ | ✅ | ❌ | ❌ |
| city, region, country | ✅ | если `show_location` | city, country — если `show_location` | ❌ |
| university | ✅ | если `show_university` | ❌ | ❌ |
| contacts | ✅ | если `show_contacts` **и** пользователю ≥18 | ❌ | ❌ |
| created_at → `joined` (месяц-год) | ✅ | если `show_join_date` | ❌ | ❌ |

**Отступление для несовершеннолетних (младше 18): `school` не отдаётся ни в Card, ни в Public.** В Public поле приходит как `null` (в Card его нет вообще). В таблице выше `school` публичен, но школа несовершеннолетнего вместе с именем и городом позволяет найти его в реальной жизни, поэтому показ закрыт независимо от настроек. Решение принимает `ProfileVisibility.school()`; там же будет меняться правило показа имени несовершеннолетних (сейчас — полное имя, см. вопросы по безопасности).

Скрытое поле возвращается как `null` (или `contacts: null`), а не опускается и не заменяется пустой строкой — клиент не может отличить «скрыто» от «пусто».
Для 16–17: `contacts` в Public всегда `null`, `show_contacts` принудительно `false`. При наступлении 18 лет флаг **остаётся `false`** — открыть контакты может только сам пользователь.

### 6.2 Умолчания (решение 2)
`show_location=true` (город виден), `show_university=true`, `show_contacts=false`, `show_in_search=true`, `show_join_date=true`. Умолчания для 16–17 те же, кроме контактов (недоступны вообще) — Q-2.

### 6.3 Скрытие в поиске и фильтрах
Запрос `GET /profiles/` исключает: себя; забаненных; неподтверждённых; тех, у кого `show_in_search=false`; всех, с кем есть блокировка **в любую сторону**.
Поиск и фильтры **не используют скрытые данные** (исправление F-15):
- `q` ищет по `first_name`, `last_name`, `username`, названию направления (`field_label`); по `university` — **только** среди профилей с `show_university=true`;
- фильтры `country`, а также поиск по `city`/`region` применяются **только** к профилям с `show_location=true`;
- `goal`, `language`, `field`, `status` — публичные поля, фильтруются всегда.
Тест обязателен: профиль с `show_university=false` не находится по запросу своего вуза; профиль со `show_location=false` не находится фильтром по своей стране.

### 6.4 Прочее
- Прямой доступ к профилю по `username` не зависит от `show_in_search` (как в legacy), но зависит от бана и блокировок (404).
- Избранное сохраняет доступ к профилю, даже если цель позже включила `show_in_search=false`.
- Файлы аватаров публичны по неугадываемому URL; при удалении аккаунта/замене файл удаляется с диска.
- Телефон не собирается и в модели отсутствует.

---

## 7. Сообщения: статусы и правила

### 7.1 Состояния диалога
| Статус (поле) | Смысл | Кто может писать |
|---|---|---|
| `pending` | инициатор отправил запрос с первым сообщением, ответа нет | никто, кроме отправленного первого сообщения: инициатор — нет (409 `request_pending`), получатель — нет, пока не примет (403 `accept_required`) |
| `accepted` | получатель принял | оба участника |
| `declined` | получатель отклонил | никто (получатель — 403 `conversation_closed`, инициатор — 409 `request_pending`: отказ ему не сообщается) |
| *заблокирован* (вычисляется: есть `Block` в любую сторону) | один из участников заблокировал другого | никто (403 `conversation_closed`) |

### 7.2 Что видит каждый (маскирование)
- **Получатель:** `pending` → вкладка `requests`; после `decline` — диалог из списков исчезает.
- **Инициатор:** `pending` и `declined` показываются одинаково как `pending` («Request sent»). Это защита от навязчивости: отказ не сообщается. Повторный запрос тому же человеку после отказа невозможен (409 `request_pending`).
- **Заблокированный:** диалог остаётся в списке без изменений (в том числе непрочитанные и `status`), историю открыть можно, но отправка → 403 `conversation_closed` (нейтральный текст, о блокировке ничего не сказано); `accept`/`decline` → тоже 403 `conversation_closed`. Профиль заблокировавшего недоступен (404) и в поиске его нет. Счётчик `pending_requests` в `summary` не учитывает запросы от/к заблокированному в обе стороны (в списке `requests` запрос остаётся).
- **Блокирующий:** диалог исчезает из всех `box`, из `summary` и по прямой ссылке (404); список заблокированных — `GET /blocks/`. После `DELETE /blocks/{username}/` диалог возвращается в прежнем статусе (сама блокировка не меняет `status`, `unread`, закладки).
- Забаненный собеседник: диалог скрыт у другой стороны, сообщения сохраняются.

### 7.3 Таблица «кто и что может отправить»
| Ситуация | Инициатор | Получатель |
|---|---|---|
| Нет диалога | `POST /conversations/` → создаётся `pending` + первое сообщение | — |
| `pending` | 409 `request_pending` | `accept` / `decline` / блок / жалоба; сообщение → 403 `accept_required` |
| `accepted` | ✅ | ✅ |
| `declined` | 409 `request_pending` (маскирование: неотличимо от `pending`) | 403 `conversation_closed` (нейтральный текст) |
| Блокировка | заблокированному — 403 `conversation_closed`; блокирующему диалог недоступен (404, §7.2) | то же |

### 7.4 Остальные правила
- Одна пара пользователей — максимум один диалог (UNIQUE `user_a<user_b`).
- Лимиты: не более 20 одновременно висящих исходящих запросов (`pending` и `declined` не старше 7 дней; 409 `pending_requests_limit_reached`), 10 новых запросов в сутки, 30 сообщений в минуту и 500 в сутки (§3.0).
- Прочитанность: `seen_at` ставит получатель через `read`; счётчик `unread_count` считается только по принятым диалогам, запросы — отдельным счётчиком `pending_requests`.
- Ограничения возраста между взрослыми и 16–17 — Q-1 (рекомендуется решить до реализации §7).
- Удаление аккаунта удаляет его диалоги и сообщения у обеих сторон (каскад, как в legacy); альтернатива — Q-8.

---

## 8. Критерии приёмки по этапам

Нумерация — шаги из `ANALYSIS.md §H.4`; шаги 5 и 9 разбиты на подшаги, добавлены блокировки/запросы по принятым решениям. Проверка «руками» = команда или действие в браузере; автотесты (`python manage.py test`) должны быть зелёными на каждом этапе.

| Этап | Что сделано | Как проверить руками |
|---|---|---|
| **1. Гигиена репозитория** | корневой `.gitignore`; `__pycache__` убран из git; `.env`/`.env.example`; `django-environ`; PostgreSQL в settings; `users` и `rest_framework` в `INSTALLED_APPS` | `git status` не показывает `.pyc`, `.env`, `networkit/`, `node_modules/`; в репозитории нет `SECRET_KEY`; `python manage.py check` без ошибок; `python manage.py dbshell` подключается к PostgreSQL; без `.env` проект не стартует с понятной ошибкой |
| **2. Кастомный User** | `users.User` (вход по email), первая миграция, регистрация в Admin | чистая БД → `migrate` проходит; `createsuperuser` спрашивает email; вход в `/admin/`; два пользователя с `A@x.com` и `a@x.com` — второй отвергнут |
| **3. Profile и справочники** | модели `Profile`, `SavedProfile`, `Block`, `Report`; `choices.py`; Admin | через Admin создаётся профиль; нарушение constraint (username с заглавной, `bio` >300 при `full_clean`) отклоняется; `Block` на себя невозможен |
| **4. Auth API + /me/** | CSRF, регистрация, подтверждение email (письмо в консоль), вход/выход, `/me/` GET/PATCH, формат ошибок, throttling | регистрация → ссылка из консоли → `verify-email` → вход; вход до подтверждения → 403 `email_not_verified`; PATCH `is_banned` игнорируется/400; POST без `X-CSRFToken` → 403 `csrf_failed`; регистрация 15 лет → `too_young`; 6 неверных входов за минуту → 429; тесты прав и приватности зелёные |
| **5a. Каркас фронтенда** | Vite-прокси `/api`, роутер, `apiClient` (CSRF), `AuthContext`, тема, `texts`, токены и базовые `ui/` | `npm run dev`: страница получает cookie `csrftoken`; `GET /api/me/` анонимом → состояние «anonymous»; переключение темы system/light/dark без вспышки; `npm run build` и `npm run lint` без ошибок |
| **5b. Страницы Landing/Login/Register** | лендинг, форма входа, мастер из 8 шагов, экраны verify/reset | регистрация целиком из браузера; ошибки сервера показываются у нужных полей; 16–17: поля контактов недоступны; адаптив 360/768/1280 px |
| **6. Справочники, редактирование профиля, аватар** | `/meta/`, `EditProfilePage`, загрузка/удаление аватара | форма заполняется сохранёнными значениями; редактируются интересы/языки/цели/год/направление (+Other); загрузка PNG 6 МБ → отказ; SVG, переименованный в `.png` → отказ; в сохранённом файле нет EXIF; замена аватара удаляет старый файл с диска |
| **7. Поиск и публичный профиль** | `/profiles/`, `/profiles/{username}/`, `DiscoverPage`, `/u/:username`; фильтры в URL | скрытый вуз/страна не находятся (тест F-15); `page_size=1000` → ограничено 24; свой профиль в выдаче отсутствует; ссылка `/u/janedoe` открывается напрямую и работает «Назад»; в JSON нет `email`, `date_of_birth`, `is_banned` |
| **8. Избранное** | `/saved/`, закладка на карточке и странице профиля | добавление/удаление идемпотентно; забаненный пропадает из списка; закладка на себя → 400 |
| **9a. Запросы на переписку** | модели/endpoints Conversation/Message, state machine §7 | пользователь A шлёт запрос B; A второй раз → 409 `request_pending`; B пишет до accept → 403 `accept_required`; B accept → оба пишут; decline → A видит `pending`, написать нельзя; чужой диалог по UUID → 404 |
| **9b. Блокировка и интерфейс чата** | `/blocks/`, `MessagesPage` (вкладки Chats/Requests/Sent), опрос | блок: профиль заблокировавшего → 404, поиск не показывает, отправка → 403 `conversation_closed`; разблок возвращает диалог; бейдж обновляется в течение 30 с; двойной Enter не создаёт дубль |
| **10. Настройки** | приватность, смена пароля/email, сброс пароля, удаление аккаунта | флаги сохраняются и **подгружаются при открытии** (регресс F-1); смена пароля сбрасывает другие сессии; сброс пароля по ссылке из письма; удаление аккаунта удаляет файл аватара и диалоги; 16–17 не может включить контакты |
| **11. Жалобы и модерация** | `POST /reports/`, Admin для Report, бан | жалоба → видна в Admin; повторная открытая жалоба не плодится; бан в Admin → у пользователя 403 `account_banned` сразу (сессии удалены), профиль 404, из поиска пропал |
| **12. Адаптив, тёмная тема, a11y, безопасность** | чек-лист DESIGN_SYSTEM, CSP, cookie-флаги, throttling | Lighthouse a11y ≥90; всё доступно с клавиатуры; `prefers-color-scheme` учитывается; нет горизонтального скролла на 360 px; в продакшн-настройках `DEBUG=False`, cookie `Secure`, `python manage.py check --deploy` без критичных предупреждений |
| **13. Деплой** | VPS: PostgreSQL, Gunicorn, Nginx, HTTPS, статика/медиа, бэкап, `purge_unverified` по cron | сайт открывается по HTTPS; HTTP → редирект; регистрация с реальным письмом; `/media/avatars/...` отдаёт Nginx; перезагрузка сервера поднимает сервисы; восстановление из бэкапа проверено |

---

## 9. Вопросы ко мне

Помечены приоритетом: **[блок]** — нужно решить до начала указанного этапа.

1. **Q-1 [блок этапа 9]. Взрослые ↔ 16–17.** Разрешаем ли взрослому отправлять запрос на переписку 16–17-летнему? Рекомендация: запретить запросы от 18+ к 16–17 (и наоборот), если нет согласованного исключения. Показывать ли возраст/признак «<18» собеседнику?
2. **Q-2 [блок этапа 3]. Умолчания для 16–17:** оставлять `show_in_search=true`? Рекомендация: для 16–17 показывать в поиске только имя + первую букву фамилии и скрывать `region`, `school`. Подходит ли?
3. **Q-3. Справочники:** точный состав стран (63 из legacy + Kyrgyzstan, Tajikistan, Turkmenistan — или полный ISO-список?), расширение `languages` (tajik, kazakh, kyrgyz, karakalpak…), `interests`; кто даёт английские метки (сейчас — из legacy).
4. **Q-4. WhatsApp:** это номер телефона (решение 3 — «телефон не собираем»). Оставлять поле как публичный контакт (скрыт по умолчанию, недоступен 16–17) или убрать?
5. **Q-5. Username:** сейчас неизменяем (в legacy можно было менять, что ломает ссылки). Достаточно или нужна смена раз в 30 дней?
6. **Q-6. Пароль:** минимум 8 (как в legacy) или 10–12?
7. **Q-7. Staff и приватность:** разрешить ли staff читать тексты сообщений? Рекомендация: нет; при жалобе — прикреплять к ней последние N сообщений автоматически (нужна согласованная формулировка в политике).
8. **Q-8. Удаление аккаунта:** сообщения удаляются у обеих сторон (как в legacy) или сохраняются у собеседника с пометкой «Deleted user»?
9. **Q-9. Отказ в запросе:** маскировать отказ как «pending» для инициатора (рекомендую) или показывать честный статус «declined»? Повтор запроса после отказа — навсегда запрещён или через N дней?
10. **Q-10. Условия и политика:** нужен ли `accepted_terms` и страницы Terms/Privacy в MVP (сейчас пустые ссылки в legacy)? Кто пишет тексты, на каком языке?
11. **Q-11. Срок сессии** 14 дней без продления — приемлемо? Нужна ли галка «Remember me»?
12. **Q-12. Хранилище лимитов throttling:** без Redis используем кэш в БД (DatabaseCache) — подходит для одного VPS (ARCHITECTURE §9). Согласен?
13. **Q-13. Профили неподтверждённых** удаляются через 7 дней — устраивает?
14. **Q-14. Публичный профиль для не вошедших:** сейчас нужен вход для просмотра любых профилей (как legacy). Нужен ли публичный SEO-просмотр профиля (с урезанным набором полей)? Рекомендация: вне MVP.
