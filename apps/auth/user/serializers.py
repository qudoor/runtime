#!/usr/bin/env python
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer
from rest_framework import fields
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer

from .exceptions import ServerError
from .token import jwt_token, TokenError
from .models import User


class JwtSerializer(Serializer):  # noqa
    username = fields.CharField(required=True)
    password = fields.CharField(required=True)

    @staticmethod
    def get_user(attrs):
        user_model = get_user_model()
        try:
            user = user_model.objects.get(username=attrs["username"])
        except user_model.DoesNotExist:
            raise ValidationError(detail={"username": _('User not found')})

        return user

    @staticmethod
    def get_token(user):
        try:
            return jwt_token.encode({
                "user_id": user.id,
                "username": user.username,
            })
        except TokenError:
            raise ServerError("Token generated failed")

    def validate(self, attrs):
        user = self.get_user(attrs)

        if not user.check_password(attrs["password"]):
            raise ValidationError(detail={"password": _('Password incorrect')})

        if not user.is_active:
            raise ValidationError(detail={"user": _('User inactive')})

        return {
            'token': self.get_token(user),
            'username': user.username,
            'user_id': user.id,
        }


class UserModelSerializer(ModelSerializer):
    created_at = fields.DateTimeField(source="date_joined", read_only=True)

    @staticmethod
    def validate_password(password: str) -> str:
        """
        密码加密
        :param password: 明文
        :return: 加密后的密码
        """
        return make_password(password)

    def update(self, instance, validated_data) -> User:
        validated_data.pop("password", None)
        validated_data.pop("username", None)
        return super().update(instance, validated_data)

    class Meta:
        model = User
        fields = ["id",
                  "username",
                  "email",
                  "password",
                  "is_superuser",
                  "created_at",
                  "last_login"]
        read_only_fields = ["id", "is_superuser", "last_login", "created_at"]
        extra_kwargs = {
            "password": {"write_only": True}
        }


class PasswordChangeSerializer(Serializer):
    original = fields.CharField(required=True, help_text=_("Old password"))
    password = fields.CharField(required=True, help_text=_("New password"))
