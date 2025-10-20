#!/usr/bin/env python3
"""
Service untuk caching data dashboard agar tidak perlu reload
"""

import redis
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        self.redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        try:
            self.redis_client = redis.Redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            self.enabled = True
            logger.info("Cache service enabled with Redis")
        except:
            self.redis_client = None
            self.enabled = False
            logger.warning("Cache service disabled - Redis not available")
    
    def _get_cache_key(self, prefix: str, user_id: str, *args) -> str:
        """Generate cache key"""
        key_parts = [prefix, user_id] + [str(arg) for arg in args if arg is not None]
        return ":".join(key_parts)
    
    def set_cache(self, key: str, data: Any, ttl_seconds: int = 300) -> bool:
        """Set cache data"""
        if not self.enabled:
            return False
        
        try:
            serialized_data = json.dumps(data, default=str)
            self.redis_client.setex(key, ttl_seconds, serialized_data)
            return True
        except Exception as e:
            logger.error(f"Failed to set cache {key}: {e}")
            return False
    
    def get_cache(self, key: str) -> Optional[Any]:
        """Get cache data"""
        if not self.enabled:
            return None
        
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get cache {key}: {e}")
            return None
    
    def delete_cache(self, key: str) -> bool:
        """Delete cache data"""
        if not self.enabled:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache {key}: {e}")
            return False
    
    def invalidate_user_cache(self, user_id: str) -> bool:
        """Invalidate all cache for user"""
        if not self.enabled:
            return False
        
        try:
            pattern = f"dashboard:*:{user_id}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate cache for user {user_id}: {e}")
            return False
    
    # Dashboard specific cache methods
    def cache_parent_dashboard_data(self, user_id: str, data: Dict[str, Any]) -> bool:
        """Cache parent dashboard data"""
        key = self._get_cache_key("dashboard", "parent", user_id, "main")
        return self.set_cache(key, data, ttl_seconds=300)  # 5 minutes
    
    def get_parent_dashboard_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached parent dashboard data"""
        key = self._get_cache_key("dashboard", "parent", user_id, "main")
        return self.get_cache(key)
    
    def cache_children_data(self, user_id: str, data: Dict[str, Any]) -> bool:
        """Cache children data"""
        key = self._get_cache_key("dashboard", "parent", user_id, "children")
        return self.set_cache(key, data, ttl_seconds=600)  # 10 minutes
    
    def get_children_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached children data"""
        key = self._get_cache_key("dashboard", "parent", user_id, "children")
        return self.get_cache(key)
    
    def cache_emotion_distribution(self, user_id: str, period: str, data: Dict[str, Any]) -> bool:
        """Cache emotion distribution data"""
        key = self._get_cache_key("dashboard", "parent", user_id, "distribution", period)
        return self.set_cache(key, data, ttl_seconds=180)  # 3 minutes
    
    def get_emotion_distribution(self, user_id: str, period: str) -> Optional[Dict[str, Any]]:
        """Get cached emotion distribution data"""
        key = self._get_cache_key("dashboard", "parent", user_id, "distribution", period)
        return self.get_cache(key)
    
    def cache_child_reports(self, user_id: str, child_id: str, period: str, data: Dict[str, Any]) -> bool:
        """Cache child reports data"""
        key = self._get_cache_key("dashboard", "parent", user_id, "reports", child_id, period)
        return self.set_cache(key, data, ttl_seconds=300)  # 5 minutes
    
    def get_child_reports(self, user_id: str, child_id: str, period: str) -> Optional[Dict[str, Any]]:
        """Get cached child reports data"""
        key = self._get_cache_key("dashboard", "parent", user_id, "reports", child_id, period)
        return self.get_cache(key)
    
    def invalidate_emotion_cache(self, student_id: str) -> bool:
        """Invalidate emotion-related cache when new emotion detected"""
        if not self.enabled:
            return False
        
        try:
            # Invalidate all emotion-related cache
            patterns = [
                f"dashboard:*:*:distribution:*",
                f"dashboard:*:*:reports:*",
                f"dashboard:*:*:main"
            ]
            
            for pattern in patterns:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            
            logger.info(f"Invalidated emotion cache for student {student_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate emotion cache: {e}")
            return False

# Global cache service instance
cache_service = CacheService()
