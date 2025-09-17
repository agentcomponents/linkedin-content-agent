import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os

class MonitoringManager:
    """Handles monitoring dashboard and alerting"""
    
    def __init__(self, database_manager, security_manager):
        self.db = database_manager
        self.security = security_manager
        self.alert_thresholds = {
            'api_usage_warning': 0.8,  # 80% of daily limit
            'failed_requests_threshold': 10,
            'failed_logins_threshold': 5,
            'low_feedback_rating': 3.0
        }
    
    def show_admin_dashboard(self):
        """Complete admin dashboard"""
        st.header("🔧 AgentComponents Admin Dashboard")
        
        # Quick stats
        self._show_quick_stats()
        
        # Tabs for different monitoring areas
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Analytics", "🔒 Security", "⚡ API Usage", "💬 Feedback", "⚙️ System Health"
        ])
        
        with tab1:
            self._show_analytics_dashboard()
        
        with tab2:
            self._show_security_dashboard()
        
        with tab3:
            self._show_api_dashboard()
        
        with tab4:
            self._show_feedback_dashboard()
        
        with tab5:
            self._show_system_health()
    
    def _show_quick_stats(self):
        """Quick overview stats"""
        col1, col2, col3, col4 = st.columns(4)
        
        # Get today's data
        api_counts = self.db.get_daily_api_counts()
        analytics = self.db.get_usage_analytics(days=1)
        
        with col1:
            st.metric(
                "Requests Today", 
                analytics.get('total_requests', 0),
                delta=f"+{analytics.get('total_requests', 0) - analytics.get('yesterday_requests', 0)}"
            )
        
        with col2:
            st.metric(
                "Unique Users", 
                analytics.get('unique_users', 0)
            )
        
        with col3:
            success_rate = analytics.get('success_rate', 0)
            st.metric(
                "Success Rate", 
                f"{success_rate:.1f}%",
                delta=f"{success_rate - 90:.1f}%" if success_rate < 90 else "Normal"
            )
        
        with col4:
            total_api_calls = sum(api_counts.values())
            st.metric(
                "API Calls Used", 
                total_api_calls,
                delta="Within limits" if total_api_calls < 100 else "High usage"
            )
    
    def _show_analytics_dashboard(self):
        """Detailed analytics dashboard"""
        st.subheader("Usage Analytics")
        
        # Time range selector
        days = st.selectbox("Time Range", [1, 7, 30], index=1, format_func=lambda x: f"Last {x} day{'s' if x > 1 else ''}")
        
        analytics = self.db.get_usage_analytics(days=days)
        
        if not analytics:
            st.warning("No analytics data available")
            return
        
        # Usage over time
        if analytics.get('daily_breakdown'):
            daily_df = pd.DataFrame(list(analytics['daily_breakdown'].items()), 
                                  columns=['Date', 'Requests'])
            daily_df['Date'] = pd.to_datetime(daily_df['Date'])
            
            fig = px.line(daily_df, x='Date', y='Requests', title='Daily Request Volume')
            st.plotly_chart(fig, use_container_width=True)
        
        # Popular topics
        if analytics.get('popular_topics'):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Popular Topics")
                topics_df = pd.DataFrame(list(analytics['popular_topics'].items()), 
                                       columns=['Topic', 'Count'])
                st.dataframe(topics_df, use_container_width=True)
            
            with col2:
                fig = px.pie(topics_df, values='Count', names='Topic', title='Topic Distribution')
                st.plotly_chart(fig, use_container_width=True)
        
        # API success rates
        if analytics.get('api_success_rates'):
            st.subheader("API Performance")
            api_df = pd.DataFrame(list(analytics['api_success_rates'].items()), 
                                columns=['API', 'Success Rate'])
            
            fig = px.bar(api_df, x='API', y='Success Rate', title='API Success Rates')
            fig.update_yaxis(range=[0, 100])
            st.plotly_chart(fig, use_container_width=True)
    
    def _show_security_dashboard(self):
        """Security monitoring dashboard"""
        st.subheader("Security Overview")
        
        health = self.security.check_system_health()
        
        # Security status
        status_color = {"healthy": "🟢", "warning": "🟡", "critical": "🔴"}
        st.markdown(f"**System Status:** {status_color.get(health['status'], '⚪')} {health['status'].title()}")
        
        if health.get('alerts'):
            st.warning("Security Alerts:")
            for alert in health['alerts']:
                st.write(f"- {alert}")
        
        # Security metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Failed Logins (24h)", health.get('failed_logins_24h', 0))
            if health.get('failed_logins_24h', 0) > self.alert_thresholds['failed_logins_threshold']:
                st.error("High number of failed login attempts!")
        
        with col2:
            st.metric("Rate Limit Hits (24h)", health.get('rate_limit_hits_24h', 0))
        
        # Recent security events
        st.subheader("Recent Security Events")
        events = self.db.get_recent_security_events(hours=24)
        
        if events:
            events_df = pd.DataFrame(events)
            st.dataframe(events_df[['timestamp', 'event_type', 'client_id', 'details']], 
                        use_container_width=True)
        else:
            st.info("No recent security events")
        
        # Manual actions
        st.subheader("Security Actions")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Reset Rate Limits"):
                st.success("Rate limits reset (feature not implemented in demo)")
        
        with col2:
            if st.button("📧 Send Security Report"):
                self.send_security_alert("Manual security report requested")
                st.success("Security report sent!")
    
    def _show_api_dashboard(self):
        """API usage monitoring"""
        st.subheader("API Usage Monitoring")
        
        # Current usage
        api_counts = self.db.get_daily_api_counts()
        
        limits = {'gemini': 100, 'huggingface': 30, 'anthropic': 10}
        
        for api, count in api_counts.items():
            limit = limits.get(api, 100)
            usage_percent = count / limit
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.progress(usage_percent, text=f"{api.title()}: {count}/{limit}")
            
            with col2:
                if usage_percent > self.alert_thresholds['api_usage_warning']:
                    st.warning("⚠️ High usage")
                else:
                    st.success("✅ Normal")
        
        # API usage over time
        st.subheader("API Usage History")
        
        days = st.slider("Days to show", 1, 30, 7)
        
        # Get historical API usage
        api_history = {}
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).date().isoformat()
            daily_usage = self.db.get_api_usage(date=date)
            
            for api in ['gemini', 'huggingface', 'anthropic']:
                api_count = len([u for u in daily_usage if u['api_name'] == api and u['success']])
                if api not in api_history:
                    api_history[api] = []
                api_history[api].append({'date': date, 'count': api_count})
        
        # Create chart
        if api_history:
            chart_data = []
            for api, data in api_history.items():
                for day_data in data:
                    chart_data.append({
                        'Date': day_data['date'],
                        'API': api.title(),
                        'Usage': day_data['count']
                    })
            
            if chart_data:
                df = pd.DataFrame(chart_data)
                df['Date'] = pd.to_datetime(df['Date'])
                
                fig = px.line(df, x='Date', y='Usage', color='API', title='API Usage Over Time')
                st.plotly_chart(fig, use_container_width=True)
        
        # API error tracking
        st.subheader("API Errors")
        error_data = self.db.get_api_usage()
        errors = [e for e in error_data if not e['success']]
        
        if errors:
            error_df = pd.DataFrame(errors)
            st.dataframe(error_df[['timestamp', 'api_name', 'error_message']], 
                        use_container_width=True)
        else:
            st.success("No recent API errors")
    
    def _show_feedback_dashboard(self):
        """User feedback monitoring"""
        st.subheader("User Feedback Analysis")
        
        feedback_stats = self.db.get_feedback_stats(days=7)
        
        if feedback_stats['total_feedback'] == 0:
            st.info("No user feedback received yet")
            return
        
        # Feedback metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_rating = feedback_stats['average_rating']
            st.metric("Average Rating", f"{avg_rating:.1f}/5")
            if avg_rating < self.alert_thresholds['low_feedback_rating']:
                st.error("Low average rating!")
        
        with col2:
            st.metric("Total Feedback", feedback_stats['total_feedback'])
        
        with col3:
            positive_feedback = sum(int(k) * v for k, v in feedback_stats['rating_distribution'].items() if int(k) >= 4)
            total_weighted = sum(int(k) * v for k, v in feedback_stats['rating_distribution'].items())
            positive_percent = (positive_feedback / total_weighted * 100) if total_weighted > 0 else 0
            st.metric("Positive Feedback", f"{positive_percent:.1f}%")
        
        # Rating distribution
        if feedback_stats['rating_distribution']:
            rating_df = pd.DataFrame(list(feedback_stats['rating_distribution'].items()), 
                                   columns=['Rating', 'Count'])
            rating_df['Rating'] = rating_df['Rating'].astype(int)
            
            fig = px.bar(rating_df, x='Rating', y='Count', title='Rating Distribution')
            st.plotly_chart(fig, use_container_width=True)
    
    def _show_system_health(self):
        """System health monitoring"""
        st.subheader("System Health Check")
        
        # Database health
        db_health = self.db.health_check()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Database Status**")
            if db_health['connected']:
                st.success("✅ Connected")
            else:
                st.error("❌ Disconnected")
                if 'error' in db_health:
                    st.error(f"Error: {db_health['error']}")
        
        with col2:
            st.write("**Tables Status**")
            if db_health['tables_accessible']:
                st.success("✅ All tables accessible")
            else:
                st.error("❌ Table access issues")
        
        # System resources (simplified for Streamlit)
        st.subheader("Application Status")
        
        # Check recent errors
        recent_errors = self.db.get_api_usage()
        error_count = len([e for e in recent_errors if not e['success']])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Recent API Errors", error_count)
        
        with col2:
            uptime_status = "🟢 Running" if db_health['connected'] else "🔴 Issues"
            st.metric("System Status", uptime_status)
        
        # Configuration check
        st.subheader("Configuration Status")
        
        config_checks = [
            ("Supabase URL", bool(os.getenv('SUPABASE_URL'))),
            ("Supabase Key", bool(os.getenv('SUPABASE_ANON_KEY'))),
            ("HuggingFace Token", bool(os.getenv('HUGGINGFACE_TOKEN'))),
            ("Gemini API Key", bool(os.getenv('GEMINI_API_KEY'))),
            ("Admin Password", bool(os.getenv('ADMIN_PASSWORD'))),
            ("Email Configuration", bool(os.getenv('SMTP_EMAIL') and os.getenv('SMTP_PASSWORD')))
        ]
        
        for check_name, status in config_checks:
            if status:
                st.success(f"✅ {check_name}")
            else:
                st.warning(f"⚠️ {check_name} not configured")
    
    def send_alert_email(self, subject: str, message: str, alert_type: str = "warning"):
        """Send alert email to admin"""
        try:
            smtp_email = os.getenv('SMTP_EMAIL')
            smtp_password = os.getenv('SMTP_PASSWORD')
            admin_email = os.getenv('ADMIN_EMAIL')
            
            if not all([smtp_email, smtp_password, admin_email]):
                print("Email configuration incomplete")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = smtp_email
            msg['To'] = admin_email
            msg['Subject'] = f"[AgentComponents Alert] {subject}"
            
            body = f"""
            AgentComponents Alert
            
            Type: {alert_type.upper()}
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Message:
            {message}
            
            ---
            AgentComponents Monitoring System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(smtp_email, smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Email alert failed: {e}")
            return False
    
    def send_daily_report(self):
        """Send daily summary report"""
        analytics = self.db.get_usage_analytics(days=1)
        api_counts = self.db.get_daily_api_counts()
        feedback_stats = self.db.get_feedback_stats(days=1)
        
        report = f"""
        AgentComponents Daily Report - {datetime.now().strftime('%Y-%m-%d')}
        
        USAGE STATISTICS:
        - Total Requests: {analytics.get('total_requests', 0)}
        - Unique Users: {analytics.get('unique_users', 0)}
        - Success Rate: {analytics.get('success_rate', 0):.1f}%
        
        API USAGE:
        - Gemini: {api_counts.get('gemini', 0)}/100
        - HuggingFace: {api_counts.get('huggingface', 0)}/30
        - Anthropic: {api_counts.get('anthropic', 0)}/10
        
        USER FEEDBACK:
        - Average Rating: {feedback_stats.get('average_rating', 0):.1f}/5
        - Total Feedback: {feedback_stats.get('total_feedback', 0)}
        
        POPULAR TOPICS:
        {chr(10).join([f"- {topic}: {count}" for topic, count in analytics.get('popular_topics', {}).items()])}
        
        SYSTEM STATUS: Operational
        """
        
        return self.send_alert_email("Daily Report", report, "info")
    
    def send_security_alert(self, message: str):
        """Send security-specific alert"""
        return self.send_alert_email("Security Alert", message, "security")
    
    def check_alert_conditions(self):
        """Check if any alert conditions are met"""
        alerts = []
        
        # Check API usage
        api_counts = self.db.get_daily_api_counts()
        limits = {'gemini': 100, 'huggingface': 30, 'anthropic': 10}
        
        for api, count in api_counts.items():
            limit = limits.get(api, 100)
            if count >= limit * self.alert_thresholds['api_usage_warning']:
                alerts.append(f"{api} API usage at {count}/{limit} ({count/limit*100:.1f}%)")
        
        # Check security events
        security_health = self.security.check_system_health()
        if security_health['status'] == 'warning':
            alerts.append(f"Security status: {security_health['status']}")
        
        # Check feedback quality
        feedback_stats = self.db.get_feedback_stats(days=1)
        if (feedback_stats['total_feedback'] > 5 and 
            feedback_stats['average_rating'] < self.alert_thresholds['low_feedback_rating']):
            alerts.append(f"Low user satisfaction: {feedback_stats['average_rating']:.1f}/5")
        
        # Send alerts if any conditions met
        if alerts:
            alert_message = "The following alert conditions were detected:\n\n" + "\n".join(f"- {alert}" for alert in alerts)
            self.send_alert_email("System Alerts", alert_message, "warning")
        
        return alerts
