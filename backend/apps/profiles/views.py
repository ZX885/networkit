from rest_framework import status
from rest_framework.exceptions import ErrorDetail, NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView

from apps.users import services as account_services
from apps.users.serializers import DeleteAccountSerializer
from config.pagination import StandardPagination
from config.exceptions import CannotTargetSelf
from config.throttles import (
    BASE_THROTTLES,
    AccountPasswordThrottle,
    SavedThrottle,
    SearchThrottle,
)

from .meta import build_meta, meta_etag
from .models import Profile, SavedProfile
from .saved import add_saved, is_saved, saved_list, saved_user_ids
from .search import search_profiles, visible_profiles
from .serializers import (
    CardSerializer,
    MeUpdateSerializer,
    OwnProfileSerializer,
    PrivacySerializer,
    PublicProfileSerializer,
    privacy_of,
)

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
    """GET — свой профиль, PATCH — изменить разрешённые поля, DELETE — удалить аккаунт (с паролем)."""

    def get_throttles(self):
        if self.request.method == "DELETE":  # проверка пароля: общий лимит на пользователя
            return [throttle() for throttle in [*BASE_THROTTLES, AccountPasswordThrottle]]
        return super().get_throttles()

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


    def delete(self, request):
        """DELETE /api/me/ {password}: удаляет аккаунт, все данные (каскадом) и сессии. 204 и выход.
        Сотрудники и суперпользователи удалить себя через API не могут (403)."""
        user = request.user
        if user.is_staff or user.is_superuser:
            raise PermissionDenied("This account cannot be deleted here.")
        serializer = DeleteAccountSerializer(data=request.data, context={"user": user})
        serializer.is_valid(raise_exception=True)
        account_services.delete_account(user)
        request._request.session.flush()  # выход: текущая сессия закрыта, cookie очищается
        return Response(status=status.HTTP_204_NO_CONTENT)


class PrivacyView(MeView):
    """GET/PATCH /api/me/privacy/ — 5 флагов приватности владельца."""

    http_method_names = ["get", "patch", "head", "options"]  # DELETE (удаление аккаунта) — только на /api/me/

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


class ProfileListView(ListAPIView):
    """GET /api/profiles/ — поиск людей (docs/SPEC.md §3.6). Параметры: q, country, field, status,
    goal, language, page, page_size. page_size больше 24 обрезается до 24."""

    serializer_class = CardSerializer
    pagination_class = StandardPagination
    throttle_classes = [*BASE_THROTTLES, SearchThrottle]

    def get_queryset(self):
        return search_profiles(self.request.user, self.request.query_params)

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset())
        # is_saved для всей страницы одним запросом (без N+1)
        saved_ids = saved_user_ids(request.user, [profile.user_id for profile in page])
        serializer = self.get_serializer(
            page, many=True, context={**self.get_serializer_context(), "saved_ids": saved_ids}
        )
        return self.get_paginated_response(serializer.data)


class ProfileDetailView(APIView):
    """GET /api/profiles/{username}/ — публичный профиль. 404, если человека нет, он забанен или не
    подтвердил почту. Профиль со show_in_search=False и свой собственный открываются."""

    def get(self, request, username):
        profile = visible_profiles().filter(username=username.lower()).first()
        if profile is None:
            raise NotFound()
        saved_ids = {profile.user_id} if is_saved(request.user, profile.user_id) else set()
        return Response(PublicProfileSerializer(profile, context={"saved_ids": saved_ids}).data)


class SavedListView(ListAPIView):
    """GET /api/saved/ — мои закладки (Card с is_saved=true), новые первыми. Забаненные, неактивные
    и неподтверждённые пропадают; show_in_search=False закладку не скрывает."""

    serializer_class = CardSerializer
    pagination_class = StandardPagination
    throttle_classes = BASE_THROTTLES

    def get_queryset(self):
        return saved_list(self.request.user)

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset())
        profiles = [saved.saved_user.profile for saved in page]
        serializer = CardSerializer(profiles, many=True, context={"all_saved": True})
        return self.get_paginated_response(serializer.data)


class SavedProfileView(APIView):
    """PUT/DELETE /api/saved/{username}/ — добавить или убрать закладку (оба идемпотентны, 204)."""

    throttle_classes = [*BASE_THROTTLES, SavedThrottle]

    def put(self, request, username):
        username = username.lower()
        own = Profile.objects.filter(user=request.user).values_list("username", flat=True).first()
        if username == own:
            raise CannotTargetSelf()
        target = visible_profiles().filter(username=username).first()
        if target is None:
            raise NotFound()  # нет такого, забанен, неактивен или не подтвердил почту
        add_saved(request.user, target.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, username):
        # Всегда 204: убрать закладку можно и на человека, который уже недоступен
        SavedProfile.objects.filter(
            owner=request.user, saved_user__profile__username=username.lower()
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
