import json
import jwt
from urllib.parse import parse_qs
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from user.models import User

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope["query_string"].decode() 
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]
        
        # We'll use a specific group for notifications
        self.room_group_name = 'pixel_notifications_group'

        if token:
            try:
                # Use JWT to get the user
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                user = await self.get_user(payload["user_id"])
                self.scope["user"] = user
                
                # Join the notification group
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.accept()
                
            except Exception as e:
                self.scope["user"] = AnonymousUser()
                await self.close(code=4001) 
        else:
            self.scope["user"] = AnonymousUser()
            await self.close(code=4002)

    async def disconnect(self, close_code):
        if self.scope.get("user") and not isinstance(self.scope["user"], AnonymousUser):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        await self.send(text_data=json.dumps({
            'status': 'received'
        }))

    async def send_user_message(self, event):
        """
        Handler for sending messages to a specific user.
        The message is only sent if the user_id in the event matches the current connection's user.
        """
        message = event['data']
        user_id = event.get('user_id')
        current_user = self.scope.get('user')
        
        if current_user and not isinstance(current_user, AnonymousUser):
            if str(current_user.user_id) == str(user_id):
                await self.send(text_data=json.dumps(message))

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return AnonymousUser()
