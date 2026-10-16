"""
Справочники профиля: пары (код, название). В базе хранится код.

Единственный источник справочников: frontend получает их через GET /api/meta/ (apps/profiles/meta.py),
своих списков во frontend нет. Коды в базе — строки из этих списков, менять их нельзя без миграции данных.
"""

# Страны: код ISO 3166-1 alpha-2
COUNTRIES = [
    ("AF", "Afghanistan"),
    ("AL", "Albania"),
    ("DZ", "Algeria"),
    ("AR", "Argentina"),
    ("AM", "Armenia"),
    ("AU", "Australia"),
    ("AT", "Austria"),
    ("AZ", "Azerbaijan"),
    ("BD", "Bangladesh"),
    ("BY", "Belarus"),
    ("BE", "Belgium"),
    ("BR", "Brazil"),
    ("CA", "Canada"),
    ("CL", "Chile"),
    ("CN", "China"),
    ("CO", "Colombia"),
    ("HR", "Croatia"),
    ("CZ", "Czech Republic"),
    ("DK", "Denmark"),
    ("EG", "Egypt"),
    ("FI", "Finland"),
    ("FR", "France"),
    ("GE", "Georgia"),
    ("DE", "Germany"),
    ("GH", "Ghana"),
    ("GR", "Greece"),
    ("HU", "Hungary"),
    ("IN", "India"),
    ("ID", "Indonesia"),
    ("IR", "Iran"),
    ("IE", "Ireland"),
    ("IT", "Italy"),
    ("JP", "Japan"),
    ("KZ", "Kazakhstan"),
    ("KE", "Kenya"),
    ("KG", "Kyrgyzstan"),
    ("MY", "Malaysia"),
    ("MX", "Mexico"),
    ("MA", "Morocco"),
    ("NL", "Netherlands"),
    ("NZ", "New Zealand"),
    ("NG", "Nigeria"),
    ("NO", "Norway"),
    ("PK", "Pakistan"),
    ("PS", "Palestine"),
    ("PE", "Peru"),
    ("PH", "Philippines"),
    ("PL", "Poland"),
    ("PT", "Portugal"),
    ("RO", "Romania"),
    ("RU", "Russia"),
    ("SA", "Saudi Arabia"),
    ("RS", "Serbia"),
    ("SG", "Singapore"),
    ("KR", "South Korea"),
    ("ES", "Spain"),
    ("SE", "Sweden"),
    ("CH", "Switzerland"),
    ("TJ", "Tajikistan"),
    ("TR", "Turkey"),
    ("TM", "Turkmenistan"),
    ("UA", "Ukraine"),
    ("AE", "United Arab Emirates"),
    ("GB", "United Kingdom"),
    ("US", "United States"),
    ("UZ", "Uzbekistan"),
    ("VN", "Vietnam"),
]

# Направления (последнее — «Other»; отдельного поля field_other нет)
FIELDS = [
    ("accounting", "Accounting"),
    ("architecture", "Architecture"),
    ("artificial_intelligence", "Artificial Intelligence"),
    ("biology", "Biology"),
    ("biotechnology", "Biotechnology"),
    ("business_administration", "Business Administration"),
    ("chemistry", "Chemistry"),
    ("civil_engineering", "Civil Engineering"),
    ("computer_science", "Computer Science"),
    ("data_science", "Data Science"),
    ("design", "Design"),
    ("economics", "Economics"),
    ("education", "Education"),
    ("electrical_engineering", "Electrical Engineering"),
    ("entrepreneurship", "Entrepreneurship"),
    ("environmental_science", "Environmental Science"),
    ("finance", "Finance"),
    ("history", "History"),
    ("international_relations", "International Relations"),
    ("journalism", "Journalism"),
    ("law", "Law"),
    ("literature", "Literature"),
    ("marketing", "Marketing"),
    ("mathematics", "Mathematics"),
    ("mechanical_engineering", "Mechanical Engineering"),
    ("medicine", "Medicine"),
    ("music", "Music"),
    ("neuroscience", "Neuroscience"),
    ("nursing", "Nursing"),
    ("philosophy", "Philosophy"),
    ("physics", "Physics"),
    ("political_science", "Political Science"),
    ("psychology", "Psychology"),
    ("public_health", "Public Health"),
    ("sociology", "Sociology"),
    ("software_engineering", "Software Engineering"),
    ("other", "Other"),
]

