# NetworkIt — анализ legacy-сайта перед переносом на Django + DRF + React

Источник анализа: `networkit-backend/` (только чтение). Прочитано полностью: `README.md`, `supabase/migrations/0001_init.sql` (470 строк), `supabase/functions/delete-account/index.ts` (59), `web/app.js` (1083), `web/index.html` (4587: CSS 13–3973, разметка 3976–4580, скрипты 4582–4585), `web/config.js`, `web/config.example.js`.
Код не запускался, пакеты не ставились. Всё, что требует запуска, помечено **«нужна проверка в рантайме»**. Ссылки вида `app.js:361` — файл:строка.

Короткий словарь Supabase (для тебя):
- **RLS (Row Level Security)** — правила в Postgres «какие строки таблицы видит/меняет пользователь». Заменяются в Django на `permissions` + `get_queryset()` в DRF.
- **`auth.uid()`** — id текущего пользователя из JWT-токена. В DRF это `request.user.id`.
- **SECURITY DEFINER-функция** — SQL-функция, которая работает с правами владельца и обходит RLS. Здесь через них отдаются «замаскированные» чужие профили. В DRF это сериализатор, который сам решает, какие поля отдать.
- **anon key** — публичный ключ, зашитый в браузер. Сам по себе не секрет; безопасность держится только на RLS.
- **Edge Function** — серверная функция (Deno/TypeScript), здесь одна: `delete-account`.

---

## A. Обзор: части системы и как они связаны

```
Браузер (index.html + app.js + config.js, чистый JS, без сборки)
  │  CDN: supabase-js@2, lucide@1.17.0, Google Fonts
  ├─ supabase.auth.*            → Supabase Auth (email+пароль, Google OAuth, сброс пароля)
  ├─ supabase.from('таблица')   → PostgREST: прямые запросы к таблицам, защита = RLS
  ├─ supabase.rpc('функция')    → SQL-функции (маскирование приватности, поиск, список чатов)
  ├─ supabase.storage           → бакет avatars (публичное чтение)
  ├─ supabase.channel(...)      → Realtime: push новых сообщений
  └─ supabase.functions.invoke  → Edge Function delete-account (service_role)
Деплой: статика на Vercel, root = web/ (README:63–64). vercel.json — не найден.
```

Ключевые факты:
- **Нет своего сервера.** Вся «бэкенд-логика» — это политики RLS, 8 SQL-функций, 3 триггера и одна Edge Function. Всё остальное (валидация, ветвление регистрации, проверка бана) — в браузерном JS, то есть **не защищено**.
- **Одностраничное приложение без роутера:** «страницы» (`page-landing/login/register/app`) и «разделы» (`sec-*`) — это `display:none/block`. URL не меняется, кнопка «Назад» не работает, `location.search/hash` нигде не читается.
- **Рендер — строками в `innerHTML`** с inline-обработчиками (`onclick="viewProfile('…')"`). Это источник XSS (раздел F).
- Старый прототип на localStorage в репозитории отсутствует (только упоминается в README).

---

## B. Карта функций

Условные обозначения: ✅ реализовано и достижимо, ⚠️ реализовано, но сломано/неполно, 🟡 заглушка, ⚫ мёртвый код, ❌ нет.

| Функция | Экран / блок HTML | Функции в app.js | Таблица / RPC | Статус |
|---|---|---|---|---|
| Лендинг, FAQ, статистика | `page-landing` (4014–4140), `#faq-list` | `renderLanding` (142), `updateHeroStats` (150), `initCanvas` (1024) | RPC `get_landing_stats` | ✅ (FAQ `max-height:180px` может обрезать, index.html:1014) |
| Регистрация email (8 шагов) | `page-register` (4179), `#reg-card` | `initReg`, `renderReg`, `buildReg`, `collectR`, `rNext/rBack/rFinish` (210–344), `pwdStr` (675) | `auth.signUp`, RPC `is_username_available`, INSERT `profiles` (+триггер → `privacy_settings`) | ⚠️ при включённом подтверждении почты профиль не создаётся (F-3) |
| Вход Google | кнопка `.socbtn` (4150) | `loginWithGoogle` (160), ветка в init (1056–1064) | `auth.signInWithOAuth` | ⚠️ (нужна настройка в Dashboard; новый пользователь → шаг регистрации) |
| Вход email | `page-login` (4143) | `doLogin` (164), `doLogout` (184) | `auth.signInWithPassword`, SELECT `profiles` | ⚠️ любая ошибка = «Incorrect email or password» (в т.ч. «email не подтверждён») |
| Сброс пароля | модалка «Reset password» | `forgotModal` (189), `sendReset` (194) | `auth.resetPasswordForEmail` | ⚠️ **нет экрана ввода нового пароля** (F-12) |
| Поиск / Discover | `sec-discover` (4234) | `runSearch` (398), `popFilters` (389), `debSearch` (438), `goP`, `clearFilters`, `toggleFilters` | RPC `search_profiles` | ✅ с оговорками (F-9, F-18) |
| История поиска | дропдаун `#search-history-dropdown` | `saveSearchHistory`… (941–963) | localStorage | ✅ (innerHTML + inline onclick, только свои данные) |
| Чужой профиль | `sec-vp` (4273) | `viewProfile` (449) | RPC `get_profile_card` | ✅, но XSS; кнопка «Report» сломана |
| Жалоба на профиль | кнопка в `viewProfile` (501) | `reportUser`/`subReport` — **закомментированы** (507–519) | INSERT `reports` | ❌ ReferenceError при клике (F-6) |
| Мой профиль | `sec-profile` (4280), `#mp-cont` | `renderMyProfile` — **закомментирована** (522–571), но вызывается в 361, 382, 595, 603, 625, 658 | — | ❌ **ReferenceError, раздел пуст, bootApp обрывается** (F-1) |
| Редактирование профиля | `sec-edit-profile` (4292) | `popEP` (574), `saveProfile` (606), `uploadAv` (582), `removeAv` (598) | UPDATE `profiles`, Storage `avatars` | ⚠️ форма не заполняется (F-1), затирает поля; интересы/языки/цели/год не редактируются (F-14) |
| Настройки: аккаунт | `st-acc` (4381) | `popStSettings` (635), `saveStAcc` (641) | UPDATE `profiles` | ⚠️ имя из одного слова нарушает CHECK last_name (F-17) |
| Настройки: приватность | `st-prv` (4389) | `loadPrivToggles` (661), `savePrivacy` (666) | UPDATE `privacy_settings` | ⚠️ **тумблеры не загружаются, сохранение затирает настройки** (F-1) |
| Смена пароля / email | `st-sec` (4423) | `changePass` (688), `changeEmail` (703) | `auth.signInWithPassword` + `updateUser` | ✅ (для Google-аккаунтов без пароля — не работает) |
| Удаление аккаунта | `st-del` (4448), модалка | `confirmDeleteAcc` (716), `deleteMyAcc` (721) | Edge Function `delete-account` | ⚠️ вероятно блокируется CORS, файлы Storage остаются (F-4) |
| Избранное | кнопка-закладка в карточке, `sec-saved` (4572) | `toggleSave` (755), `renderSaved` (772), `loadSavedIds` (107) | `saved_profiles`, RPC `get_identities` | ✅ (закладки нет на странице профиля) |
| Личные сообщения | `sec-messages` (4500) | `startChat`, `openChat`, `ensureConversation`, `renderConvList`, `renderMessages`, `sendMessage`, `markSeen`, `updateMsgBadge`, `subscribeMessages` (799–939) | `conversations`, `messages`, RPC `list_conversations`, `get_identities`, Realtime | ✅ с багами (F-8, F-16) |
| Экспорт «PDF» | кнопка в «My profile» | `exportProfilePDF` (972) | — | ⚠️ это HTML + `window.print()`; в HTML вставляются данные без экранирования (свои) |
| Ссылка на профиль | кнопка «Share profile» | `shareProfile` (966) | — | ⚠️ ссылка `?profile=…` **никем не читается** (F-14) |
| Тёмная тема | кнопки в nav и sidebar | `toggleTheme`, `applyTheme` (1006–1021) | localStorage `nk_theme` | ✅ |
| Уведомления | `sec-notifications` (4562), `#notif-badge` | `markAllRead` (736) — заглушка | нет | 🟡 скрыто в `bootApp` (357) |
| Админка | `sec-admin` (4463) | `loadAdmUsers` (735) — заглушка | нет (`is_admin` в таблице) | 🟡 скрыто (`sn-admin` display:none) |
| Онлайн-статус, «похожие люди», completeness, onboarding | только CSS (2914–3293, 3072–3102) | — | — | ⚫ мёртвый CSS без разметки и JS |
| `previewUser` (129), `me()` (86), `#login-btn`, `#ep-msg`, `#ep-save-btn`, `#suggest-section`, `.btn-white`-дубли | — | — | — | ⚫ не используются |

