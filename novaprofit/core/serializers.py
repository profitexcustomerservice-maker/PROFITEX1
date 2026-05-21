from rest_framework import serializers
from .models import Plan, Task, UserTask, UserPlan

class TaskSerializer(serializers.ModelSerializer):
    task_type = serializers.CharField(source='media_type', read_only=True)
    duration = serializers.IntegerField(read_only=True)
    can_perform = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = ("id", "title", "description", "reward", "media", "media_type", "task_type", "duration", "active", "created_at", "can_perform")
        read_only_fields = ("created_at",)
    
    def get_can_perform(self, obj):
        """Check if current user can perform this task"""
        from .views import user_can_do_tasks
        
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return user_can_do_tasks(request.user)

class PlanSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    plan_level = serializers.ChoiceField(choices=Plan.PLAN_LEVEL_CHOICES, required=True)

    class Meta:
        model = Plan
        fields = ("id", "plan_level", "title", "description", "amount", "reward_multiplier", "daily_earning_limit", "max_tasks_per_day", "duration_days", "active", "created_at")
        read_only_fields = ("created_at",)

    def validate_plan_level(self, value):
        existing = Plan.objects.filter(plan_level=value)
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError("A plan with this level already exists. Please choose a different plan level.")
        return value

class UserTaskSerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)
    task_id = serializers.PrimaryKeyRelatedField(queryset=Task.objects.filter(active=True), write_only=True, source="task")
    duration_spent = serializers.IntegerField(write_only=True, required=False, min_value=0)

    class Meta:
        model = UserTask
        fields = ("id", "task", "task_id", "completed_at", "duration_spent")
        read_only_fields = ("id", "task", "completed_at")

class UserPlanSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(queryset=Plan.objects.filter(active=True), write_only=True, source="plan")

    class Meta:
        model = UserPlan
        fields = ("id", "plan", "plan_id", "joined_at")
        read_only_fields = ("id", "plan", "joined_at")

    def validate(self, attrs):
        user = self.context.get("request").user if self.context.get("request") else None
        if user and UserPlan.objects.filter(user=user).exists():
            raise serializers.ValidationError("You have already joined a plan.")
        return attrs
