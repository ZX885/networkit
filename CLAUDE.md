# NetworkIt — правила проекта
Платформа-нетворкинг (профили, поиск, избранное, личные сообщения). Сначала Узбекистан.
Старый сайт: networkit-backend/ (Supabase + статический JS) — ТОЛЬКО чтение. Анализ: docs/ANALYSIS.md.

## Стек (менять только с моего согласия)
- Backend: Python, Django, DRF, PostgreSQL. Приложения в backend/apps: common, users, profiles, messaging. Настройки в backend/config.
- Frontend: React на чистом JavaScript с JSX, сборщик Vite. БЕЗ TypeScript, без Vue, без UI-китов.
- Авторизация: сессии Django + CSRF, фронт и API на одном домене.
- Новые библиотеки только после вопроса мне (одобренный список в docs/SPEC.md).

## Структура и стиль
- Frontend: app/ pages/ features/ components/(ui, layout, shared) lib/ constants/ styles/.
- Один компонент на файл (до ~200 строк), PascalCase.jsx, хуки useX.js, стили Name.module.css рядом.
- Цвета, шрифты, отступы, тени — только из src/styles/tokens.css, без хардкода значений в компонентах.
- Тёмная тема только через переменные [data-theme]. Glassmorphism — класс .glass из effects.css.
- Backend: на каждое приложение models/serializers/views/urls/admin/tests. Файл больше ~300 строк делим на пакет.

## Правила работы
- Код простой и читаемый, с короткими комментариями. Я знаю Python/Django/DRF и JSX.
- Работай небольшими шагами. Перед изменениями покажи план и жди моего ответа.
- Права и приватность проверяй на сервере (permissions/serializers), а не во фронтенде.
- Пользовательский текст никогда не вставлять как HTML (без dangerouslySetInnerHTML).
- Секреты только в .env, не коммитить.
- После каждой задачи: 3–5 строк, что изменено и как запустить/проверить.
- Документы и объяснения пиши на русском, имена в коде на английском.

## Структура frontend/src
app/ (App, router, providers) · pages/ · features/<имя>/ (components, hooks) · components/ui|layout|shared · lib/ · constants/ · texts/ · styles/ (tokens, themes, base, index)
Тексты интерфейса лежат в src/texts, не в компонентах.
Моки API (пока нет бэкенда) лежат в src/api/mock/ и помечены комментарием MOCK.
Возраст: MIN_AGE=13 (constants/rules.js); младше 18 лет считаются несовершеннолетними (контакты запрещены).