Расхождения id/функций HTML↔JS (проверено скриптом-сверкой): все `getElementById` в `app.js` находят элемент, все inline-обработчики HTML имеют функцию. Исключения: `renderMyProfile`, `reportUser` (в JS закомментированы, см. выше); поле `#ep-yr` есть в HTML, но не читается/не пишется JS; классы `.pb`/`.plb` (регистрация) вообще не имеют CSS, а `pwdStr` ставит классы `w/m/s`, тогда как CSS знает `.weak/.medium/.strong` (index.html:1527–1540) — индикатор силы пароля **не стилизован нигде**.

---

## C. Модель данных

### C.1 Таблицы (0001_init.sql)

**profiles** (26–56) — 1:1 с `auth.users`, `id uuid PK → auth.users ON DELETE CASCADE`.
| Поле | Тип / ограничение |
|---|---|
| username | citext NOT NULL UNIQUE (**без CHECK на длину/символы**) |
| first_name, last_name | text NOT NULL, CHECK длина 1–60 |
| date_of_birth | date, nullable |
| gender, country, region, city | text |
| status | text CHECK IN ('Student','Professional') |
| school, university, field, year_level | text |
| bio | text CHECK ≤ 300 |
| interests, languages, goals | text[] NOT NULL DEFAULT '{}' (без лимита размера) |
| phone | text — «приватный», нигде не отдаётся |
| telegram, instagram, whatsapp, linkedin, public_email | text |
| avatar_url | text (любая строка) |
| is_admin, is_banned | boolean DEFAULT false |
| created_at, updated_at | timestamptz; триггер `set_updated_at` (62–71) |
Индексы: `field`, `country`, `status` (58–60). Индекса под поиск `ILIKE '%…%'` нет.

**privacy_settings** (96–103) — PK=`profile_id`; `show_location/university/socials/in_search/join_date`, все DEFAULT true. Создаётся триггером `handle_new_profile` (118–128, security definer).

**saved_profiles** (133–139) — PK(user_id, saved_profile_id), CHECK user≠saved.

**conversations** (153–161) — `user_a`, `user_b`, CHECK `user_a < user_b`, UNIQUE пара, `last_message_at`. Клиент обязан сам отсортировать пару (`pairKey`, app.js:805). Комментарий в SQL ссылается на несуществующий `supabase-client.js: startConversation()`.

**messages** (171–178) — `conversation_id`, `sender_id`, `body` CHECK 1–4000, `created_at`, `seen_at`. Индекс (conversation_id, created_at). Триггеры: `guard_message_seen_update` (219–233) — менять можно только `seen_at`; `bump_conversation_last_message` (235–244).

**reports** (254–262) — `reporter_id` (SET NULL), `target_id` (CASCADE), `reason`, `details` (без лимитов), `status` ('open','dismissed','actioned'). Читать никто не может (нет SELECT-политики).

### C.2 Политики RLS
| Таблица | Политика | Суть |
|---|---|---|
| profiles | select_own / insert_own / update_own | только своя строка; **update без ограничения колонок** (86–87) |
| privacy_settings | select/insert/update own | своя строка |
| saved_profiles | `for all` own | своя строка |
| conversations | select/insert participant | участник; insert разрешён с **любым** вторым участником |
| messages | select/insert participant; update seen by recipient | участник; отправитель = `auth.uid()` |
| reports | insert own | reporter = `auth.uid()` |
| storage.objects (avatars) | public read; insert/update/delete только в папке `<uid>/` | нет лимитов размера/типа |

### C.3 SQL-функции
- `get_identities(uuid[])` (284) — карточка 1..N людей, маскирует город/страну по `show_location`; **не проверяет бан и show_in_search**.
- `get_profile_card(citext)` (306) — полный профиль по username, маскирует location/university/socials/join_date.
- `search_profiles(...)` (341) — фильтры, страницы, `count(*) over()`; исключает себя, забаненных, админов, `show_in_search=false`. **`p_page_size` не ограничен.**
- `is_username_available` (389), `get_landing_stats` (400), `list_conversations` (416, не definer, использует RLS).
- Все `grant execute … to authenticated` (+ anon для двух последних). `REVOKE … FROM PUBLIC` нигде нет (F-19).

### C.4 Эквивалент в Django (предложение)

Приложения: **`users`** (учётка), **`profiles`** (профиль, приватность, избранное, жалобы), **`messaging`** (диалоги и сообщения).

