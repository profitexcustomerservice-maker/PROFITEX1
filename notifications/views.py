from django.shortcuts import render, redirect
from rest_framework import permissions, viewsets
from rest_framework.authentication import SessionAuthentication
from .models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    authentication_classes = (SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_update(self, serializer):
        # Only allow updating the is_read field
        if 'is_read' in self.request.data:
            serializer.save()
        else:
            serializer.save(user=self.request.user)

def notifications_admin_redirect(request):
    return redirect('/admin_panel/')


def notifications_page(request):
    """Render the notifications page"""
    user = request.user
    if not user.is_authenticated:
        return redirect('/login/')
    
    notifications = Notification.objects.filter(user=user).order_by('-created_at')
    
    context = {
        'notifications': notifications,
    }
    return render(request, 'notifications.html', context)
