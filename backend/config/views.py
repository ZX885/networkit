from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@authentication_classes([])  # сессию не читаем: проверка должна быть дешёвой
@permission_classes([AllowAny])  # публичный endpoint: доступ без входа
def health(request):
    """GET /api/health/ — сервер работает."""
    return Response({"status": "ok"})