```python
# users/models.py — своя модель пользователя (делать ДО первой миграции!)
class User(AbstractUser):            # вход по email: USERNAME_FIELD = "email"
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)   # is_admin → is_staff/is_superuser
    # Django сам хранит хэш пароля; телефон — в Profile

# profiles/models.py
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    username = models.CharField(max_length=30, unique=True,
                                validators=[RegexValidator(r"^[a-z0-9_]{3,30}$")])  # lowercase
    first_name = models.CharField(max_length=60); last_name = models.CharField(max_length=60, blank=True)
    date_of_birth = models.DateField()        # + проверка возраста в serializer
    gender = models.CharField(max_length=20, blank=True, choices=...)
    country = models.CharField(max_length=2/…, db_index=True)  # код страны, не свободный текст
    region = models.CharField(max_length=100, blank=True); city = models.CharField(max_length=100)
    status = models.CharField(max_length=12, choices=[("student","Student"),("professional","Professional")])
    school/university = CharField(blank=True); field = CharField(db_index=True); year_level = CharField(blank=True)
    bio = models.TextField(max_length=300, blank=True)
    interests/languages/goals = ArrayField(CharField(...), default=list, size=…)  # PostgreSQL
    phone = CharField(max_length=20)          # приватно: НЕ входит ни в один публичный serializer
    telegram/instagram/whatsapp/linkedin = CharField(blank=True); public_email = EmailField(blank=True)
    avatar = models.ImageField(upload_to="avatars/%Y/")   # нужен Pillow
    created_at, updated_at

class PrivacySettings(models.Model):          # или 5 полей прямо в Profile — проще для MVP
    profile = OneToOneField(Profile, primary_key=True, ...)
    show_location, show_university, show_socials, show_in_search, show_join_date = BooleanField(default=...)

class SavedProfile(models.Model):             # избранное
    owner = FK(Profile); saved = FK(Profile); created_at
    class Meta: unique_together; constraints=[CheckConstraint(owner != saved)]

class Report(models.Model): reporter(FK null), target(FK), reason(choices), details(max 1000), status, created_at

# messaging/models.py
class Conversation(models.Model):
    user_a = FK(User); user_b = FK(User); last_message_at; created_at
    class Meta: constraints=[CheckConstraint(user_a_id < user_b_id), UniqueConstraint(user_a, user_b)]
class Message(models.Model):
    conversation = FK; sender = FK(User); body = TextField(max 4000); created_at; seen_at(null)
    class Meta: indexes=[Index(fields=["conversation","created_at"])]
```
Соответствие механизмов:
| Supabase | Django/DRF |
|---|---|
| RLS «только своя строка» | `get_queryset()` с фильтром + `IsAuthenticated`, `IsOwner` |
| SECURITY DEFINER-маскирование | `PublicProfileSerializer` (выбирает поля по `privacy`) — **телефон, DOB, is_banned туда не попадают** |
| Триггер `handle_new_profile` | создание `PrivacySettings` в `serializer.create()` / сигнал `post_save` |
| Триггер `set_updated_at` | `auto_now=True` |
| Триггер `guard_message_seen_update` | отдельный endpoint «отметить прочитанным» (меняет только `seen_at`) |
| Триггер `bump_conversation_last_message` | обновление в `MessageViewSet.perform_create` (в транзакции) |
| `list_conversations` | queryset с `Subquery` (последнее сообщение) + `Count` (непрочитанные) |
| Edge Function delete-account | `DELETE /api/me/` + удаление файлов аватара |
| Realtime | вне MVP; пока polling раз в 5–10 с |
Запрещённые для записи клиентом поля (`is_banned`, `is_staff`, `created_at`, `id`, `user`) — `read_only_fields` в сериализаторе.

---

## D. UI: экраны, компоненты, константы, стили

### D.1 Экраны
Landing (hero+stats, features, how, FAQ, CTA, footer) · Login · Register (8 шагов) · App-оболочка (sidebar + main) · Разделы: Discover, View profile, My profile, Edit profile, Settings (4 вкладки: Account/Privacy/Security/Danger), Messages (список + чат), Saved, Notifications* и Admin* (*вне MVP).

### D.2 Повторяющиеся компоненты → React
| Компонент | Где в legacy | Предложение для `frontend/src/components` |
|---|---|---|
| Avatar (градиент по id + инициалы / картинка) | `ac`, `ah` (83–85); `.rcav/.phav/.sbav/.conv-av` | `Avatar.jsx` (props: user, size) |
| PersonCard | `runSearch` (419), `renderSaved` (782) — **две копии** | `PersonCard.jsx` + кнопки View/Message/Save |
| Tag / TagList | `.tag`, `.rcts` | `TagList.jsx` |
| Modal | `openModal` (739), `#modal` | `Modal.jsx` (+ focus trap, Esc) |
| Toast | `toast` (747) | `ToastProvider` + хук `useToast` |
| Button / Input / Select / FormField | `.btn*`, `.fi`, `.fg`, `.fl` | `ui/Button.jsx`, `ui/Field.jsx` |
| Step-визард регистрации | `buildReg` (225) | `RegisterWizard.jsx` + 8 небольших шагов, состояние в одном `useState`/`useReducer` |
| ChipSelect (мультивыбор) и RadioPills | `.chip`, `.gchip`, `.rb` | `ChipSelect.jsx` (+ `<button>`, `aria-pressed`) |
| Toggle | `.tog` | `Toggle.jsx` (`role="switch"`) |
| Pagination | `goP`, `.pg` | `Pagination.jsx` |
| ChatList / ChatWindow / MessageBubble | 851–894 | `messaging/*` |
| Sidebar + mobile overlay | 4201–4230, `toggleSB` | `AppLayout.jsx` |
| ProfileView | `viewProfile` (449) и закомментированный `renderMyProfile` (почти идентичны) | один `ProfileView.jsx` (props: profile, isOwner) |
| EmptyState, PasswordStrength | `.empty`, `pwdStr` | мелкие компоненты |

### D.3 Константы (app.js)
| Константа | Строка | Размер | Проблема |
|---|---|---|---|
| `INTS` интересы | 206 | 25 | используются только в регистрации |
| `LAS` языки | 207 | 27 | нет Tajik/Kazakh/Kyrgyz/Karakalpak (важно для UZ) |
| `GLS` цели (+иконка) | 208 | 8 | **не совпадает с `GOALS` фильтра** (F-9) |
| `CTRS` страны | 209 | 63 | нет Kyrgyzstan/Tajikistan/Turkmenistan; порядок не алфавитный (Palestine между Ireland и Italy) |
| `FLDS` направления (фильтр) | 390 | 36 | в регистрации «field» — свободный текст (F-9) |
| `GOALS` цели (фильтр) | 391 | 10 | 3 значения (Project collaborators, Build CV / portfolio, College application prep) невозможно получить при регистрации; нет «Career networking» |
| `SNMS` названия шагов | 205 | 8 | |
| `AVC` градиенты аватаров | 83 | 8 | |
| `FAQS` | 132 | 8 | пункт «Registration requires a verified email» противоречит README (рекомендует отключить подтверждение) |
Рекомендация: вынести в `frontend/src/constants/*.js` **и** отдавать с сервера `GET /api/meta/` (единый источник; сервер валидирует по `choices`). Стоит заложить i18n (ru/uz/en) — открытый вопрос.

### D.4 CSS-переменные и тёмная тема
- Переменные в `:root` (index.html:33–62): цвета `--bg --white --border --border2 --blue --blue2 --blue-lt --blue-lt2 --text --text2 --text3 --text4 --ok --ok-lt --err --err-lt --warn`, тени `--shadow-sm/…/-lg`, радиусы `--r … --r-2xl`, шрифты `--font-d` (Sora) и `--font-b` (Inter), `--tr`.
- Тёмная тема: класс `body.dark` (2528–2812): переопределяет часть переменных + ещё ~60 ручных переопределений (`body.dark .xxx`), большинство **избыточны** (компонент уже использует переменные). Переключатель — `localStorage nk_theme`, `prefers-color-scheme` не учитывается; мигание светлой темой до загрузки скриптов.
- Недостатки: `--white` в тёмной теме = #111 (имя вводит в заблуждение → переименовать в `--surface`); жёсткие цвета (`#FECACA`, `#93C5FD`, `#A7F3D0`, inline-стили) не переключаются.
- **Что переиспользовать:** блок `:root` почти как есть → `frontend/src/styles/tokens.css`; тёмная тема — только переопределение переменных в `[data-theme="dark"]` на `<html>` (+ `@media (prefers-color-scheme: dark)` как значение по умолчанию). Компонентные стили (кнопки, формы, карточки, чипы, модалка, сайдбар, чат) переносить в CSS-файлы рядом с компонентами или CSS Modules (без новых библиотек).
- Адаптивность: брейкпойнты 440/480/500/580/600/640/700/768/780/900 — **много дублей** (одни и те же правила повторены в 3–4 блоках, 3296–3972). При переносе свести к 3 (600, 768, 900).

