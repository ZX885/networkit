from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Общая пагинация: 12 записей на странице, клиент может попросить до 24 (?page_size=24)."""

    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 24
