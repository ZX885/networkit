from rest_framework import status
from rest_framework.exceptions import ErrorDetail, NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Profile
from .serializers import MeUpdateSerializer, OwnProfileSerializer

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
)


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
