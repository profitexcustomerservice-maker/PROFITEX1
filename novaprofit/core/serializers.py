from rest_framework import serializers
from .models import Plan, Task, UserTask, UserPlan

class TaskSerializer(serializers.ModelSerializer):
    task_type = serializers.CharField(source='media_type', read_only=True)
    duration = serializers.IntegerField(default=30, read_only=True)
    
    class Meta:
        model = Task
        fields = ("id", "title", "description", "reward", "media", "media_type", "task_type", "duration", "active", "created_at")
        read_only_fields = ("created_at",)

class PlanSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    plan_level = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = Plan
        fields = ("id", "plan_level", "title", "description", "amount", "reward_multiplier", "daily_earning_limit", "max_tasks_per_day", "duration_days", "active", "created_at")
        read_only_fields = ("created_at",)

class UserTaskSerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)
    task_id = serializers.PrimaryKeyRelatedField(queryset=Task.objects.filter(active=True), write_only=True, source="task")

    class Meta:
        model = UserTask
        fields = ("id", "task", "task_id", "completed_at")
        read_only_fields = ("id", "task", "completed_at")

class UserPlanSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(queryset=Plan.objects.filter(active=True), write_only=True, source="plan")

    class Meta:
        model = UserPlan
        fields = ("id", "plan", "plan_id", "joined_at")
        read_only_fields = ("id", "plan", "joined_at")
