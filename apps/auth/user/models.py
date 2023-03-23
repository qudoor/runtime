from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser


def avatar_upload_to(instance, filename):
    return "/".join(["user", "avatar", str(instance.id), filename])


class User(AbstractUser):
    name = models.CharField(
        verbose_name=_("name"),
        max_length=32,
        null=True,
        blank=True
    )

    nickname = models.CharField(
        verbose_name=_("nickname"),
        max_length=32,
        null=True,
        blank=True,
    )

    phone = models.CharField(
        verbose_name=_("phone"),
        max_length=32,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"<{self.name or ''}:{self.username}>"

    class Meta:
        abstract = False
        verbose_name = _("user")
        verbose_name_plural = _("users")
        db_table = "auth_user"