---

## E. Потоки (пошагово)

### E.1 Регистрация по email
1. Лендинг → `showPage('register')` (обёртка, app.js:1074) → `initReg()` (RD={}) → `renderReg()`.
2. Шаги 1–8: `buildReg(s)` рисует HTML, `rNext()` → `collectR(s)` собирает значения из DOM в `RD` и валидирует. Шаг 1: RPC `is_username_available`. Шаг 8: телефон обязателен.
3. `rFinish()` (302): `collectR(8)` → `sb.auth.signUp({email, password})` (312).
   - Ошибка «registered» → возврат на шаг 1.
   - Нет `data.session` (подтверждение почты включено) → тост + `showPage('login')`, **профиль не создан, `RD` потерян** (317–321).
   - Есть сессия → INSERT в `profiles` (325–335) → триггер создаёт `privacy_settings`.
4. `loadMyProfile()`, `loadSavedIds()`, `showPage('app')` → `bootApp()` (**падает на `renderMyProfile`, F-1**).

### E.2 Регистрация/вход через Google
`loginWithGoogle` (160) → редирект на Google → возврат на сайт → init (1046): `refreshSession()` → `loadMyProfile()`: профиля нет → `showPage('register')`. В шаге 1 скрыты email/пароль (`SESSION` задан), `rFinish` пропускает `signUp` и сразу делает INSERT. Если пользователь бросил регистрацию — остаётся «сирота» в `auth.users` без профиля.

### E.3 Вход
`doLogin` (164): `signInWithPassword` → `loadMyProfile` → нет профиля: `signOut` + ошибка «Could not load your profile» (**тупик для email-пользователя без профиля**); `ME.ban` → `signOut`; иначе `loadSavedIds` → `showPage('app')`.
Init при загрузке страницы (1046–1072): `getSession` → профиль → app / register / landing. `onAuthStateChange` регистрируется только если сессии нет (1068) — F-5.

### E.4 Сброс пароля
`forgotModal` → `sendReset` (194): `resetPasswordForEmail(email, {redirectTo})`, одинаковое сообщение (защита от перебора email — хорошо). Пользователь переходит по ссылке → Supabase создаёт «recovery»-сессию → приложение открывается как обычный вход. **Обработчика `PASSWORD_RECOVERY` и формы нового пароля нет** (grep: не найдено). `changePass` требует старый пароль → восстановить доступ нельзя.

### E.5 Смена пароля / email
`changePass` (688): проверка полей → `signInWithPassword` (проверка старого пароля) → `updateUser({password})`. `changeEmail` (703): аналогично → `updateUser({email})` → Supabase шлёт письмо(а) подтверждения (по умолчанию «secure email change» — на оба адреса, текст сообщения «sent to your new email» может быть неточным; нужна проверка в рантайме). `ME.em` обновится только после перезагрузки.

### E.6 Удаление аккаунта
`confirmDeleteAcc` (модалка, ввод `DELETE`) → `deleteMyAcc` (721) → `functions.invoke('delete-account')` → функция проверяет JWT (`auth.getUser`), `admin.deleteUser(id)` → каскад по FK удаляет profiles, privacy, saved, conversations, messages. Затем `signOut`, `showPage('landing')`. Файлы в Storage не удаляются; сообщения удалённого пользователя исчезают и у собеседников.

### E.7 Поиск
Ввод в `#qs` → `debSearch` (320 мс) → `runSearch` (398): читает 5 фильтров из DOM → RPC `search_profiles` (page=`sPage`, size=9) → `mapCard` → HTML-строка карточек (innerHTML) → пагинация из `total_count`. Кнопки карточки: View (`viewProfile` → RPC `get_profile_card`), Message (`startChat`), Save (`toggleSave`).

### E.8 Сообщения
1. «Message» → `startChat` → `ensureConversation` (806): сортирует пару id, SELECT, при отсутствии INSERT (при конфликте — повторный SELECT); кэш `CONV_CACHE`.
2. `showSec('messages')` → `renderConvList` (RPC `list_conversations` + `get_identities`), `updateMsgBadge` (ещё раз `list_conversations`), `subscribeMessages`.
3. `openChat` → шапка → `markSeen` (UPDATE seen_at) → `renderMessages` (**всю историю**) → подписка Realtime.
4. `sendMessage` (895): INSERT → только затем очищает поле → `renderMessages` + `renderConvList` + `updateMsgBadge`. Триггер обновляет `last_message_at`.
5. Входящее: Realtime INSERT → перерисовка чата (если открыт) + `markSeen` + список + бейдж.

---

## F. Проблемы

Условные обозначения: **[К]** — подтверждено чтением кода; **[Р]** — нужна проверка в рантайме (или зависит от настроек Supabase).

### F.0 Проверка твоих подозрений (сводка)
| # | Подозрение | Вердикт |
|---|---|---|
| 1 | XSS через innerHTML / inline onclick | **Подтверждено [К]** — Critical (F-2) |
| 2 | Политики profiles позволяют менять is_admin/is_banned; бан только в JS | **Подтверждено [К]** — Critical (F-7) |
| 3 | Регистрация с подтверждением почты: профиль не создаётся | **Подтверждено [К]**; частично смягчается, если пользователь вернётся по ссылке из письма (F-3) |
| 4 | delete-account: CORS/OPTIONS, файлы Storage | **Подтверждено [К]** по коду; факт CORS-блокировки — [Р] (F-4) |
| 5 | Инициализация: await без try/catch, onAuthStateChange после return, падение без CDN | **Подтверждено [К]** все три пункта (F-5) |
| 6 | Несовершеннолетние | **Подтверждено [К]**: проверки возраста нет (F-10) |
| 7 | Storage без серверных лимитов; нет rate limit/CAPTCHA | **Подтверждено [К]** (F-11); лимиты Supabase Auth по умолчанию — [Р] |
| 8 | Недоделки | **Подтверждено [К]**; плюс обнаружено, что страница «My profile» вообще не работает (F-1) |
| 9 | Версии CDN | **Частично подтверждено**: `lucide@1.17.0` существует (проверено через jsDelivr API), но устарела (последняя 1.55.0); `supabase-js@2` — плавающая версия (сейчас 2.117.3), без SRI (F-13) |

### F.1 Critical

**F-1. `renderMyProfile` и `reportUser` закомментированы, но вызываются — [К]** (`app.js:361, 382, 501, 595, 603, 625, 658`; определения закомментированы `507–519`, `522–571`)
Суть: `ReferenceError`. Каскад:
- `bootApp` обрывается на строке 361 → **не выполняются** `popEP()`, `popStSettings()`, `loadPrivToggles()` (362–364). Форма редактирования пуста, настройки пусты, **тумблеры приватности остаются «включены» (дефолт HTML) независимо от БД**.
- `savePrivacy` (666) читает все 5 тумблеров из DOM и пишет их в БД → пользователь, у которого скрыта локация, нажимает любой тумблер → **все скрытые поля снова становятся публичными** (утечка приватности).
- `saveProfile` (606) шлёт `field: v('ep-fi')`, `city`, `country`, `bio` без fallback → при пустой форме **стирает поля профиля**; затем падает на 625 и не показывает тост/не переключает раздел.
- `uploadAv`, `removeAv`, `saveStAcc` падают после записи в БД (595/603/658), UI не обновляется. Раздел «My profile» пуст. Кнопка «Report this profile» → ошибка в консоли.
Как проверить: открыть консоль после входа, видеть `ReferenceError: renderMyProfile is not defined` [Р-подтверждение тривиально]. Исправление: в React это один `ProfileView`; `Report` — модалка + `POST /api/reports/`; формы заполнять из `GET /api/me/`.
(README заявляет «profile reporting» — на деле не работает.)

