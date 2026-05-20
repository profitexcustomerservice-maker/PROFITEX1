# WebSocket signals temporarily disabled due to Channels version compatibility
# TODO: Fix Channels integration for real-time notifications
# from asgiref.sync import async_to_sync
# from channels.layers import get_channel_layer
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import Notification

# @receiver(post_save, sender=Notification)
# def send_notification_ws(sender, instance, created, **kwargs):
#     if not created:
#         return
#     channel_layer = get_channel_layer()
#     group_name = f"user_{instance.user.id}"
#     payload = {
#         "type": "notification_message",
#         "data": {
#             "title": instance.title,
#             "message": instance.message,
#             "created_at": instance.created_at.isoformat(),
#             "is_read": instance.is_read,
#         },
#     }
#     async_to_sync(channel_layer.group_send)(group_name, payload)
