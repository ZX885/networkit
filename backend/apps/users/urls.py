from django.urls import path

from . import views

urlpatterns = [
    path("auth/csrf/", views.csrf, name="auth-csrf"),
    path("auth/username-available/", views.username_available, name="auth-username-available"),
    path("auth/register/", views.RegisterView.as_view(), name="auth-register"),
    path("auth/verify-email/", views.VerifyEmailView.as_view(), name="auth-verify-email"),
    path(
        "auth/resend-verification/",
        views.ResendVerificationView.as_view(),
        name="auth-resend-verification",
    ),
    path("auth/login/", views.LoginView.as_view(), name="auth-login"),
    path("auth/logout/", views.LogoutView.as_view(), name="auth-logout"),
    path(
        "auth/password-reset/",
        views.PasswordResetRequestView.as_view(),
        name="auth-password-reset",
    ),
    path(
        "auth/password-reset/confirm/",
        views.PasswordResetConfirmView.as_view(),
        name="auth-password-reset-confirm",
    ),
    path("auth/password/change/", views.PasswordChangeView.as_view(), name="auth-password-change"),
    path("auth/email/change/", views.EmailChangeView.as_view(), name="auth-email-change"),
    path(
        "auth/email/change/confirm/",
        views.EmailChangeConfirmView.as_view(),
        name="auth-email-change-confirm",
    ),
]
