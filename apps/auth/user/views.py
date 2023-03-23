from django.utils.translation import gettext_lazy as _
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework import fields
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, inline_serializer

from .models import User
from .serializers import JwtSerializer
from .serializers import PasswordChangeSerializer
from .serializers import UserModelSerializer
from .schemas import UserInfo

__all__ = ("UserModelViewSet", "LoginView", "UserInfoView", "PasswordChangeView")


class UserModelViewSet(ModelViewSet):
    """
    用户
    """

    queryset = User.objects.order_by("id")
    serializer_class = UserModelSerializer
    permission_classes = (IsAuthenticated, IsAdminUser)
    lookup_field = 'username'
    lookup_type = 'str'

    @extend_schema(summary=_("user") + "-" + _("reset password"))
    @action(methods=["PATCH"], detail=True, url_path="reset-password")
    def reset_password(self, request, *args, **kwargs):
        """
        重置用户密码
        """
        user = self.get_object()
        password = request.data.get('password', None)
        if not password:
            raise ValidationError(detail={"password": _("No password")})
        user.set_password(password)
        user.save()

        return Response()


class LoginView(APIView):
    """
    登陆:  Authentication: Bearer {Token}
    """
    permission_classes = ()
    authentication_classes = ()
    # renderer_classes = (JSONRenderer,)
    # parser_classes = (JSONParser,)
    www_authenticate_realm = "api"

    def get_authenticate_header(self, request):
        return 'JWT realm="{}"'.format(
            self.www_authenticate_realm,
        )

    @extend_schema(summary=_("login"), request=JwtSerializer)
    @extend_schema(responses={
        200: inline_serializer("Login", {
            "token": fields.CharField(),
            "user_id": fields.IntegerField(),
            "username": fields.CharField(),
        })
    })
    def post(self, request, *args, **kwargs):
        serializer = JwtSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class UserInfoView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(summary=_("User Info"), responses={
        (200, "application/json"): UserInfo.schema()
    })
    def get(self, request, *args, **kwargs):
        u = UserInfo.from_orm(request.user)
        return Response(u.dict())


class PasswordChangeView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(summary=_("Change Password"), request=PasswordChangeSerializer, responses={200: ""})
    def patch(self, request, *args, **kwargs):
        """
        修改密码
        """
        ser = PasswordChangeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        if not request.user.check_password(ser.validated_data["original"]):
            raise ValidationError(detail={"original": _("Invalid original password")})

        request.user.set_password(ser.validated_data["password"])
        request.user.save()
        return Response()
