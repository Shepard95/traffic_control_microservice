import json
from channels.generic.websocket import AsyncWebsocketConsumer
import redis
from django.conf import settings

r = redis.Redis.from_url(settings.REDIS_URL)

class TrafficConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.checkpoint_id = self.scope['url_route']['kwargs']['checkpoint_id']
        self.step = 0
        await self.accept()
        await self.send_realtime_data()

    async def send_realtime_data(self):
        """Envía datos de checkpoint en tiempo real"""
        while True:
            data = r.get(f"checkpoint:{self.checkpoint_id}:{self.step}")
            if data:
                await self.send({
                    'type': 'traffic_data',
                    'data': json.loads(data)
                })
                self.step += 1
            await asyncio.sleep(1)