**F-2. Stored XSS — [К]**
Данные других пользователей вставляются в HTML без экранирования:
- карточки: `${u.fn} ${u.ln}`, `u.fi`, `u.ci`, `u.co`, `u.bio`, теги (`app.js:421–424`), избранное (785–791), список чатов (870), профиль (469–496, 483–485), социальные ссылки (457–461), аватар `<img src="${u.av}">` (85).
- inline-обработчики: `onclick="viewProfile('${u.un}')"` (426, 793) — **username не ограничен никаким форматом** (SQL:28, JS нет проверки): `x');alert(1);//` исполняется у каждого, кто увидит карточку в поиске.
- Достаточно `first_name = <img src=x onerror=…>` (≤60 символов) или bio (≤300).
- `avatar_url` пользователь может записать напрямую через UPDATE (политика не ограничивает) — попадает в атрибут `src` у всех зрителей.
- Хорошо: сообщения экранируются `escapeHTML` (87), имя в шапке чата — через `textContent` (835).
Последствие: токены Supabase лежат в `localStorage` → кража сессии, действия от имени жертвы, удаление аккаунта. CSP не найдена.
Как проверить [Р]: зарегистрировать тестового пользователя с именем `<img src=x onerror=alert(1)>`, открыть Discover другим аккаунтом.
При переносе: React экранирует текст автоматически — **не использовать `dangerouslySetInnerHTML`**; ссылки соцсетей строить из проверенного username (regex на сервере), `href` только `https://t.me/…`; валидировать формат username (`^[a-z0-9_]{3,30}$`); аватар — только загруженный файл. Добавить CSP-заголовок.

**F-7. Пользователь может сам сделать себя админом / разбанить себя; бан проверяется только в браузере — [К]**
`profiles_update_own` (SQL:86–87) и `profiles_insert_own` (83–84) не ограничивают колонки; триггера, защищающего `is_admin/is_banned`, нет; `revoke update (…)` нет. Из консоли: `sb.from('profiles').update({is_banned:false,is_admin:true}).eq('id',…)`; при регистрации можно вставить строку сразу с `is_admin=true`.
Бан проверяется только в `doLogin` (176) и init (1058). Ни одна RLS-политика не смотрит `is_banned`: забаненный с живым токеном продолжает писать сообщения, менять профиль. `get_profile_card`/`get_identities` не фильтруют забаненных.
Сейчас `is_admin=true` даёт лишь «невидимость» в поиске (`search_profiles` исключает админов, 359) и в статистике, но в «Фазе 2» станет эскалацией привилегий.
Исправление: `is_banned/is_staff` — только read-only в serializer; проверка бана в `permission_classes` (`IsNotBanned`) на каждом запросе; при бане — инвалидировать токены.

### F.2 High

**F-3. Регистрация с подтверждением почты — профиль не создаётся — [К]** (`app.js:312–321`; триггера на `auth.users` нет — не найдено)
`signUp` без сессии → тост «check your email» → логин. `RD` теряется. Если пользователь вернётся через письмо, init увидит сессию без профиля и откроет `register` (данные вводить заново, 8 шагов); если вместо этого введёт пароль на странице логина — `doLogin` сделает `signOut` и покажет «Could not load your profile» (175) без пути вперёд. `emailRedirectTo` не задан → ссылка ведёт на «Site URL» из Dashboard [Р]. Ошибка «email не подтверждён» маскируется под «Incorrect email or password» (172).
Исправление: профиль создаётся в одном запросе `POST /api/auth/register/` (user+profile в одной транзакции); подтверждение почты — отдельный токен; логин блокируется с понятным сообщением.

**F-4. delete-account — [К] по коду, CORS — [Р]**
- Функция не обрабатывает `OPTIONS` и не добавляет `Access-Control-Allow-*` (`index.ts:25–59`): `supabase-js` шлёт заголовки `Authorization`, `apikey`, `x-client-info` → браузер делает preflight `OPTIONS` → получает 405 без CORS-заголовков → запрос блокируется, пользователь видит «Could not delete account» (`app.js:724`). Фактическое поведение — проверить в рантайме.
- Файлы аватара в Storage не удаляются: нет FK на `auth.users`, функция их не трогает; файлы публично читаются по известному URL → нарушение «удалить все данные» (FAQ:140).
- Успешные/ошибочные ответы без `Content-Type` (31, 38, 43).
- После удаления клиент не сбрасывает `MY_PRIVACY/SAVED_IDS/CONV_CACHE`.
Исправление: `DELETE /api/me/` в Django — в транзакции удалить файл аватара и пользователя; CORS настраивается централизованно.

**F-5. Инициализация хрупкая — [К]**
- `app.js:22` `window.supabase.createClient` без проверки: если CDN недоступен, скрипт падает; `const/let` ниже не инициализируются, `DOMContentLoaded`-слушатель (1046) не регистрируется → мёртвый сайт (ни FAQ, ни статистики, ни навигации). Нет `defer`/фолбэка/сообщения пользователю. То же при отсутствии `config.js`.
- Init (1046–1072): `await refreshSession()`/`loadMyProfile()` без `try/catch` — при сетевой ошибке необработанное исключение, пользователь остаётся на landing и не понимает почему.
- `onAuthStateChange` (1068) регистрируется **после** ранних `return` (1058, 1059, 1063) → для вернувшегося пользователя (сессия есть) подписки нет: выход в другой вкладке, истечение токена, `USER_UPDATED` не обрабатываются.
- `localStorage` без `try/catch` (например, 1021 выполняется на верхнем уровне): при заблокированном хранилище (Safari private/запрет cookies) скрипт обрывается [Р].
- `bootApp` вызывается из `showPage` без `await/catch` (120).

**F-6.** см. F-1 (жалобы не работают — таблица `reports` бесполезна). Убрать из README ложное утверждение.

**F-8. Спам и дубль-отправка в сообщениях — [К]**
- Кто угодно может создать диалог с кем угодно (`conversations_insert_participant`, SQL:168–169) и сразу писать; блокировки/запроса на переписку нет. `startChat` создаёт **пустой диалог при простом клике** (821–822), он сразу виден получателю («No messages yet»). Для платформы со школьниками — риск преследования.
- `sendMessage` очищает поле только после ответа сервера (899–901): двойной Enter/клик отправляет дубликат.
- `renderMessages` каждый раз тянет всю историю (879) — без пагинации; на каждое отправленное/входящее сообщение 3–4 запроса (`renderMessages`, `renderConvList`, `updateMsgBadge` — два раза `list_conversations`).
- `CONV_CACHE` (802) не сбрасывается при выходе → после смены аккаунта в той же вкладке сообщения уходят в чужой диалог и получают отказ RLS «Message failed to send». `activeChatId/activeConvId` тоже не сбрасываются; Realtime-канал остаётся после `doLogout` и в колбэке обращается к `SESSION.user` (null) → TypeError.

