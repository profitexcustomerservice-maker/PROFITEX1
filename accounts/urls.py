from django.urls import path
from .views import dashboard, home_page, login_page, logout_page, register_page, wallet_page, profile_page, referral_details_page, otp_verify, otp_resend, forgot_password_view, reset_password_view, reset_password_resend_view, admin_diagnostic, auth_test
from .debug_views import debug_admin_status
from .auth_test_view import test_admin_auth
from .admin_setup_bypass import admin_setup_bypass
from .simple_test import simple_admin_test
from .version_check import version_check


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
    path("referrals/", referral_details_page, name="referral_details"),
    path("admin-diagnostic/", admin_diagnostic, name="admin_diagnostic"),
    path("auth-test/", auth_test, name="auth_test"),
    path("debug-admin/", debug_admin_status, name="debug_admin_status"),
    path("test-admin-auth/", test_admin_auth, name="test_admin_auth"),
    path("admin-setup-bypass/", admin_setup_bypass, name="admin_setup_bypass"),
    path("simple-admin-test/", simple_admin_test, name="simple_admin_test"),
    path("version-check/", version_check, name="version_check"),
    path("", home_page, name="home"),

]
