# Create your views here.
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.auth.user.models import User
from .models import ApiRecord


class ApiRecordSerializer(ModelSerializer):
    name = serializers.SerializerMethodField()
    operation = serializers.CharField(source="action")
    operation_info = serializers.CharField(source="body")

    class Meta:
        model = ApiRecord
        fields = '__all__'

    @staticmethod
    def get_name(obj: ApiRecord):
        try:
            return User.objects.get(id=obj.user_id).username
        except User.DoesNotExist:
            return ""


class ApiRecordViewSet(ReadOnlyModelViewSet):
    serializer_class = ApiRecordSerializer
    queryset = ApiRecord.objects.order_by('-id')
