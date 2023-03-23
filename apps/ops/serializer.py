from rest_framework import serializers
from .models import AdHocModel, PlayBookModel


class AdhocSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdHocModel
        fields = '__all__'


class PlaybookSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayBookModel
        fields = '__all__'
