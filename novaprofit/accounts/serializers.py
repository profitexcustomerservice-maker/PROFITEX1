from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name")

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class UserSerializer(serializers.ModelSerializer):
    wallet_balance = serializers.SerializerMethodField()
    plan_name = serializers.SerializerMethodField()
    tasks_completed = serializers.SerializerMethodField()

    profile_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            "id", "email", "first_name", "last_name", "current_plan_level", 
            "profile_image", "is_admin", "is_staff", "is_active", 
            "is_superuser", "last_active", "last_rewarded_at", "created_at", 
            "wallet_balance", "plan_name", "tasks_completed"
        )
        extra_kwargs = {
            "email": {"read_only": True},
            "first_name": {"required": False},
            "last_name": {"required": False},
        }

    def get_wallet_balance(self, obj):
        if hasattr(obj, "wallet"):
            return float(obj.wallet.balance)
        return 0.0

    def get_plan_name(self, obj):
        from core.models import UserPlan
        up = UserPlan.objects.filter(user=obj).select_related('plan').first()
        return up.plan.title if up else "No Plan"

    def get_tasks_completed(self, obj):
        return obj.completed_tasks.count()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data.get("email"), password=data.get("password"))
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        data["user"] = user
        return data
