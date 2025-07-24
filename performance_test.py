#!/usr/bin/env python3
"""
Performance Testing Suite for FAL.AI Video Generator
Comprehensive load testing, stress testing, and performance validation
"""

import asyncio
import aiohttp
import time
import json
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TestMetrics:
    """Performance test metrics"""
    test_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    response_times: List[float] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)
    start_time: float = 0
    end_time: float = 0
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def avg_response_time(self) -> float:
        if not self.response_times:
            return 0
        return statistics.mean(self.response_times)
    
    @property
    def p95_response_time(self) -> float:
        if not self.response_times:
            return 0
        return statistics.quantiles(self.response_times, n=20)[18]  # 95th percentile
    
    @property
    def total_duration(self) -> float:
        return self.end_time - self.start_time
    
    @property
    def requests_per_second(self) -> float:
        if self.total_duration == 0:
            return 0
        return self.total_requests / self.total_duration


class PerformanceTester:
    """Comprehensive performance testing suite"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8001"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.test_results: Dict[str, TestMetrics] = {}
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def run_all_tests(self) -> Dict[str, TestMetrics]:
        """Run complete performance test suite"""
        logger.info("🚀 Starting comprehensive performance test suite...")
        
        # Test sequence with increasing complexity
        tests = [
            ("basic_health_check", self.test_basic_endpoints),
            ("load_models_performance", self.test_models_endpoint_load),
            ("file_upload_performance", self.test_file_upload_performance),
            ("concurrent_users", self.test_concurrent_users),
            ("rate_limiting", self.test_rate_limiting),
            ("memory_stress", self.test_memory_stress),
            ("sustained_load", self.test_sustained_load),
        ]
        
        for test_name, test_func in tests:
            logger.info(f"📊 Running test: {test_name}")
            try:
                await test_func()
                logger.info(f"✅ Test {test_name} completed successfully")
            except Exception as e:
                logger.error(f"❌ Test {test_name} failed: {e}")
                # Continue with other tests
        
        # Generate final report
        self.generate_performance_report()
        return self.test_results
    
    async def test_basic_endpoints(self):
        """Test basic endpoint performance"""
        metrics = TestMetrics("basic_health_check")
        metrics.start_time = time.time()
        
        endpoints = [
            "/",
            "/api/models",
            "/api/performance",
        ]
        
        for endpoint in endpoints:
            for _ in range(10):  # 10 requests per endpoint
                start_time = time.time()
                try:
                    async with self.session.get(f"{self.base_url}{endpoint}") as response:
                        await response.text()
                        response_time = time.time() - start_time
                        
                        metrics.total_requests += 1
                        metrics.response_times.append(response_time)
                        
                        if response.status == 200:
                            metrics.successful_requests += 1
                        else:
                            metrics.failed_requests += 1
                            metrics.error_messages.append(f"HTTP {response.status} for {endpoint}")
                            
                except Exception as e:
                    metrics.total_requests += 1
                    metrics.failed_requests += 1
                    metrics.error_messages.append(f"Exception for {endpoint}: {str(e)}")
        
        metrics.end_time = time.time()
        self.test_results["basic_health_check"] = metrics
    
    async def test_models_endpoint_load(self):
        """Test models endpoint under load"""
        metrics = TestMetrics("load_models_performance")
        metrics.start_time = time.time()
        
        # Concurrent requests to models endpoint
        tasks = []
        for _ in range(50):  # 50 concurrent requests
            task = self._make_request("/api/models", metrics)
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        metrics.end_time = time.time()
        self.test_results["load_models_performance"] = metrics
    
    async def test_file_upload_performance(self):
        """Test file upload performance with various sizes"""
        metrics = TestMetrics("file_upload_performance")
        metrics.start_time = time.time()
        
        # Create test files of different sizes
        test_files = [
            (100 * 1024, "small_100kb.jpg"),      # 100KB
            (500 * 1024, "medium_500kb.jpg"),     # 500KB
            (1024 * 1024, "large_1mb.jpg"),       # 1MB
            (5 * 1024 * 1024, "xlarge_5mb.jpg"),  # 5MB
        ]
        
        for file_size, filename in test_files:
            # Create fake JPEG data
            jpeg_header = b'\\xff\\xd8\\xff\\xe0\\x00\\x10JFIF'
            fake_data = jpeg_header + b'\\x00' * (file_size - len(jpeg_header))
            
            for attempt in range(3):  # 3 attempts per file size
                start_time = time.time()
                try:
                    data = aiohttp.FormData()
                    data.add_field('file', fake_data, filename=filename, content_type='image/jpeg')
                    
                    async with self.session.post(f"{self.base_url}/api/upload", data=data) as response:
                        await response.text()
                        response_time = time.time() - start_time
                        
                        metrics.total_requests += 1
                        metrics.response_times.append(response_time)
                        
                        if response.status in [200, 413]:  # 413 = Payload too large (expected for large files)
                            metrics.successful_requests += 1
                        else:
                            metrics.failed_requests += 1
                            metrics.error_messages.append(f"Upload failed: HTTP {response.status}")
                
                except Exception as e:
                    metrics.total_requests += 1
                    metrics.failed_requests += 1
                    metrics.error_messages.append(f"Upload exception: {str(e)}")
        
        metrics.end_time = time.time()
        self.test_results["file_upload_performance"] = metrics
    
    async def test_concurrent_users(self):
        """Simulate concurrent users accessing the application"""
        metrics = TestMetrics("concurrent_users")
        metrics.start_time = time.time()
        
        # Simulate 20 concurrent users, each making 5 requests
        user_tasks = []
        
        for user_id in range(20):
            user_task = self._simulate_user_session(user_id, metrics)
            user_tasks.append(user_task)
        
        await asyncio.gather(*user_tasks, return_exceptions=True)
        
        metrics.end_time = time.time()
        self.test_results["concurrent_users"] = metrics
    
    async def _simulate_user_session(self, user_id: int, metrics: TestMetrics):
        """Simulate a realistic user session"""
        user_actions = [
            "/",
            "/api/models",
            "/api/performance",
            "/api/history",
        ]
        
        for action in user_actions:
            await asyncio.sleep(0.5)  # Realistic user think time
            await self._make_request(action, metrics)
    
    async def test_rate_limiting(self):
        """Test rate limiting functionality"""
        metrics = TestMetrics("rate_limiting")
        metrics.start_time = time.time()
        
        # Rapid requests to trigger rate limiting
        tasks = []
        for _ in range(100):  # 100 rapid requests
            task = self._make_request("/api/models", metrics)
            tasks.append(task)
        
        # Execute all at once to trigger rate limits
        await asyncio.gather(*tasks, return_exceptions=True)
        
        metrics.end_time = time.time()
        self.test_results["rate_limiting"] = metrics
    
    async def test_memory_stress(self):
        """Test memory usage under stress"""
        metrics = TestMetrics("memory_stress")
        metrics.start_time = time.time()
        
        # Create multiple concurrent sessions to test memory handling
        sessions = []
        try:
            # Create 50 concurrent sessions
            for _ in range(50):
                session = aiohttp.ClientSession()
                sessions.append(session)
            
            # Make requests with all sessions
            tasks = []
            for session in sessions:
                for _ in range(5):  # 5 requests per session
                    task = self._make_request_with_session(session, "/api/models", metrics)
                    tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
        finally:
            # Clean up sessions
            for session in sessions:
                await session.close()
        
        metrics.end_time = time.time()
        self.test_results["memory_stress"] = metrics
    
    async def test_sustained_load(self):
        """Test sustained load over time"""
        metrics = TestMetrics("sustained_load")
        metrics.start_time = time.time()
        
        # Run sustained load for 60 seconds
        end_time = time.time() + 60
        
        while time.time() < end_time:
            # Batch of requests every second
            tasks = []
            for _ in range(10):  # 10 requests per second
                task = self._make_request("/api/models", metrics)
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(1)  # Wait 1 second before next batch
        
        metrics.end_time = time.time()
        self.test_results["sustained_load"] = metrics
    
    async def _make_request(self, endpoint: str, metrics: TestMetrics):
        """Make a single request and record metrics"""
        return await self._make_request_with_session(self.session, endpoint, metrics)
    
    async def _make_request_with_session(self, session: aiohttp.ClientSession, endpoint: str, metrics: TestMetrics):
        """Make a request with a specific session"""
        start_time = time.time()
        try:
            async with session.get(f"{self.base_url}{endpoint}") as response:
                await response.text()
                response_time = time.time() - start_time
                
                metrics.total_requests += 1
                metrics.response_times.append(response_time)
                
                if response.status in [200, 429]:  # 429 = Rate limited (expected)
                    metrics.successful_requests += 1
                else:
                    metrics.failed_requests += 1
                    metrics.error_messages.append(f"HTTP {response.status} for {endpoint}")
        
        except Exception as e:
            metrics.total_requests += 1
            metrics.failed_requests += 1
            metrics.error_messages.append(f"Exception for {endpoint}: {str(e)}")
    
    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        report = {
            "test_summary": {
                "total_tests": len(self.test_results),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "base_url": self.base_url
            },
            "test_results": {}
        }
        
        for test_name, metrics in self.test_results.items():
            report["test_results"][test_name] = {
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "success_rate": round(metrics.success_rate, 2),
                "avg_response_time_ms": round(metrics.avg_response_time * 1000, 2),
                "p95_response_time_ms": round(metrics.p95_response_time * 1000, 2),
                "requests_per_second": round(metrics.requests_per_second, 2),
                "total_duration_seconds": round(metrics.total_duration, 2),
                "error_messages": metrics.error_messages[:5]  # First 5 errors
            }
        
        # Save report to file
        report_path = Path("performance_test_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Performance report saved to: {report_path}")
        
        # Print summary
        self._print_summary(report)
    
    def _print_summary(self, report: Dict[str, Any]):
        """Print performance test summary"""
        print("\\n" + "="*80)
        print("📊 PERFORMANCE TEST SUMMARY")
        print("="*80)
        
        for test_name, results in report["test_results"].items():
            print(f"\\n🔍 {test_name.upper()}")
            print(f"   Requests: {results['total_requests']} total, {results['successful_requests']} successful")
            print(f"   Success Rate: {results['success_rate']}%")
            print(f"   Avg Response Time: {results['avg_response_time_ms']}ms")
            print(f"   95th Percentile: {results['p95_response_time_ms']}ms")
            print(f"   Throughput: {results['requests_per_second']} req/sec")
            
            if results['error_messages']:
                print(f"   Sample Errors: {results['error_messages'][:2]}")
        
        print("\\n" + "="*80)


async def main():
    """Run performance test suite"""
    try:
        async with PerformanceTester() as tester:
            await tester.run_all_tests()
    except Exception as e:
        logger.error(f"Performance test suite failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))