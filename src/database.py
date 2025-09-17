import os
from supabase import create_client, Client
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

class DatabaseManager:
    """Handles all database operations with Supabase"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if self.supabase_url and self.supabase_key:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        else:
            self.supabase = None
            print("Warning: Supabase credentials not found, using fallback storage")
    
    def initialize_tables(self):
        """Initialize database tables if they don't exist"""
        if not self.supabase:
            return False
        
        # Tables will be created via Supabase dashboard/SQL
        # This method validates they exist
        try:
            # Test each table
            self.supabase.table('api_usage').select('*').limit(1).execute()
            self.supabase.table('user_requests').select('*').limit(1).execute()
            self.supabase.table('security_events').select('*').limit(1).execute()
            self.supabase.table('admin_sessions').select('*').limit(1).execute()
            self.supabase.table('user_feedback').select('*').limit(1).execute()
            return True
        except Exception as e:
            print(f"Database initialization error: {e}")
            return False
    
    # API Usage Tracking
    def log_api_usage(self, api_name: str, success: bool = True, error_message: str = None):
        """Log API usage for rate limiting and monitoring"""
        if not self.supabase:
            return self._fallback_log_api_usage(api_name, success, error_message)
        
        try:
            self.supabase.table('api_usage').insert({
                'api_name': api_name,
                'timestamp': datetime.now().isoformat(),
                'success': success,
                'error_message': error_message,
                'date': datetime.now().date().isoformat()
            }).execute()
        except Exception as e:
            print(f"Database logging error: {e}")
            return self._fallback_log_api_usage(api_name, success, error_message)
    
    def get_api_usage(self, api_name: str = None, date: str = None) -> List[Dict]:
        """Get API usage statistics"""
        if not self.supabase:
            return self._fallback_get_api_usage(api_name, date)
        
        try:
            query = self.supabase.table('api_usage').select('*')
            
            if api_name:
                query = query.eq('api_name', api_name)
            
            if date:
                query = query.eq('date', date)
            else:
                # Default to today
                query = query.eq('date', datetime.now().date().isoformat())
            
            result = query.execute()
            return result.data
        except Exception as e:
            print(f"Database query error: {e}")
            return self._fallback_get_api_usage(api_name, date)
    
    def get_daily_api_counts(self) -> Dict[str, int]:
        """Get today's API usage counts by service"""
        usage_data = self.get_api_usage(date=datetime.now().date().isoformat())
        
        counts = {'gemini': 0, 'huggingface': 0, 'anthropic': 0}
        
        for record in usage_data:
            if record['success'] and record['api_name'] in counts:
                counts[record['api_name']] += 1
        
        return counts
    
    # User Request Tracking
    def log_user_request(self, client_id: str, request_type: str, topic: str = None, 
                        ip_address: str = None, success: bool = True):
        """Log user requests for rate limiting and analytics"""
        if not self.supabase:
            return self._fallback_log_user_request(client_id, request_type, topic, ip_address, success)
        
        try:
            self.supabase.table('user_requests').insert({
                'client_id': client_id,
                'request_type': request_type,
                'topic': topic,
                'ip_address': ip_address,
                'timestamp': datetime.now().isoformat(),
                'success': success,
                'date': datetime.now().date().isoformat()
            }).execute()
        except Exception as e:
            print(f"Database logging error: {e}")
    
    def get_ip_usage(self, client_id: str, hours: int = 24) -> List[Dict]:
        """Get request usage for specific IP/client"""
        if not self.supabase:
            return []
        
        try:
            since = datetime.now() - timedelta(hours=hours)
            
            result = self.supabase.table('user_requests').select('*').eq(
                'client_id', client_id
            ).gte('timestamp', since.isoformat()).execute()
            
            return result.data
        except Exception as e:
            print(f"Database query error: {e}")
            return []
    
    # Security Event Logging
    def log_security_event(self, event_type: str, client_id: str, details: str = None):
        """Log security events"""
        if not self.supabase:
            return
        
        try:
            self.supabase.table('security_events').insert({
                'event_type': event_type,
                'client_id': client_id,
                'details': details,
                'timestamp': datetime.now().isoformat()
            }).execute()
        except Exception as e:
            print(f"Security logging error: {e}")
    
    def log_admin_access(self, session_id: str, client_id: str):
        """Log admin access"""
        if not self.supabase:
            return
        
        try:
            self.supabase.table('admin_sessions').insert({
                'session_id': session_id,
                'client_id': client_id,
                'login_time': datetime.now().isoformat()
            }).execute()
        except Exception as e:
            print(f"Admin logging error: {e}")
    
    def get_recent_security_events(self, hours: int = 24) -> List[Dict]:
        """Get recent security events"""
        if not self.supabase:
            return []
        
        try:
            since = datetime.now() - timedelta(hours=hours)
            
            result = self.supabase.table('security_events').select('*').gte(
                'timestamp', since.isoformat()
            ).execute()
            
            return result.data
        except Exception as e:
            print(f"Database query error: {e}")
            return []
    
    # User Feedback
    def log_user_feedback(self, client_id: str, topic: str, rating: int, 
                         feedback_text: str = None, content_variation: int = None):
        """Log user feedback on generated content"""
        if not self.supabase:
            return
        
        try:
            self.supabase.table('user_feedback').insert({
                'client_id': client_id,
                'topic': topic,
                'rating': rating,
                'feedback_text': feedback_text,
                'content_variation': content_variation,
                'timestamp': datetime.now().isoformat()
            }).execute()
        except Exception as e:
            print(f"Feedback logging error: {e}")
    
    def get_feedback_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get feedback statistics"""
        if not self.supabase:
            return {'average_rating': 0, 'total_feedback': 0, 'rating_distribution': {}}
        
        try:
            since = datetime.now() - timedelta(days=days)
            
            result = self.supabase.table('user_feedback').select('rating').gte(
                'timestamp', since.isoformat()
            ).execute()
            
            ratings = [r['rating'] for r in result.data]
            
            if not ratings:
                return {'average_rating': 0, 'total_feedback': 0, 'rating_distribution': {}}
            
            rating_dist = {}
            for i in range(1, 6):
                rating_dist[str(i)] = ratings.count(i)
            
            return {
                'average_rating': sum(ratings) / len(ratings),
                'total_feedback': len(ratings),
                'rating_distribution': rating_dist
            }
        except Exception as e:
            print(f"Feedback stats error: {e}")
            return {'average_rating': 0, 'total_feedback': 0, 'rating_distribution': {}}
    
    # Analytics
    def get_usage_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive usage analytics"""
        try:
            since = datetime.now() - timedelta(days=days)
            
            # Get user requests
            requests = self.supabase.table('user_requests').select('*').gte(
                'timestamp', since.isoformat()
            ).execute().data
            
            # Get API usage
            api_usage = self.supabase.table('api_usage').select('*').gte(
                'timestamp', since.isoformat()
            ).execute().data
            
            # Calculate metrics
            total_requests = len(requests)
            unique_users = len(set(r['client_id'] for r in requests))
            successful_requests = len([r for r in requests if r['success']])
            
            popular_topics = {}
            for request in requests:
                if request['topic']:
                    topic = request['topic'].lower()
                    popular_topics[topic] = popular_topics.get(topic, 0) + 1
            
            api_success_rate = {}
            for api in ['gemini', 'huggingface', 'anthropic']:
                api_calls = [a for a in api_usage if a['api_name'] == api]
                if api_calls:
                    successful = len([a for a in api_calls if a['success']])
                    api_success_rate[api] = successful / len(api_calls) * 100
                else:
                    api_success_rate[api] = 0
            
            return {
                'total_requests': total_requests,
                'unique_users': unique_users,
                'success_rate': successful_requests / total_requests * 100 if total_requests > 0 else 0,
                'popular_topics': dict(sorted(popular_topics.items(), key=lambda x: x[1], reverse=True)[:5]),
                'api_success_rates': api_success_rate,
                'daily_breakdown': self._get_daily_breakdown(requests)
            }
        except Exception as e:
            print(f"Analytics error: {e}")
            return {}
    
    def _get_daily_breakdown(self, requests: List[Dict]) -> Dict[str, int]:
        """Get daily request breakdown"""
        daily = {}
        for request in requests:
            date = request['timestamp'][:10]  # Extract date part
            daily[date] = daily.get(date, 0) + 1
        return daily
    
    # Fallback methods for when Supabase is unavailable
    def _fallback_log_api_usage(self, api_name: str, success: bool, error_message: str):
        """Fallback to file-based logging"""
        try:
            with open('fallback_api_usage.json', 'a') as f:
                record = {
                    'api_name': api_name,
                    'timestamp': datetime.now().isoformat(),
                    'success': success,
                    'error_message': error_message
                }
                f.write(json.dumps(record) + '\n')
        except Exception as e:
            print(f"Fallback logging failed: {e}")
    
    def _fallback_get_api_usage(self, api_name: str, date: str) -> List[Dict]:
        """Fallback to file-based retrieval"""
        try:
            with open('fallback_api_usage.json', 'r') as f:
                records = []
                for line in f:
                    try:
                        record = json.loads(line.strip())
                        if api_name and record['api_name'] != api_name:
                            continue
                        if date and record['timestamp'][:10] != date:
                            continue
                        records.append(record)
                    except:
                        continue
                return records
        except FileNotFoundError:
            return []
    
    def _fallback_log_user_request(self, client_id: str, request_type: str, 
                                  topic: str, ip_address: str, success: bool):
        """Fallback user request logging"""
        try:
            with open('fallback_user_requests.json', 'a') as f:
                record = {
                    'client_id': client_id,
                    'request_type': request_type,
                    'topic': topic,
                    'ip_address': ip_address,
                    'timestamp': datetime.now().isoformat(),
                    'success': success
                }
                f.write(json.dumps(record) + '\n')
        except Exception as e:
            print(f"Fallback user logging failed: {e}")
    
    def health_check(self) -> Dict[str, bool]:
        """Check database connection health"""
        if not self.supabase:
            return {'connected': False, 'tables_accessible': False}
        
        try:
            # Simple query to test connection
            self.supabase.table('api_usage').select('id').limit(1).execute()
            return {'connected': True, 'tables_accessible': True}
        except Exception as e:
            return {'connected': False, 'tables_accessible': False, 'error': str(e)}
