from django.urls import path

from . import views

urlpatterns = [
    path("conversations/", views.ConversationListView.as_view(), name="conversation-list"),
    path("conversations/summary/", views.ConversationSummaryView.as_view(), name="conversation-summary"),
    path("conversations/<uuid:pk>/", views.ConversationDetailView.as_view(), name="conversation-detail"),
    path(
        "conversations/<uuid:pk>/accept/",
        views.ConversationDecideView.as_view(accept=True),
        name="conversation-accept",
    ),
    path(
        "conversations/<uuid:pk>/decline/",
        views.ConversationDecideView.as_view(accept=False),
        name="conversation-decline",
    ),
    path("conversations/<uuid:pk>/messages/", views.MessageListView.as_view(), name="message-list"),
    path("conversations/<uuid:pk>/read/", views.ConversationReadView.as_view(), name="conversation-read"),
]
