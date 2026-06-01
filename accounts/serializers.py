from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import User, SocialLink, Referral


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    referral_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="An account with this email already exists."
            )
        ]
    )

    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name", "referral_code")

    def create(self, validated_data):
        # Normalize email to lower-case for consistent uniqueness checks
        referral_code = validated_data.pop('referral_code', '').strip().upper()
        validated_data['email'] = validated_data.get('email', '').strip().lower()

        if referral_code:
            referrer = User.objects.filter(referral_code=referral_code).first()
            if not referrer:
                raise serializers.ValidationError({"referral_code": "Invalid referral code."})
            validated_data['referred_by'] = referrer

        user = User.objects.create_user(**validated_data)

        if referral_code and user.referred_by:
            Referral.objects.create(referrer=user.referred_by, referred_user=user)

        return user

class UserSerializer(serializers.ModelSerializer):
    wallet_balance = serializers.SerializerMethodField()
    plan_name = serializers.SerializerMethodField()
    tasks_completed = serializers.SerializerMethodField()
    referral_code = serializers.CharField(read_only=True)
    referred_by = serializers.SerializerMethodField()
    referral_link = serializers.SerializerMethodField()

    profile_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            "id", "email", "first_name", "last_name", "current_plan_level", 
            "profile_image", "is_admin", "is_staff", "is_active", 
            "is_superuser", "last_active", "last_rewarded_at", "created_at", 
            "wallet_balance", "plan_name", "tasks_completed", "referral_code", "referred_by", "referral_link"
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

    def get_referred_by(self, obj):
        return obj.referred_by.email if obj.referred_by else None

    def get_referral_link(self, obj):
        if not obj.referral_code:
            return None
        return f"/register/?referral_code={obj.referral_code}"

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


class SocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLink
        fields = ['id', 'name', 'url', 'icon', 'is_active', 'order', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