**F-9. Фильтры поиска расходятся с данными регистрации — [К]**
- `GOALS` фильтра (391) содержат 3 значения, которых регистрация не создаёт (поиск всегда пуст), и не содержат «Career networking».
- Поле `field` в регистрации — свободный текст (249), фильтр — точное равенство `p.field = p_field` (SQL:368) со списком из 36 значений → «computer science» ≠ «Computer Science». То же `country`: в Edit profile это текстовый input (4328), в регистрации select → после правки фильтр по стране не найдёт человека.
- README уже исправлял такую же проблему для `status`, но не для остальных.

**F-10. Несовершеннолетние и приватность по умолчанию — [К]**
- Возраст: поле даты — три `<input type=number>` с `max="2015"` (app.js:235). Вне `<form>` браузерной валидации нет, JS диапазон не проверяет; БД тоже (`date_of_birth` просто `date`). Даже по атрибуту допускает 11 лет (при дате анализа 2026-10-10), реально — любую дату, в т.ч. будущую. 31 февраля ломает INSERT с техническим текстом ошибки (337).
- Маркетинг прямо адресован школьникам («high schoolers», index.html:4019, 4112; FAQ:133–134).
- Умолчания приватности: всё `true` (SQL:98–102): локация (город+страна+регион), университет, **все контакты (Telegram, Instagram, WhatsApp, публичный email)** и поиск — открыты любому зарегистрированному (а при отключённом подтверждении почты — любому, кто создаст аккаунт). Для несовершеннолетних это неприемлемо.
- Писать первым может любой (F-8). Возраст собеседника не виден.
- Телефон обязателен «для верификации» (app.js:261, 297), но верификации нет (README:28) — лишний сбор персональных данных.
Решение — в открытых вопросах (I-1, I-2): минимальный возраст; для < 18 — закрытые умолчания (контакты скрыты, не в поиске, писать могут только взрослым после запроса или вовсе запрет); телефон убрать из MVP.

