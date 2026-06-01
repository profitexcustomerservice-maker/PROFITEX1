from rest_framework import serializers
from .models import Task, UserTaskSubmission


class TaskSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = (
            'id', 'title', 'description', 'reward_amount', 'task_type', 'is_active', 
            'media', 'media_type', 'thumbnail_url', 'ad_url', 'required_duration',
            'survey_data', 'premium_only', 'created_at'
        )
    
    def get_thumbnail_url(self, obj):
        """Generate thumbnail URL for task media or link"""
        if obj.media:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.media.url)
            return obj.media.url
        
        # For links without media, could return a generated link preview
        # For now just return None - frontend can use a default placeholder
        return None


class UserTaskSubmissionSerializer(serializers.ModelSerializer):
    task_details = TaskSerializer(source='task', read_only=True)
    minimum_duration_met = serializers.SerializerMethodField()
    
    class Meta:
        model = UserTaskSubmission
        fields = (
            'id', 'user', 'task', 'task_details', 'status', 'submitted_data', 
            'time_spent', 'timer_started_at', 'timer_completed_at', 'link_opened_at',
            'admin_comment', 'submitted_at', 'reviewed_at', 'minimum_duration_met'
        )
        read_only_fields = ('status', 'submitted_at', 'reviewed_at', 'admin_comment', 'task_details', 'minimum_duration_met')

    def get_minimum_duration_met(self, obj):
        """Check if submission meets minimum duration requirement"""
        return obj.is_minimum_duration_met()

    def validate(self, attrs):
        user = attrs.get('user') or self.context['request'].user
        task = attrs.get('task')
        
        # Prevent duplicate pending/approved submissions for same task
        if UserTaskSubmission.objects.filter(user=user, task=task).exclude(status=UserTaskSubmission.Status.REJECTED).exists():
            raise serializers.ValidationError('You have an existing pending or approved submission for this task.')
        
        # Check minimum duration for tasks that require it
        if task.required_duration and attrs.get('time_spent', 0) < task.required_duration:
            raise serializers.ValidationError(
                f'You must spend at least {task.required_duration} seconds on this task. '
                f'You spent {attrs.get("time_spent", 0)} seconds.'
            )
        
        return attrs

    def create(self, validated_data):
        # ensure user is set to request user
        if 'user' not in validated_data:
            validated_data['user'] = self.context['request'].user
        
        # Set timer completion time if time was spent
        if validated_data.get('time_spent', 0) > 0 and not validated_data.get('timer_completed_at'):
            from django.utils import timezone
            validated_data['timer_completed_at'] = timezone.now()
        
        return super().create(validated_data)
