from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PublicTaskViewSet, SubmissionViewSet
from .views import WalletView

router = DefaultRouter()
router.register(r'public-tasks', PublicTaskViewSet, basename='public-task')
router.register(r'submissions', SubmissionViewSet, basename='submission')

urlpatterns = [
    path('', include(router.urls)),
    path('wallet/', WalletView.as_view(), name='wallet'),
]
