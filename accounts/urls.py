from django.urls import path
from .views import dashboard, home_page, login_page, logout_page, register_page, wallet_page, profile_page, otp_verify, otp_resend, forgot_password_view, reset_password_view, reset_password_resend_view, admin_diagnostic, auth_test


urlpatterns = [
    path("register/", register_page, name="register_page"),
    path("login/", login_page, name="login_page"),
    path("logout/", logout_page, name="logout_page"),
    path("forgot-password/", forgot_password_view, name="forgot_password"),
    path("reset-password/", reset_password_view, name="reset_password"),
    path("reset-password/resend/", reset_password_resend_view, name="reset_password_resend"),
    path("otp/verify/", otp_verify, name="otp_verify"),
    path("otp/resend/", otp_resend, name="otp_resend"),
    path("dashboard/", dashboard, name="dashboard"),
    path("wallet/", wallet_page, name="wallet_page"),
    path("profile/", profile_page, name="profile_page"),
    path("admin-diagnostic/", admin_diagnostic, name="admin_diagnostic"),
    path("auth-test/", auth_test, name="auth_test"),
    path("", home_page, name="home"),

]
