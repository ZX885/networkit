from django.urls import path

from .views import MeView, MetaView, PrivacyView

urlpatterns = [
    path("meta/", MetaView.as_view(), name="meta"),
    path("me/", MeView.as_view(), name="me"),
    path("me/privacy/", PrivacyView.as_view(), name="me-privacy"),
]
