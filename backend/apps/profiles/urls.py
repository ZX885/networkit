from django.urls import path

from .views import (
    MeView,
    MetaView,
    PrivacyView,
    ProfileDetailView,
    ProfileListView,
    SavedListView,
    SavedProfileView,
)

urlpatterns = [
    path("meta/", MetaView.as_view(), name="meta"),
    path("me/", MeView.as_view(), name="me"),
    path("me/privacy/", PrivacyView.as_view(), name="me-privacy"),
    path("profiles/", ProfileListView.as_view(), name="profile-list"),
    path("profiles/<str:username>/", ProfileDetailView.as_view(), name="profile-detail"),
    path("saved/", SavedListView.as_view(), name="saved-list"),
    path("saved/<str:username>/", SavedProfileView.as_view(), name="saved-profile"),
]
