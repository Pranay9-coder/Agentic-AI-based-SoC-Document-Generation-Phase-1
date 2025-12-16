"""
Centralized Rate Limiter for Gemini API
File: backend/utils/gemini_rate_limiter.py

Prevents quota exhaustion by:
1. Tracking all API calls globally
2. Enforcing wait times between calls
3. Respecting API retry delays
4. Providing quota status
"""
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict


class GeminiRateLimiter:
    """
    Global rate limiter for Gemini API calls
    
    Free Tier Limits:
    - 5 requests per minute
    - 20 requests per day
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern - only one rate limiter instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize rate limiter"""
        if self._initialized:
            return
        
        self._initialized = True
        
        # Configuration (adjust based on your tier)
        self.rpm_limit = 5  # requests per minute
        self.rpd_limit = 20  # requests per day
        
        # Tracking
        self.minute_calls = []  # timestamps of calls in last minute
        self.day_calls = []     # timestamps of calls in last day
        self.last_call_time = None
        self.min_delay = 12  # minimum 12 seconds between calls (5 per minute = 60/5)
        
        # For API-requested delays
        self.forced_wait_until = None
        
        print(f"🎯 Rate Limiter initialized: {self.rpm_limit} RPM, {self.rpd_limit} RPD")
    
    def wait_if_needed(self) -> Dict[str, any]:
        """
        Wait if necessary before making an API call
        Returns status info
        """
        with self._lock:
            now = datetime.now()
            
            # 1. Check if API requested a forced delay
            if self.forced_wait_until and now < self.forced_wait_until:
                wait_seconds = (self.forced_wait_until - now).total_seconds()
                print(f"⏳ API requested delay: waiting {wait_seconds:.1f}s...")
                time.sleep(wait_seconds)
                self.forced_wait_until = None
            
            # 2. Clean old timestamps
            self._clean_old_calls(now)
            
            # 3. Check daily limit
            if len(self.day_calls) >= self.rpd_limit:
                oldest_day_call = self.day_calls[0]
                reset_time = oldest_day_call + timedelta(days=1)
                wait_seconds = (reset_time - now).total_seconds()
                
                if wait_seconds > 0:
                    return {
                        'allowed': False,
                        'reason': 'daily_limit',
                        'wait_seconds': wait_seconds,
                        'daily_used': len(self.day_calls),
                        'daily_limit': self.rpd_limit
                    }
            
            # 4. Check per-minute limit
            if len(self.minute_calls) >= self.rpm_limit:
                oldest_minute_call = self.minute_calls[0]
                reset_time = oldest_minute_call + timedelta(minutes=1)
                wait_seconds = (reset_time - now).total_seconds()
                
                if wait_seconds > 0:
                    print(f"⏳ Per-minute limit: waiting {wait_seconds:.1f}s...")
                    time.sleep(wait_seconds + 0.5)  # Add buffer
                    now = datetime.now()
                    self._clean_old_calls(now)
            
            # 5. Enforce minimum delay between calls
            if self.last_call_time:
                time_since_last = (now - self.last_call_time).total_seconds()
                if time_since_last < self.min_delay:
                    wait_time = self.min_delay - time_since_last
                    print(f"⏳ Rate limiting: waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    now = datetime.now()
            
            # 6. Record this call
            self.minute_calls.append(now)
            self.day_calls.append(now)
            self.last_call_time = now
            
            return {
                'allowed': True,
                'minute_used': len(self.minute_calls),
                'minute_limit': self.rpm_limit,
                'daily_used': len(self.day_calls),
                'daily_limit': self.rpd_limit
            }
    
    def _clean_old_calls(self, now: datetime):
        """Remove timestamps older than tracking window"""
        # Clean minute calls (older than 60 seconds)
        cutoff_minute = now - timedelta(minutes=1)
        self.minute_calls = [t for t in self.minute_calls if t > cutoff_minute]
        
        # Clean day calls (older than 24 hours)
        cutoff_day = now - timedelta(days=1)
        self.day_calls = [t for t in self.day_calls if t > cutoff_day]
    
    def record_api_delay(self, retry_delay_seconds: float):
        """
        Record when API tells us to wait
        
        Args:
            retry_delay_seconds: Seconds to wait as told by API
        """
        with self._lock:
            self.forced_wait_until = datetime.now() + timedelta(seconds=retry_delay_seconds)
            print(f"📝 API requested {retry_delay_seconds:.1f}s delay")
    
    def get_quota_status(self) -> Dict[str, any]:
        """Get current quota usage"""
        with self._lock:
            now = datetime.now()
            self._clean_old_calls(now)
            
            return {
                'minute_used': len(self.minute_calls),
                'minute_limit': self.rpm_limit,
                'minute_remaining': self.rpm_limit - len(self.minute_calls),
                'daily_used': len(self.day_calls),
                'daily_limit': self.rpd_limit,
                'daily_remaining': self.rpd_limit - len(self.day_calls),
                'can_make_call': (
                    len(self.minute_calls) < self.rpm_limit and 
                    len(self.day_calls) < self.rpd_limit
                )
            }
    
    def reset(self):
        """Reset all counters (for testing or quota reset)"""
        with self._lock:
            self.minute_calls = []
            self.day_calls = []
            self.last_call_time = None
            self.forced_wait_until = None
            print("🔄 Rate limiter reset")


# Global instance
_rate_limiter = GeminiRateLimiter()


def get_rate_limiter() -> GeminiRateLimiter:
    """Get the global rate limiter instance"""
    return _rate_limiter