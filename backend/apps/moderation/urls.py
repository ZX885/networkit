from django.urls import path

from . import views

urlpatterns = [
    path("blocks/", views.BlockListView.as_view(), name="block-list"),
    path("blocks/<str:username>/", views.BlockView.as_view(), name="block-detail"),
    path("reports/", views.ReportView.as_view(), name="report-create"),
]
