from django.urls import path
from .views import notifications_page, notifications_admin_redirect

urlpatterns = [
    path("notifications/admin/", notifications_admin_redirect, name="notifications_admin_redirect"),
    path("notifications/", notifications_page, name="notifications_page"),
]
