from rest_framework.response import Response


# 删除 PUT 方法，为了阻止修改 name
class PartialUpdateModelMixin:
    """
    Update a model instance.
    """
    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        if request.data.get('name') is not None:
            del request.data['name'] # 名称（name）不可修改，但可新增

        partial = True
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)
