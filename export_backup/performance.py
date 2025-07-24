#!/usr/bin/env python3
"""
Performance optimization module for FAL.AI Video Generator
Caching, async operations, batch processing, and performance monitoring
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import aiofiles
try:
    import aiohttp
except ImportError:
    aiohttp = None
from functools import wraps
try:
    import redis.asyncio as redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)


# ========================================================================
#                            Performance Metrics                         
# ========================================================================

@dataclass
class PerformanceMetrics:
    """Track performance metrics"""
    operation_name: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration: Optional[float] = None
    cache_hit: bool = False
    file_size: Optional[int] = None
    error: Optional[str] = None
    
    def finish(self, error: Optional[str] = None):
        """Mark operation as finished"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.error = error


class PerformanceMonitor:
    """Monitor and track performance metrics"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.operation_counts: Dict[str, int] = {}
        self.total_time: Dict[str, float] = {}
        self.cache_hit_rates: Dict[str, float] = {}
    
    def start_operation(self, operation_name: str) -> PerformanceMetrics:
        """Start tracking an operation"""
        metric = PerformanceMetrics(operation_name)
        self.metrics.append(metric)
        return metric
    
    def record_operation(self, metric: PerformanceMetrics):
        """Record completed operation"""
        if metric.duration is None:
            metric.finish()
        
        op_name = metric.operation_name
        self.operation_counts[op_name] = self.operation_counts.get(op_name, 0) + 1
        self.total_time[op_name] = self.total_time.get(op_name, 0) + metric.duration
        
        # Update cache hit rate
        if op_name not in self.cache_hit_rates:
            self.cache_hit_rates[op_name] = 0
        
        current_count = self.operation_counts[op_name]
        current_rate = self.cache_hit_rates[op_name]
        if metric.cache_hit:
            self.cache_hit_rates[op_name] = (current_rate * (current_count - 1) + 1) / current_count
        else:
            self.cache_hit_rates[op_name] = (current_rate * (current_count - 1)) / current_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = {}
        for op_name in self.operation_counts:
            count = self.operation_counts[op_name]
            total_time = self.total_time[op_name]
            avg_time = total_time / count if count > 0 else 0
            cache_hit_rate = self.cache_hit_rates.get(op_name, 0)
            
            stats[op_name] = {
                "count": count,
                "total_time": total_time,
                "avg_time": avg_time,
                "cache_hit_rate": cache_hit_rate
            }
        
        return stats


# Global performance monitor
performance_monitor = PerformanceMonitor()


# ========================================================================
#                              Caching System                            
# ========================================================================

class CacheManager:
    """Advanced caching with Redis backend and intelligent invalidation"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.local_cache: Dict[str, Any] = {}
        self.cache_stats = {"hits": 0, "misses": 0, "errors": 0}
    
    async def connect(self):
        """Connect to Redis"""
        if redis is None:
            logger.warning("⚠️ Redis module not available, using local cache only")
            self.redis_client = None
            return
            
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            logger.info("✅ Connected to Redis cache")
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable, using local cache: {e}")
            self.redis_client = None
    
    async def get(self, key: str, default=None) -> Any:
        """Get value from cache with fallback chain"""
        cache_key = self._make_key(key)
        
        try:
            # Try Redis first
            if self.redis_client:
                value = await self.redis_client.get(cache_key)
                if value is not None:
                    self.cache_stats["hits"] += 1
                    return json.loads(value)
            
            # Fallback to local cache
            if cache_key in self.local_cache:
                entry = self.local_cache[cache_key]
                if entry["expires"] > time.time():
                    self.cache_stats["hits"] += 1
                    return entry["value"]
                else:
                    del self.local_cache[cache_key]
            
            self.cache_stats["misses"] += 1
            return default
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self.cache_stats["errors"] += 1
            return default
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL"""
        cache_key = self._make_key(key)
        serialized_value = json.dumps(value, default=str)
        
        try:
            # Store in Redis
            if self.redis_client:
                await self.redis_client.setex(cache_key, ttl, serialized_value)
            
            # Store in local cache as backup
            self.local_cache[cache_key] = {
                "value": value,
                "expires": time.time() + ttl
            }
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self.cache_stats["errors"] += 1
    
    async def delete(self, key: str):
        """Delete key from cache"""
        cache_key = self._make_key(key)
        
        try:
            if self.redis_client:
                await self.redis_client.delete(cache_key)
            
            self.local_cache.pop(cache_key, None)
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
    
    def _make_key(self, key: str) -> str:
        """Create cache key with namespace"""
        return f"fal_video_gen:{key}"
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.cache_stats,
            "hit_rate": round(hit_rate, 2),
            "local_cache_size": len(self.local_cache)
        }


# Global cache manager
cache_manager = CacheManager()


# ========================================================================
#                          Performance Decorators                        
# ========================================================================

def performance_monitor_decorator(operation_name: str = None):
    """Decorator to monitor function performance"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            metric = performance_monitor.start_operation(op_name)
            
            try:
                result = await func(*args, **kwargs)
                metric.finish()
                performance_monitor.record_operation(metric)
                return result
            except Exception as e:
                metric.finish(error=str(e))
                performance_monitor.record_operation(metric)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            metric = performance_monitor.start_operation(op_name)
            
            try:
                result = func(*args, **kwargs)
                metric.finish()
                performance_monitor.record_operation(metric)
                return result
            except Exception as e:
                metric.finish(error=str(e))
                performance_monitor.record_operation(metric)
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def cache_result(ttl: int = 3600, key_func: Optional[Callable] = None):
    """Decorator to cache function results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
                cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we can't use async cache directly
            # This would need to be handled differently in a real implementation
            return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


# ========================================================================
#                          Async File Operations                         
# ========================================================================

class AsyncFileManager:
    """High-performance async file operations with caching"""
    
    def __init__(self, chunk_size: int = 8192):
        self.chunk_size = chunk_size
        self.file_cache: Dict[str, bytes] = {}
        self.max_cache_size = 100 * 1024 * 1024  # 100MB max cache
        self.current_cache_size = 0
    
    @performance_monitor_decorator("file_read")
    async def read_file(self, file_path: str, use_cache: bool = True) -> bytes:
        """Async file reading with optional caching"""
        path_obj = Path(file_path)
        
        if not path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check cache first
        if use_cache and file_path in self.file_cache:
            return self.file_cache[file_path]
        
        # Read file asynchronously
        async with aiofiles.open(file_path, 'rb') as f:
            data = await f.read()
        
        # Cache small files
        if use_cache and len(data) < 10 * 1024 * 1024:  # Cache files < 10MB
            self._add_to_cache(file_path, data)
        
        return data
    
    @performance_monitor_decorator("file_write")
    async def write_file(self, file_path: str, data: bytes) -> None:
        """Async file writing"""
        path_obj = Path(file_path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(data)
    
    @performance_monitor_decorator("file_copy")
    async def copy_file(self, src_path: str, dst_path: str) -> None:
        """Async file copying with chunked reading"""
        dst_obj = Path(dst_path)
        dst_obj.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(src_path, 'rb') as src, \
                   aiofiles.open(dst_path, 'wb') as dst:
            
            while True:
                chunk = await src.read(self.chunk_size)
                if not chunk:
                    break
                await dst.write(chunk)
    
    def _add_to_cache(self, file_path: str, data: bytes):
        """Add file to cache with size management"""
        data_size = len(data)
        
        # Check if we need to free up space
        while self.current_cache_size + data_size > self.max_cache_size and self.file_cache:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self.file_cache))
            old_data = self.file_cache.pop(oldest_key)
            self.current_cache_size -= len(old_data)
        
        # Add to cache
        self.file_cache[file_path] = data
        self.current_cache_size += data_size
    
    def clear_cache(self):
        """Clear file cache"""
        self.file_cache.clear()
        self.current_cache_size = 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get file cache statistics"""
        return {
            "cached_files": len(self.file_cache),
            "cache_size_mb": round(self.current_cache_size / 1024 / 1024, 2),
            "max_cache_size_mb": round(self.max_cache_size / 1024 / 1024, 2)
        }


