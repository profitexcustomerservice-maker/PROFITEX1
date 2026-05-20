from rest_framework import serializers
from .models import Task, UserTaskSubmission


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('id', 'title', 'description', 'reward_amount', 'task_type', 'is_active', 'created_at')


class UserTaskSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTaskSubmission
        fields = ('id', 'user', 'task', 'status', 'submitted_data', 'admin_comment', 'submitted_at', 'reviewed_at')
        read_only_fields = ('status', 'submitted_at', 'reviewed_at', 'admin_comment')

    def validate(self, attrs):
        user = attrs.get('user') or self.context['request'].user
        task = attrs.get('task')
        # Prevent duplicate pending/approved submissions for same task
        if UserTaskSubmission.objects.filter(user=user, task=task).exclude(status=UserTaskSubmission.Status.REJECTED).exists():
            raise serializers.ValidationError('You have an existing pending or approved submission for this task.')
        return attrs

    def create(self, validated_data):
        # ensure user is set to request user
        if 'user' not in validated_data:
            validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