# Интересы
INTERESTS = [
    ("business", "Business"),
    ("economics", "Economics"),
    ("finance", "Finance"),
    ("law", "Law"),
    ("medicine", "Medicine"),
    ("computer_science", "Computer Science"),
    ("engineering", "Engineering"),
    ("psychology", "Psychology"),
    ("marketing", "Marketing"),
    ("design", "Design"),
    ("entrepreneurship", "Entrepreneurship"),
    ("artificial_intelligence", "Artificial Intelligence"),
    ("mathematics", "Mathematics"),
    ("physics", "Physics"),
    ("biology", "Biology"),
    ("chemistry", "Chemistry"),
    ("history", "History"),
    ("philosophy", "Philosophy"),
    ("sociology", "Sociology"),
    ("political_science", "Political Science"),
    ("architecture", "Architecture"),
    ("music", "Music"),
    ("literature", "Literature"),
    ("neuroscience", "Neuroscience"),
    ("biotechnology", "Biotechnology"),
]

# Языки
LANGUAGES = [
    ("english", "English"),
    ("spanish", "Spanish"),
    ("french", "French"),
    ("german", "German"),
    ("arabic", "Arabic"),
    ("russian", "Russian"),
    ("chinese", "Chinese"),
    ("japanese", "Japanese"),
    ("portuguese", "Portuguese"),
    ("italian", "Italian"),
    ("korean", "Korean"),
    ("turkish", "Turkish"),
    ("hindi", "Hindi"),
    ("dutch", "Dutch"),
    ("polish", "Polish"),
    ("swedish", "Swedish"),
    ("norwegian", "Norwegian"),
    ("danish", "Danish"),
    ("ukrainian", "Ukrainian"),
    ("uzbek", "Uzbek"),
    ("persian", "Persian"),
    ("thai", "Thai"),
    ("vietnamese", "Vietnamese"),
    ("indonesian", "Indonesian"),
    ("yoruba", "Yoruba"),
    ("swahili", "Swahili"),
    ("bengali", "Bengali"),
    ("tajik", "Tajik"),
    ("kazakh", "Kazakh"),
    ("kyrgyz", "Kyrgyz"),
    ("karakalpak", "Karakalpak"),
]

# Цели
GOALS = [
    ("friends", "Looking for friends"),
    ("study_partners", "Study partners"),
    ("project_collaborators", "Project collaborators"),
    ("startup_cofounders", "Startup co-founders"),
    ("mentorship", "Mentorship"),
    ("research_collaboration", "Research collaboration"),
    ("internship_opportunities", "Internship opportunities"),
    ("career_networking", "Career networking"),
    ("cv_portfolio", "Build CV / portfolio"),
    ("college_prep", "College application prep"),
]

# Статус
STATUSES = [
    ("student", "Student"),
    ("professional", "Professional"),
]

# Пол (необязательное поле)
GENDERS = [
    ("male", "Male"),
    ("female", "Female"),
    ("non_binary", "Non-binary"),
    ("undisclosed", "Prefer not to say"),
]

# Города Узбекистана для фильтра поиска и выбора в формах (решение заказчика: сначала Узбекистан).
# В профиле город остаётся свободным текстом (Profile.city); фильтр сравнивает его с названием города
# из этого списка. Код — название в нижнем регистре; «Other» (любой другой город) в справочник не входит.
UZ_CITIES = [
    ("tashkent", "Tashkent"),
    ("samarkand", "Samarkand"),
    ("bukhara", "Bukhara"),
    ("andijan", "Andijan"),
    ("namangan", "Namangan"),
    ("fergana", "Fergana"),
    ("nukus", "Nukus"),
    ("karshi", "Karshi"),
    ("termez", "Termez"),
    ("urgench", "Urgench"),
    ("jizzakh", "Jizzakh"),
    ("navoi", "Navoi"),
]

# Для какой страны клиент показывает список городов (UZ_CITIES)
COUNTRY_CITIES_DEFAULT = "UZ"


def codes(choices):
    """Список кодов из списка пар (код, название)."""
    return [code for code, _label in choices]


def label_of(choices, code):
    """Название по коду; неизвестный код (или пусто) — пустая строка."""
    return dict(choices).get(code, "")


def as_options(choices):
    """Список пар → [{"code": ..., "label": ...}] (формат /api/meta/)."""
    return [{"code": code, "label": label} for code, label in choices]
