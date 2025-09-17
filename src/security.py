import streamlit as st
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import uuid
from better_profanity import profanity
import os

class SecurityManager:
    """Handles authentication, rate limiting, and content safety"""
    
    def __init__(self, database_manager):
        self.db = database_manager
        self.admin_session_timeout = 3600  # 1 hour
        profanity.load_censor_words()
        
    def create_admin_session(self, password: str) -> bool:
        """Create admin session with timeout"""
        correct_password = os.getenv('ADMIN_PASSWORD', 'AgentComponents2024!')
        
        if self.verify_password(password, correct_password):
            session_id = str(uuid.uuid4())
            expires_at = datetime.now() + timedelta(seconds=self.admin_session_timeout)
            
            st.session_state.admin_session_id = session_id
            st.session_state.admin_expires_at = expires_at
            
            # Log admin access
            self.db.log_admin_access(session_id, st.session_state.get('client_ip', 'unknown'))
            return True
        return False
    
    def verify_password(self, provided_password: str, correct_password: str) -> bool:
        """Secure password verification"""
        return hmac.compare_digest(provided_password, correct_password)
    
    def is_admin_authenticated(self) -> bool:
        """Check if current session is authenticated admin"""
        if not hasattr(st.session_state, 'admin_session_id'):
            return False
        
        if not hasattr(st.session_state, 'admin_expires_at'):
            return False
        
        if datetime.now() > st.session_state.admin_expires_at:
            self.logout_admin()
            return False
        
        return True
    
    def logout_admin(self):
        """Clear admin session"""
        if hasattr(st.session_state, 'admin_session_id'):
            del st.session_state.admin_session_id
        if hasattr(st.session_state, 'admin_expires_at'):
            del st.session_state.admin_expires_at
    
    def check_ip_rate_limit(self, ip_address: str) -> Dict[str, any]:
        """Check IP-based rate limiting"""
        limits = {
            'requests_per_hour': 10,
            'requests_per_day': 50
        }
        
        usage = self.db.get_ip_usage(ip_address)
        
        current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
        current_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        hourly_count = sum(1 for req in usage if req['timestamp'] >= current_hour)
        daily_count = sum(1 for req in usage if req['timestamp'] >= current_day)
        
        return {
            'allowed': hourly_count < limits['requests_per_hour'] and daily_count < limits['requests_per_day'],
            'hourly_remaining': max(0, limits['requests_per_hour'] - hourly_count),
            'daily_remaining': max(0, limits['requests_per_day'] - daily_count),
            'reset_time': current_hour + timedelta(hours=1)
        }
    
    def log_request(self, ip_address: str, request_type: str, topic: str = None):
        """Log request for rate limiting and analytics"""
        self.db.log_user_request(ip_address, request_type, topic)
    
    def content_safety_check(self, text: str) -> Dict[str, any]:
        """Comprehensive content safety check"""
        issues = []
        severity = 'safe'
        
        # Profanity check
        if profanity.contains_profanity(text):
            issues.append('Contains inappropriate language')
            severity = 'warning'
        
        # Length check
        if len(text) > 2000:
            issues.append('Content too long')
            severity = 'warning'
        
        # Basic spam detection
        if self._detect_spam_patterns(text):
            issues.append('Potential spam detected')
            severity = 'warning'
        
        # Harmful content patterns
        if self._detect_harmful_content(text):
            issues.append('Potentially harmful content detected')
            severity = 'blocked'
        
        return {
            'safe': severity != 'blocked',
            'severity': severity,
            'issues': issues,
            'sanitized_text': profanity.censor(text) if profanity.contains_profanity(text) else text
        }
    
    def _detect_spam_patterns(self, text: str) -> bool:
        """Detect spam patterns"""
        spam_indicators = [
            text.count('!') > 5,  # Too many exclamation marks
            text.count('$') > 3,  # Multiple dollar signs
            len(set(text.split())) < len(text.split()) * 0.5,  # Too much repetition
            'click here' in text.lower(),
            'buy now' in text.lower(),
            'free money' in text.lower()
        ]
        return any(spam_indicators)
    
    def _detect_harmful_content(self, text: str) -> bool:
        """Detect potentially harmful content"""
        harmful_patterns = [
            'violence',
            'hate speech',
            'self-harm',
            'illegal activities',
            'discrimination'
        ]
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in harmful_patterns)
    
    def get_client_ip(self) -> str:
        """Get client IP address safely"""
        # Streamlit doesn't provide direct IP access, use session-based tracking
        if 'client_id' not in st.session_state:
            st.session_state.client_id = str(uuid.uuid4())
        
        return st.session_state.client_id
    
    def require_admin(self):
        """Decorator-like function to require admin authentication"""
        if not self.is_admin_authenticated():
            st.error("Admin authentication required")
            
            with st.form("admin_login"):
                password = st.text_input("Admin Password", type="password")
                if st.form_submit_button("Login"):
                    if self.create_admin_session(password):
                        st.success("Admin authenticated")
                        st.rerun()
                    else:
                        st.error("Invalid password")
                        # Log failed attempt
                        self.db.log_security_event("failed_admin_login", self.get_client_ip())
            
            st.stop()
    
    def check_system_health(self) -> Dict[str, any]:
        """Check overall system security health"""
        recent_failures = self.db.get_recent_security_events(hours=24)
        
        failed_logins = sum(1 for event in recent_failures if event['event_type'] == 'failed_admin_login')
        rate_limit_hits = sum(1 for event in recent_failures if event['event_type'] == 'rate_limit_exceeded')
        
        health = {
            'status': 'healthy',
            'failed_logins_24h': failed_logins,
            'rate_limit_hits_24h': rate_limit_hits,
            'alerts': []
        }
        
        if failed_logins > 10:
            health['status'] = 'warning'
            health['alerts'].append('High number of failed login attempts')
        
        if rate_limit_hits > 100:
            health['status'] = 'warning'
            health['alerts'].append('High rate limiting activity')
        
        return health
