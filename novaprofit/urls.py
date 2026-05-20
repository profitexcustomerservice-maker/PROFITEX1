from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
from rest_framework.routers import DefaultRouter
from accounts.views import RegisterView, CurrentUserView, UserListView, UserDetailView, ToggleUserStatusView
from core.views import TaskViewSet, PlanViewSet, UserPlanViewSet, UserTaskViewSet, system_settings_api, health_check
from wallet.views import TransactionViewSet, WithdrawalViewSet, PaymentMethodViewSet, CryptoDepositViewSet
from notifications.views import NotificationViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r"tasks", TaskViewSet, basename="task")
router.register(r"plans", PlanViewSet, basename="plan")
router.register(r"user-tasks", UserTaskViewSet, basename="user-task")
router.register(r"user-plans", UserPlanViewSet, basename="user-plan")
router.register(r"transactions", TransactionViewSet, basename="transaction")
router.register(r"withdrawals", WithdrawalViewSet, basename="withdrawal")
router.register(r"payment-methods", PaymentMethodViewSet, basename="payment-method")
router.register(r"crypto-deposits", CryptoDepositViewSet, basename="crypto-deposit")
router.register(r"notifications", NotificationViewSet, basename="notification")

urlpatterns = [
	path("admin/", admin.site.urls),
	path("admin_panel/", include("admin_panel.urls")),
	path("api/auth/register/", RegisterView.as_view(), name="auth_register"),
	path("api/auth/login/", TokenObtainPairView.as_view(), name="auth_login"),
	path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
	path("api/auth/me/", CurrentUserView.as_view(), name="auth_me"),
	path("api/user/", CurrentUserView.as_view(), name="user_me"),
	path("api/auth/users/", UserListView.as_view(), name="auth_users"),
	path("api/auth/users/<int:pk>/", UserDetailView.as_view(), name="auth_user_detail"),
	path("api/auth/users/<int:user_id>/toggle-status/", ToggleUserStatusView.as_view(), name="auth_user_toggle_status"),
	path("api/system/settings/", system_settings_api, name="system_settings_api"),
	path("health/", health_check, name="health_check"),
	path("api/", include(router.urls)),
	path("", include("accounts.urls")),
	path("", include("core.urls")),
	path("", include("wallet.urls")),
	path("", include("notifications.urls")),
]

if settings.DEBUG:
	urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
	urlpatterns += [
		re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATICFILES_DIRS[0]}),
	]

