from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """Allow clients to control page size up to a safe maximum."""
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 500