**F-11. Нет серверных ограничений на загрузки и частоту — [К]**
- Бакет создаётся без `file_size_limit`/`allowed_mime_types` (SQL:450–452). Проверки «image/*» и 5 МБ — только в JS (584–585) и обходятся прямым запросом к Storage. Расширение берётся из имени файла (586) → можно загрузить `.html/.svg` в публичный бакет. `removeAv` удаляет только 5 расширений (600) → файлы с другими расширениями и старые аватары другого типа остаются.
- `avatar_url` — произвольная строка (см. F-2).
- Rate limit/CAPTCHA на уровне приложения не найдены: signUp без `captchaToken`, RPC/сообщения/жалобы без ограничений. Встроенные лимиты Supabase Auth — [Р] (Dashboard → Auth → Rate Limits).
- Поля без верхних границ: `interests/languages/goals` (массивы), `reports.reason/details`, `phone`, `field` и др. — можно хранить мегабайты.
- `search_profiles(p_page_size)` без ограничения (SQL:349, 382): один вызов с `p_page_size=100000` выгружает весь каталог.
В Django: `ImageField` + проверка Pillow + перекодирование + лимит размера (`DATA_UPLOAD_MAX_MEMORY_SIZE`), `DRF throttling` (anon/user/scoped), `max_length` и `choices` во всех сериализаторах, `max_page_size`.

**F-12. Сброс пароля не доведён до конца — [К]** (E.4). Нет `PASSWORD_RECOVERY`/`location.hash`-обработки. Пользователь не может задать новый пароль. High (функционально).

### F.3 Medium

**F-13. Зависимости с CDN — [К]/[Р]** (`index.html:4582–4583`)
- `@supabase/supabase-js@2` — плавающая мажорная версия: при каждой загрузке может прийти другой минорный релиз (на дату анализа `2.117.3`, готовится 3.x) — непредсказуемая поломка и риск цепочки поставок. `lucide@1.17.0` — закреплена и существует, но устарела (актуальная 1.55.0), без SRI (`integrity`/`crossorigin`). Google Fonts без запасного шрифта. В React-версии зависимости ставятся через npm и фиксируются `package-lock.json`.
- `MutationObserver` на весь документ (app.js:35) пересоздаёт иконки при каждом изменении DOM.

**F-14. Недоделки — [К]**
- `?profile=<username>` генерируется (`shareProfile`, 966–970), но `location.search` нигде не читается → ссылка бесполезна. Нужен роутер `/u/:username`.
- Редактирование: нет интересов, языков, целей, года/уровня (`#ep-yr` есть в HTML, но не читается/не пишется), пола, даты рождения, телефона, школы, региона, статуса (UI отсутствует; `saveProfile` 614–620 их не трогает). `ep-co` — свободный текст вместо списка.
- Уведомления, админка, онлайн-статус, просмотры профиля, completeness, «people like you» — нет бэкенда (README:22–28); в CSS лежит ~400 строк под них.
- Закладки нет на странице чужого профиля; блок «Report» содержит кнопку «Send message» (4497–4502 / app.js:497–502).
- Нет блокировки пользователей.

**F-15. Утечки приватности через поиск — [К]** (SQL:365–368)
`search_profiles` ищет по `university` и фильтрует по `country` **независимо от `show_university`/`show_location`**: запрос «MIT» вернёт тех, кто скрыл университет; фильтр «Uzbekistan» — тех, кто скрыл страну (в ответе поле null, но принадлежность раскрыта). Решение: в DRF-фильтрах учитывать приватность (`Q(show_university=True) | …`).

**F-16. Прочие логические ошибки — [К]**
- `saveStAcc` делит «Display name» по первому пробелу (650–651): имя из одного слова → `last_name=''` нарушает CHECK 1–60 (SQL:30) → «Could not save».
- Username меняется в двух местах (Edit profile и Settings) — дублирование логики (606 vs 641). Нет ограничения формата и частоты смены.
- `changePass/changeEmail` не работают для аккаунтов Google (пароля нет).
- `rBack` игнорирует результат `collectR` (301).
- Состояние `RD` подставляется в `value="${…}"` без экранирования (231–267) — самоинъекция атрибута.
- Гонка в поиске: ответы не отменяются/не сверяются (stale results), рекурсия в `runSearch` (414).
- `get_landing_stats`: комментарий говорит «только search-visible» (SQL:397–399), код не фильтрует `show_in_search`.
- `exportProfilePDF` применяет настройки приватности к экспорту своих же данных (974) и склеивает HTML из полей без экранирования (991–996) — только свои данные.
- Фильтры на мобильных скрыты `display:none` и дублируются в CSS дважды (3579–3591, 3960–3972).

**F-17. Валидация только на клиенте — [К]** Пароль ≥ 8 (285) проверяется в JS; серверное требование Supabase по умолчанию мягче [Р]. Email, DOB, телефон не валидируются на сервере. В DRF — валидаторы паролей Django и сериализаторы.

**F-18. Производительность — [К]/[Р]**
- `requestAnimationFrame(draw)` (1041) крутится вечно, даже когда лендинг скрыт (`display:none`), O(n²) по 50 точкам; нет `prefers-reduced-motion`. Нагрузка на батарею.
- `ILIKE '%…%'` по конкатенации полей (SQL:366–367) — полный перебор таблицы, индексы не помогут; при росте базы нужен `pg_trgm` + GIN или полнотекстовый поиск.
- Пагинация рисует кнопки для всех страниц (433).
- Стили на 3900 строк в одном HTML, много дублей.

### F.4 Low

**F-19. Права на функции — [Р]** Для SQL-функций нет `REVOKE EXECUTE … FROM PUBLIC`. В Supabase функции в `public` по умолчанию доступны роли `anon`. Тогда `get_profile_card(username)` и `get_identities(uuid[])` вызываются **без входа** (скрейпинг профилей, включая контакты, по угаданным username; `is_username_available` помогает подбирать). `search_profiles` для anon вернёт пусто только случайно (`id <> NULL`). Проверка: `select has_function_privilege('anon','public.get_profile_card(citext)','execute');`.

**F-20. Секреты/репозиторий — [К]**
- `web/config.js` содержит реальный `SUPABASE_URL` и anon-ключ (роль `anon`; публичный по замыслу). В git сейчас не отслеживается (`??`), но корневого `.gitignore` нет — `git add .` его закоммитит. В новый проект его не переносить.
- В новом каркасе: `backend/backend/settings.py` содержит `SECRET_KEY`, `DEBUG=True`, `ALLOWED_HOSTS=[]`, SQLite; `__pycache__/*.pyc` уже в git; `Pipfile` без пакетов; `frontend/` отслеживается, `networkit/` (venv) нужно игнорировать. См. раздел H.0.

**F-21. Мелкие SQL-замечания — [К]** Получатель может сбросить `seen_at` обратно в NULL (guard пропускает); `reports` без лимитов и без защиты от повторных жалоб; `ilike` не экранирует `%`/`_`; удаление пользователя каскадно стирает переписку у собеседников; комментарий про `supabase-client.js` устарел.

**F-22. Доступность (a11y) — [К], контраст — [Р]**
- `viewport … maximum-scale=1.0` (index.html:6) запрещает масштабирование (WCAG 1.4.4).
- Интерактивные элементы — `<a onclick>`/`<div onclick>` без `href`/`role`/`tabindex` (навигация, футер, `.chip`, `.rb`, `.gchip`, `.conv-item`, `.sb-user`, логотипы) — недоступны с клавиатуры.
- `<label class="fl">` без `for` → поля не связаны с подписями; иконки-кнопки (гамбургер, закладка, отправить, тема) без `aria-label`; тумблеры `.tog` без `role="switch"/aria-checked`; модалка без `role="dialog"`, ловушки фокуса и Esc; тост без `aria-live`; FAQ без `aria-expanded`.
- Нет `alt` у аватаров, нет управления фокусом при смене «страниц».
- Цвет `--text4 #9CA3AF` на белом ≈ 2.5:1 — ниже AA для мелкого текста (оценка по значениям, проверить Lighthouse).

**F-23. UX — [К]** Нет состояний загрузки/блокировки кнопок (все async-действия); ошибки Supabase показываются пользователю как есть (`'Could not create your profile: ' + perr.message`); интерфейс только на английском; футер-ссылки (About, Privacy, Terms) пустышки — для сбора персональных данных нужны Политика и Условия; год «© 2025» захардкожен; `FAQ`: «verified email» не соответствует режиму из README.

---

## G. Что переиспользовать из legacy, что выбросить

**Переиспользовать (идеи и контент):**
- Дизайн-токены (`:root`), типографика (Inter/Sora), базовые стили кнопок/форм/карточек/чипов/модалки/чата/сайдбара.
- Структура экранов и тексты лендинга; список шагов регистрации и набор полей; константы (после чистки).
- Принцип «приватность решает сервер»: перенести как сериализаторы Public/Own.
- Идеи, достойные сохранения: одинаковое сообщение при сбросе пароля (защита от перебора email); пара `user_a < user_b` + UNIQUE для диалогов; `list_conversations` одним запросом; пагинация с общим `count`; `unread_count`; кэш истории поиска в localStorage; `escapeHTML` для сообщений (в React не нужен).
- SQL из `0001_init.sql` — как спецификация ограничений (длины, CHECK), переносить в `validators`/`constraints`.

**Выбросить / не переносить:**
- Supabase-клиент, `config*.js`, Edge Function, RLS-политики и SECURITY DEFINER-функции (заменяются DRF).
- Весь рендер строками `innerHTML` и inline-обработчики; глобальные переменные; `window.showPage`-обёртка; `MutationObserver`.
- Мёртвый код и CSS: online-status, suggest, completeness, onboarding, notifications (до этапа «вне MVP»), admin (CSS/HTML), `previewUser`, неиспользуемые id.
- ~60 переопределений `body.dark …`, дубли media-запросов.
- Захардкоженные CDN-скрипты; canvas-анимация (по желанию — упростить/отключить).
- Сбор обязательного телефона; `is_admin` как поле клиента.
- Realtime (вне MVP).

---

## H. План переноса

### H.0 Состояние каркаса и что поправить сразу (без смены стека)
- `backend/`: Django-проект есть, приложение `users` создано, **но не добавлено в `INSTALLED_APPS`** (settings.py:33–40 — только стандартные), БД SQLite, `SECRET_KEY` в коде, `DEBUG=True`. Нужно: `.env`, PostgreSQL, добавить `rest_framework`, создать `profiles`, `messaging`. **Кастомную модель User определить до первой `migrate`** (сейчас миграций нет — `users/migrations/` пуст).
- Корневой `.gitignore`: `__pycache__/`, `*.pyc`, `.env`, `networkit/` (venv), `node_modules/`, `media/`.
- `frontend/`: Vite + React 19 (JS, JSX), демо-страница; без роутера и HTTP-клиента.

### H.1 Django-приложения
| Приложение | Назначение |
|---|---|
| `users` (оставить) | кастомный `User` (вход по email), регистрация, логин/логаут, сброс пароля, смена пароля/email, удаление аккаунта |
| `profiles` (добавить) | `Profile`, приватность, `SavedProfile`, `Report`, поиск, загрузка аватара, справочники (`/api/meta/`) |
| `messaging` (добавить) | `Conversation`, `Message`, список диалогов, отметка «прочитано» |
Админку «Фазы 2» заменяет стандартный Django Admin (`/admin/`) — бесплатно для модерации жалоб и банов.

### H.2 DRF endpoints (MVP)
Все пути под `/api/`. Доступ: **A** — анонимно, **U** — авторизованный и не забаненный, **O** — владелец.
| Метод | URL | Доступ | Ответ / примечание |
|---|---|---|---|
| POST | `/auth/register/` | A | создаёт User+Profile+Privacy в транзакции; 201 `{profile}`; ошибки по полям |
| POST | `/auth/login/` | A | токены/сессия; различает «неверный пароль» и «email не подтверждён» (без раскрытия существования email) |
| POST | `/auth/logout/` | U | 204 |
| POST | `/auth/password-reset/` | A | всегда 200 (одинаковый ответ) |
| POST | `/auth/password-reset/confirm/` | A | `{uid, token, new_password}` → 200 |
| POST | `/auth/verify-email/` | A | `{token}` (если включаем подтверждение) |
| POST | `/auth/password/change/` | U | `{old, new}` |
| POST | `/auth/email/change/` | U | `{new_email, password}` |
| GET | `/auth/username-available/?u=` | A (throttle) | `{available: bool}` |
| GET | `/me/` | U | собственный профиль (полный, без чужих скрытий) + privacy |
| PATCH | `/me/` | O | редактирование; `read_only`: is_banned, created_at, user |
| DELETE | `/me/` | O | удаление аккаунта и аватара, 204 |
| PUT/DELETE | `/me/avatar/` | O | multipart-загрузка / удаление; проверка типа/размера |
| GET/PATCH | `/me/privacy/` | O | 5 флагов |
| GET | `/profiles/?q=&country=&field=&status=&goal=&language=&page=` | U | `{count, next, results:[PublicCard]}`; `page_size` ≤ 24; учитывает приватность и бан |
| GET | `/profiles/{username}/` | U | `PublicProfile` (маскирование); 404 для забаненных |
| GET | `/saved/` | U | список карточек избранного |
| PUT/DELETE | `/saved/{profile_id}/` | U | добавить/убрать (идемпотентно) |
| POST | `/reports/` | U | `{target, reason, details}`; throttle |
| GET | `/conversations/` | U | список: `other_user`, `last_message`, `unread_count` |
| POST | `/conversations/` | U | `{user_id}` → создать/вернуть диалог (по правилам политики для несовершеннолетних) |
| GET | `/conversations/{id}/messages/?before=` | участник | пагинация (по 30) |
| POST | `/conversations/{id}/messages/` | участник | `{body}` ≤ 4000 |
| POST | `/conversations/{id}/read/` | участник | помечает входящие `seen_at=now` |
| GET | `/messages/unread-count/` | U | для бейджа |
| GET | `/meta/` | A | страны, поля, интересы, языки, цели, статусы |
| GET | `/stats/` | A | members/fields/countries (кэш) |
Вне MVP: уведомления, `/admin/*` API, realtime (WebSocket/SSE), блокировки пользователей, верификация телефона.

Аутентификация (решение нужно, см. I-4): либо **сессии Django + CSRF** (проще, если фронт и API на одном домене/через прокси), либо **JWT в httpOnly-cookie**. Токены в `localStorage` — не использовать (урок F-2).

### H.3 React: страницы и компоненты (JSX)
Роутер (`react-router-dom`, **новая библиотека — прошу согласовать**; без неё — самописный `window.history`, хуже).
```
frontend/src/
  api/          client.js (fetch-обёртка: base URL, CSRF/токен, ошибки), auth.js, profiles.js, messages.js
  context/      AuthContext.jsx (текущий пользователь), ThemeContext.jsx, ToastContext.jsx
  hooks/        useDebounce.js, useApi.js
  constants/    (из app.js; позже из /api/meta/)
  styles/       tokens.css, base.css, dark.css
  components/   ui/ (Button, Field, Modal, Toast, Toggle, ChipSelect, Pagination, EmptyState)
                Avatar.jsx, PersonCard.jsx, TagList.jsx, ProfileView.jsx, AppLayout.jsx (Sidebar)
  pages/        LandingPage, LoginPage, RegisterPage (wizard), ResetPasswordPage, ResetConfirmPage,
                DiscoverPage, ProfilePage (/u/:username), MyProfilePage, EditProfilePage,
                SettingsPage (Account/Privacy/Security/Danger), MessagesPage, SavedPage, NotFoundPage
  App.jsx       маршруты; ProtectedRoute (редирект на /login)
```
Маршруты: `/`, `/login`, `/register`, `/reset-password`, `/reset-password/:uid/:token`, `/discover`, `/u/:username`, `/me`, `/me/edit`, `/settings`, `/messages`, `/messages/:conversationId`, `/saved`. Фильтры поиска хранить в query-string (ссылки и «Назад» работают). Сообщения в MVP — опрос раз в несколько секунд при открытом чате.

### H.4 Порядок работ (малые шаги, после каждого — проверка)
1. **Гигиена репозитория:** `.gitignore`, убрать `__pycache__` из git, `.env` + `python-dotenv`/`environ` (после согласования), PostgreSQL в settings, `users` в `INSTALLED_APPS`.
2. Кастомный `User` (email-вход) + первая миграция.
3. `profiles`: модели `Profile/PrivacySettings`, миграции, админка.
4. Регистрация/логин/логаут + `/me/` (GET/PATCH) + тесты прав (нельзя менять `is_banned`).
5. React: Vite-каркас, роутер, `AuthContext`, Landing/Login/Register (wizard из 8 шагов), токены темы.
6. Справочники `/meta/`, редактирование профиля, аватар (+ валидации).
7. Поиск `/profiles/` + `DiscoverPage` + публичный профиль `/u/:username` (сериализаторы Public с приватностью; тест «скрытое поле не уходит»).
8. Избранное.
9. Сообщения: модели, endpoints, `MessagesPage` (polling), правила «кто может писать первым».
10. Настройки: приватность, смена пароля/email, сброс пароля, удаление аккаунта.
11. Жалобы + Django Admin для модерации и банов (`IsNotBanned`).
12. Адаптив/тёмная тема/доступность (чек-лист из F-22), throttling, CSP/безопасные cookie.
13. Деплой: PostgreSQL, `gunicorn` + статика (WhiteNoise — согласовать), фронт на Vercel/Nginx, HTTPS, `DEBUG=False`, бэкапы.

---

## I. Открытые вопросы к тебе

1. **Минимальный возраст** и аудитория: допускаем ли школьников (до 18)? Какой порог (13/14/16/18)? Нужно ли согласие родителей? Это влияет на умолчания приватности и правила переписки (F-10). Юридические требования РУз к персональным данным (в т.ч. хранение на серверах в стране) я не проверял — нужна консультация.
2. **Умолчания приватности:** оставить «всё открыто» для взрослых? Контакты (Telegram/WhatsApp/телефон) показывать только по клику/взаимному согласию?
3. **Телефон:** нужен ли вообще (верификация SMS в MVP не планируется)? Предлагаю убрать из регистрации.
4. **Аутентификация:** сессии Django+CSRF (один домен) или JWT в httpOnly-cookie (фронт и API на разных доменах)? Где будет хоститься фронт и API?
5. **Подтверждение почты** в MVP: включаем? Какой SMTP/провайдер писем?
6. **Язык интерфейса:** только английский, как сейчас, или ru/uz/en? Страны/языки: добавить Kyrgyzstan, Tajikistan, Turkmenistan и языки региона?
7. **Новые библиотеки (по CLAUDE.md спрашиваю заранее):** backend — `psycopg` (PostgreSQL), `python-dotenv` или `django-environ`, `djangorestframework-simplejwt` (если JWT), `django-cors-headers`, `Pillow` (аватары), `django-filter` (необязательно), `gunicorn`/`whitenoise` (деплой); frontend — `react-router-dom`. Что разрешаешь?
8. **Справочники:** `field` и `university` — выбор из списка (чище поиск) или свободный текст с подсказками? `country` храним кодом ISO?
9. **Кто может писать первым:** любой / только после «запроса на переписку» / только после взаимного избранного? Нужна ли кнопка «заблокировать» уже в MVP?
10. **Существующие данные** в проекте Supabase (`bqjpzdbvqmbijukwbapn`): переносить пользователей или стартуем с чистой базы? (Пароли из Supabase Auth перенести нельзя без хэшей; аватары — потребуется выгрузка.)
11. **Тёмная тема:** оставляем в MVP? Использовать системную тему по умолчанию?
12. **Деплой:** где поднимаем PostgreSQL и Django (VPS, Render, Railway, другое)? Есть ли домен?
13. **Жалобы:** достаточно Django Admin для модерации в MVP (рекомендую)?
14. **Старые тексты:** FAQ, «Privacy Policy», «Terms» — кто готовит? Сейчас это пустые ссылки.
