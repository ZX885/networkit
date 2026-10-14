from rest_framework import status
from rest_framework.exceptions import ErrorDetail, NotFound, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .meta import build_meta, meta_etag
from .models import Profile
from .serializers import MeUpdateSerializer, OwnProfileSerializer, PrivacySerializer, privacy_of

# Поля, которые нельзя менять через PATCH /api/me/ (docs/SPEC.md §3.5)
READ_ONLY_FIELDS = (
    "username",
    "date_of_birth",
    "email",
    "email_verified",
    "age",
    "is_minor",
    "is_banned",
    "avatar_url",
    "privacy",
    "created_at",
    "country_label",
    "field_label",
    "status_label",
)

META = build_meta()  # справочники меняются только с деплоем: собираем один раз
META_ETAG = meta_etag(META)
META_MAX_AGE = 60 * 60  # браузер и CDN могут держать ответ час


class MetaView(APIView):
    """GET /api/meta/ — справочники и лимиты для форм. Публичный, кэшируется."""

    authentication_classes = []  # сессию не читаем: ответ одинаков для всех
    permission_classes = [AllowAny]

    def get(self, request):
        headers = {"ETag": META_ETAG, "Cache-Control": f"public, max-age={META_MAX_AGE}"}
        if request.headers.get("If-None-Match") == META_ETAG:
            return Response(status=status.HTTP_304_NOT_MODIFIED, headers=headers)
        return Response(META, headers=headers)


class MeView(APIView):
    """GET — свой профиль, PATCH — изменить разрешённые поля."""

    def get_profile(self, request):
        profile = Profile.objects.select_related("user").filter(user=request.user).first()
        if profile is None:
            raise NotFound()  # у аккаунта нет профиля (например, у суперпользователя)
        return profile

    def get(self, request):
        return Response(OwnProfileSerializer(self.get_profile(request)).data)

    def patch(self, request):
        profile = self.get_profile(request)
        data = request.data
        if not isinstance(data, dict):
            raise ValidationError("Expected a JSON object.")
        forbidden = {
            name: [ErrorDetail("This field cannot be changed.", code="read_only_field")]
            for name in READ_ONLY_FIELDS
            if name in data
        }
        if forbidden:
            raise ValidationError(forbidden)

        serializer = MeUpdateSerializer(profile, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return Response(OwnProfileSerializer(profile).data, status=status.HTTP_200_OK)


class PrivacyView(MeView):
    """GET/PATCH /api/me/privacy/ — 5 флагов приватности владельца."""

    def get(self, request):
        return Response(privacy_of(self.get_profile(request)))

    def patch(self, request):
        profile = self.get_profile(request)
        if not isinstance(request.data, dict):
            raise ValidationError("Expected a JSON object.")
        serializer = PrivacySerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return Response(privacy_of(profile))
