"""Cliente Redis asíncrono para caché de respuestas de Moodle."""

import hashlib
import json
from typing import Any

import redis.asyncio as aioredis

from app.core.environment import environment


class RedisClient:
    """Cliente Redis asíncrono con métodos de caché."""

    def __init__(self):
        self.redis: aioredis.Redis | None = None

    async def connect(self) -> None:
        """Conecta al servidor Redis. Si falla, opera sin caché."""
        try:
            self.redis = aioredis.Redis(
                host=environment.REDIS_HOST,
                port=environment.REDIS_PORT,
                db=environment.REDIS_DB,
                password=environment.REDIS_PASSWORD or None,
                decode_responses=True,
            )
            await self.redis.ping()
            print("✅ Redis conectado")
        except Exception as e:
            print(f"⚠️ Redis no disponible, operando sin caché: {e}")
            self.redis = None

    async def disconnect(self) -> None:
        """Cierra la conexión a Redis."""
        if self.redis:
            await self.redis.close()

    async def get(self, key: str) -> dict | None:
        """Obtiene un valor del caché y lo deserializa desde JSON."""
        if not self.redis:
            return None
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Guarda un valor en caché serializado como JSON."""
        if not self.redis:
            return
        ttl = ttl or environment.REDIS_CACHE_TTL
        await self.redis.setex(key, ttl, json.dumps(value, default=str))

    async def delete(self, key: str) -> None:
        """Elimina una clave del caché."""
        if self.redis:
            await self.redis.delete(key)

    async def delete_pattern(self, pattern: str) -> None:
        """Elimina todas las claves que coinciden con un patrón."""
        if not self.redis:
            return
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break

    @staticmethod
    def build_key(prefix: str, **kwargs) -> str:
        """Construye una clave de caché a partir de parámetros."""
        raw = json.dumps(kwargs, sort_keys=True, default=str)
        hashed = hashlib.md5(raw.encode()).hexdigest()
        return f"moodle:{prefix}:{hashed}"


# Instancia global del cliente Redis
redis_client = RedisClient()
