from datetime import date


def calculate_age(birth_date, today=None):
    """Полных лет на дату today (по умолчанию — сегодня). Нужен и модели, и валидатору."""
    today = today or date.today()
    had_birthday = (today.month, today.day) >= (birth_date.month, birth_date.day)
    return today.year - birth_date.year - (0 if had_birthday else 1)
