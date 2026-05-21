from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TransactionViewSet, WithdrawalViewSet, CryptoDepositViewSet, 
    PaymentMethodViewSet, transactions_page
)

router = DefaultRouter()
router.register(r"transactions", TransactionViewSet, basename="transaction")
router.register(r"withdrawals", WithdrawalViewSet, basename="withdrawal")
router.register(r"crypto-deposits", CryptoDepositViewSet, basename="crypto-deposit")
router.register(r"payment-methods", PaymentMethodViewSet, basename="payment-method")

urlpatterns = [
    path("transactions/", transactions_page, name="transactions_page"),
    path("api/", include(router.urls))
]
