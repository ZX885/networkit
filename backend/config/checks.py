from django.core.checks import Error, register
from django.db import connection
from django.db.utils import OperationalError


@register()
def check_database_connection(app_configs, **kwargs):
    """Останавливает runserver / check с понятным сообщением, если нет связи с PostgreSQL."""
    try:
        connection.ensure_connection()
    except OperationalError as exc:
        settings = connection.settings_dict
        reply = str(exc).strip()
        # PostgreSQL на русской Windows отвечает в кодировке cp1251: текст приходит искажённым
        if "�" in reply:
            reply = "(текст ответа сервера нечитаем из-за кодировки Windows)"
        return [
            Error(
                f"Не удалось подключиться к PostgreSQL "
                f"(база «{settings['NAME']}», {settings['HOST']}:{settings['PORT']}, "
                f"пользователь «{settings['USER']}»).",
                hint=(
                    "Чаще всего: неверный пароль или логин в DATABASE_URL (файл backend/.env), "
                    "неверное имя базы (регистр важен) или PostgreSQL не запущен. "
                    f"Ответ сервера: {reply}"
                ),
                id="config.E001",
            )
        ]
    return []