# Global async file manager
async_file_manager = AsyncFileManager()


# ========================================================================
#                            Batch Processing                            
# ========================================================================

class BatchProcessor:
    """Batch processing for video generation requests"""
    
    def __init__(self, batch_size: int = 5, timeout: float = 30.0):
        self.batch_size = batch_size
        self.timeout = timeout
        self.pending_requests: List[Dict[str, Any]] = []
        self.processing_lock = asyncio.Lock()
        self.batch_counter = 0
    
    async def add_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add request to batch and process when ready"""
        async with self.processing_lock:
            self.pending_requests.append(request_data)
            
            # Process batch if we have enough requests or timeout occurred
            if len(self.pending_requests) >= self.batch_size:
                return await self._process_batch()
            else:
                # Wait for more requests or timeout
                return await self._wait_and_process(request_data)
    
    async def _wait_and_process(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Wait for timeout or more requests"""
        start_time = time.time()
        
        while len(self.pending_requests) < self.batch_size:
            if time.time() - start_time > self.timeout:
                break
            await asyncio.sleep(0.1)
        
        return await self._process_batch()
    
    @performance_monitor_decorator("batch_processing")
    async def _process_batch(self) -> Dict[str, Any]:
        """Process current batch of requests"""
        if not self.pending_requests:
            return {}
        
        self.batch_counter += 1
        batch_id = f"batch_{self.batch_counter}_{int(time.time())}"
        current_batch = self.pending_requests.copy()
        self.pending_requests.clear()
        
        logger.info(f"Processing batch {batch_id} with {len(current_batch)} requests")
        
        # Group requests by model for efficiency
        model_groups = {}
        for request in current_batch:
            model = request.get('model', 'default')
            if model not in model_groups:
                model_groups[model] = []
            model_groups[model].append(request)
        
        # Process each model group
        results = {}
        tasks = []
        
        for model, requests in model_groups.items():
            task = self._process_model_group(model, requests)
            tasks.append(task)
        
        # Wait for all model groups to complete
        group_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        for group_result in group_results:
            if isinstance(group_result, dict):
                results.update(group_result)
            else:
                logger.error(f"Batch processing error: {group_result}")
        
        return results
    
    async def _process_model_group(self, model: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process requests for a specific model"""
        results = {}
        
        # TODO: Implement actual batch processing logic for each model
        # This would depend on the FAL.AI API capabilities
        
        for request in requests:
            request_id = request.get('id', f"req_{int(time.time())}")
            # Simulate processing
            await asyncio.sleep(0.1)
            results[request_id] = {
                "status": "processed",
                "model": model,
                "batch_processed": True
            }
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get batch processing statistics"""
        return {
            "pending_requests": len(self.pending_requests),
            "batch_counter": self.batch_counter,
            "batch_size": self.batch_size,
            "timeout": self.timeout
        }


# Global batch processor
batch_processor = BatchProcessor()


# ========================================================================
#                         Performance Utilities                          
# ========================================================================

class PerformanceOptimizer:
    """Main performance optimization coordinator"""
    
    def __init__(self):
        self.startup_time = time.time()
        self.optimization_enabled = True
    
    async def initialize(self):
        """Initialize all performance components"""
        logger.info("🚀 Initializing performance optimizations...")
        
        # Connect to cache
        await cache_manager.connect()
        
        # Warm up file cache with common files
        await self._warmup_cache()
        
        logger.info("✅ Performance optimizations initialized")
    
    async def _warmup_cache(self):
        """Warm up cache with frequently accessed data"""
        try:
            # Cache common configuration
            common_configs = {
                "models": {
                    "kling_pro": "fal-ai/kling-video/v1/pro/image-to-video",
                    "kling_v16": "fal-ai/kling-video/v1.6/pro/image-to-video"
                },
                "aspect_ratios": ["16:9", "9:16", "1:1", "4:3"],
                "max_durations": {"kling_pro": 10, "kling_v16": 5}
            }
            
            for key, value in common_configs.items():
                await cache_manager.set(f"config:{key}", value, ttl=86400)  # 24 hours
            
            logger.info("🔥 Cache warmed up with common configurations")
            
        except Exception as e:
            logger.warning(f"Cache warmup failed: {e}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        uptime = time.time() - self.startup_time
        
        return {
            "uptime_seconds": round(uptime, 2),
            "optimization_enabled": self.optimization_enabled,
            "performance_metrics": performance_monitor.get_stats(),
            "cache_stats": cache_manager.get_stats(),
            "file_cache_stats": async_file_manager.get_cache_stats(),
            "batch_processor_stats": batch_processor.get_stats(),
            "memory_usage_mb": self._get_memory_usage()
        }
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage"""
        try:
            import psutil
            process = psutil.Process()
            return round(process.memory_info().rss / 1024 / 1024, 2)
        except ImportError:
            return 0.0
    
    async def cleanup(self):
        """Cleanup performance resources"""
        logger.info("🧹 Cleaning up performance resources...")
        
        async_file_manager.clear_cache()
        
        if cache_manager.redis_client:
            await cache_manager.redis_client.close()
        
        logger.info("✅ Performance cleanup completed")


# Global performance optimizer
performance_optimizer = PerformanceOptimizer()


# ========================================================================
#                           API Integration                              
# ========================================================================

async def optimized_api_call(url: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
    """Optimized API calls with caching and retry logic"""
    if aiohttp is None:
        raise ImportError("aiohttp is required for optimized API calls")
        
    cache_key = f"api:{hashlib.md5(f'{url}:{method}:{str(kwargs)}'.encode()).hexdigest()}"
    
    # Try cache first for GET requests
    if method == "GET":
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
    
    # Make API call with performance monitoring
    metric = performance_monitor.start_operation("api_call")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, **kwargs) as response:
                result = await response.json()
                
                # Cache successful GET requests
                if method == "GET" and response.status == 200:
                    await cache_manager.set(cache_key, result, ttl=300)  # 5 minutes
                
                metric.finish()
                performance_monitor.record_operation(metric)
                return result
                
    except Exception as e:
        metric.finish(error=str(e))
        performance_monitor.record_operation(metric)
        raise


# ========================================================================
#                            Export Functions                            
# ========================================================================

__all__ = [
    'performance_monitor',
    'cache_manager', 
    'async_file_manager',
    'batch_processor',
    'performance_optimizer',
    'performance_monitor_decorator',
    'cache_result',
    'optimized_api_call'
]