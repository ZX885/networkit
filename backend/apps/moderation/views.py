from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.profiles.visibility import ProfileVisibility
from config.pagination import StandardPagination
from config.throttles import BASE_THROTTLES, BlockThrottle, ReportThrottle

from . import services
from .models import Block


def mini_card(profile):
    """Мини-карточка заблокированного: имя — через общую функцию приватности."""
    return {
        "username": profile.username,
        **ProfileVisibility(profile).name(),
        "avatar_url": None,
    }


class BlockListView(APIView):
    """GET /api/blocks/ — кого заблокировал я (новые первыми). Кто заблокировал меня — не отдаётся."""

    def get(self, request):
        queryset = (
            Block.objects.filter(blocker=request.user, blocked__profile__isnull=False)
            .select_related("blocked__profile")
            .order_by("-created_at", "-id")
        )
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginator.get_paginated_response([mini_card(b.blocked.profile) for b in page])


class BlockView(APIView):
    """PUT/DELETE /api/blocks/{username}/ — заблокировать и разблокировать (оба идемпотентны, 204)."""

    throttle_classes = [*BASE_THROTTLES, BlockThrottle]

    def put(self, request, username):
        services.block_user(request.user, username)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, username):
        services.unblock_user(request.user, username)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReportView(APIView):
    """POST /api/reports/ — пожаловаться на человека (или на диалог с ним). Ответ всегда один."""

    throttle_classes = [*BASE_THROTTLES, ReportThrottle]

    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        services.create_report(request.user, data)
        return Response({"status": "received"}, status=status.HTTP_201_CREATED)
