from rest_framework import status
from rest_framework.exceptions import ErrorDetail, NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from config.pagination import StandardPagination
from config.throttles import (
    BASE_THROTTLES,
    MessageRequestThrottle,
    MessageSendDayThrottle,
    MessageSendThrottle,
)

from . import queries, services
from .models import Message
from .serializers import ConversationSerializer, MessageSerializer

BOXES = ("chats", "requests", "sent")
MESSAGES_DEFAULT_LIMIT = 30
MESSAGES_MAX_LIMIT = 50


def get_conversation_or_404(user, pk):
    """Диалог с аннотациями, если user — участник и собеседник виден; иначе 404 (чужой диалог
    неотличим от несуществующего)."""
    conversation = queries.annotated(user, queries.participant_conversations(user).filter(pk=pk)).first()
    if conversation is None:
        raise NotFound()
    return conversation


def present(conversation, user):
    return ConversationSerializer(conversation, context={"user": user}).data


def body_data(request):
    return request.data if isinstance(request.data, dict) else {}


def positive_int(params, name):
    raw = params.get(name)
    if raw in (None, ""):
        return None
    try:
        value = int(raw)
    except ValueError:
        value = 0
    if value < 1:
        raise ValidationError({name: [ErrorDetail("Enter a positive number.", code="invalid")]})
    return value


class ConversationListView(APIView):
    """GET /api/conversations/?box=chats|requests|sent — список; POST — запрос на переписку."""

    def get_throttles(self):
        if self.request.method == "POST":
            return [throttle() for throttle in [*BASE_THROTTLES, MessageRequestThrottle]]
        return super().get_throttles()

    def get(self, request):
        box = request.query_params.get("box") or "chats"
        if box not in BOXES:
            raise ValidationError({"box": [ErrorDetail(f'"{box}" is not a valid choice.', code="invalid_choice")]})
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queries.box_conversations(request.user, box), request, view=self)
        data = ConversationSerializer(page, many=True, context={"user": request.user}).data
        return paginator.get_paginated_response(data)

    def post(self, request):
        data = body_data(request)
        conversation = services.create_request(request.user, data.get("username") or "", data.get("body"))
        first = Message.objects.filter(conversation=conversation).order_by("id").first()
        return Response(
            {
                "conversation": present(get_conversation_or_404(request.user, conversation.pk), request.user),
                "message": MessageSerializer(first, context={"user": request.user}).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ConversationSummaryView(APIView):
    """GET /api/conversations/summary/ — счётчики для бейджей (опрос раз в 30 секунд)."""

    def get(self, request):
        return Response(queries.summary(request.user))


class ConversationDetailView(APIView):
    def get(self, request, pk):
        return Response(present(get_conversation_or_404(request.user, pk), request.user))


class ConversationDecideView(APIView):
    """POST …/accept/ и …/decline/ (accept задаётся в as_view)."""

    accept = True

    def post(self, request, pk):
        conversation = get_conversation_or_404(request.user, pk)
        services.decide(conversation.pk, request.user, self.accept)
        return Response(present(get_conversation_or_404(request.user, pk), request.user))


class MessageListView(APIView):
    """GET — курсорная выдача по возрастанию id; POST — отправка сообщения."""

    def get_throttles(self):
        if self.request.method == "POST":
            return [
                throttle()
                for throttle in [*BASE_THROTTLES, MessageSendThrottle, MessageSendDayThrottle]
            ]
        return super().get_throttles()

    def get(self, request, pk):
        conversation = get_conversation_or_404(request.user, pk)
        params = request.query_params
        raw_limit = str(params.get("limit", ""))  # кривой или нулевой limit — значение по умолчанию
        limit = int(raw_limit) if raw_limit.isdigit() and int(raw_limit) > 0 else MESSAGES_DEFAULT_LIMIT
        limit = min(limit, MESSAGES_MAX_LIMIT)
        before, after = positive_int(params, "before"), positive_int(params, "after")
        messages = Message.objects.filter(conversation=conversation)

        if after is not None:  # новые сообщения (опрос открытого чата)
            rows = list(messages.filter(id__gt=after).order_by("id")[:limit])
            oldest_id = rows[0].pk if rows else after + 1
        else:  # последние limit (или limit перед сообщением before)
            if before is not None:
                messages = messages.filter(id__lt=before)
            rows = list(messages.order_by("-id")[:limit])
            rows.reverse()
            oldest_id = rows[0].pk if rows else (before or 0)
        has_more_older = Message.objects.filter(conversation=conversation, id__lt=oldest_id).exists()
        serializer = MessageSerializer(rows, many=True, context={"user": request.user})
        return Response({"results": serializer.data, "has_more_older": has_more_older})

    def post(self, request, pk):
        conversation = get_conversation_or_404(request.user, pk)
        message = services.send_message(conversation.pk, request.user, body_data(request).get("body"))
        return Response(
            MessageSerializer(message, context={"user": request.user}).data,
            status=status.HTTP_201_CREATED,
        )


class ConversationReadView(APIView):
    """POST /api/conversations/{id}/read/ — помечает входящие прочитанными (только принятый диалог)."""

    def post(self, request, pk):
        conversation = get_conversation_or_404(request.user, pk)
        return Response({"updated": services.mark_read(conversation, request.user)})

