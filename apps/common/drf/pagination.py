from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param


class MyPageNumberPagination(PageNumberPagination):
    page_size = 10000  # default page size 如果没有默认的
    page_size_query_param = 'pageSize'  # ?pageNum=xx&pageSize=??
    page_query_param = 'pageNum'
    max_page_size = 10000  # max page size

    # 根据前端读取的数据格式，格式化数据
    def get_paginated_response(self, data):
        # url = self.request.build_absolute_uri()
        # num_pages = self.page.paginator.num_pages
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'total': self.page.paginator.count,
            'num_pages': self.page.paginator.num_pages,
            'items': data
        })
