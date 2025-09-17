-- AgentComponents Database Schema for Supabase
-- Run these commands in your Supabase SQL Editor

-- API Usage Tracking Table
CREATE TABLE api_usage (
    id SERIAL PRIMARY KEY,
    api_name VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX idx_api_usage_date ON api_usage(date);
CREATE INDEX idx_api_usage_api_name ON api_usage(api_name);

-- User Requests Tracking Table
CREATE TABLE user_requests (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(100) NOT NULL,
    request_type VARCHAR(50) NOT NULL, -- 'live_research', 'cached_research', etc.
    topic VARCHAR(200),
    ip_address VARCHAR(45), -- Supports IPv6
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    success BOOLEAN DEFAULT TRUE,
    date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for rate limiting queries
CREATE INDEX idx_user_requests_client_id ON user_requests(client_id);
CREATE INDEX idx_user_requests_timestamp ON user_requests(timestamp);
CREATE INDEX idx_user_requests_date ON user_requests(date);

-- Security Events Table
CREATE TABLE security_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL, -- 'failed_admin_login', 'rate_limit_exceeded', etc.
    client_id VARCHAR(100) NOT NULL,
    details TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for security monitoring
CREATE INDEX idx_security_events_timestamp ON security_events(timestamp);
CREATE INDEX idx_security_events_type ON security_events(event_type);

-- Admin Sessions Table
CREATE TABLE admin_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    client_id VARCHAR(100) NOT NULL,
    login_time TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for session management
CREATE INDEX idx_admin_sessions_session_id ON admin_sessions(session_id);

-- User Feedback Table
CREATE TABLE user_feedback (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(100) NOT NULL,
    topic VARCHAR(200) NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    content_variation INTEGER,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for feedback analysis
CREATE INDEX idx_user_feedback_timestamp ON user_feedback(timestamp);
CREATE INDEX idx_user_feedback_rating ON user_feedback(rating);

-- Row Level Security (RLS) Policies
-- Enable RLS on all tables for security
ALTER TABLE api_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE security_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_feedback ENABLE ROW LEVEL SECURITY;

-- Create policies for service role access (your application)
-- These allow your backend to read/write all data

CREATE POLICY "Service role can manage api_usage" ON api_usage
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage user_requests" ON user_requests
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage security_events" ON security_events
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage admin_sessions" ON admin_sessions
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage user_feedback" ON user_feedback
    FOR ALL USING (auth.role() = 'service_role');

-- Create some useful views for analytics
CREATE VIEW daily_usage_summary AS
SELECT 
    date,
    COUNT(*) as total_requests,
    COUNT(DISTINCT client_id) as unique_users,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_requests,
    ROUND(
        (SUM(CASE WHEN success THEN 1 ELSE 0 END)::DECIMAL / COUNT(*)) * 100, 
        2
    ) as success_rate
FROM user_requests
GROUP BY date
ORDER BY date DESC;

CREATE VIEW api_usage_summary AS
SELECT 
    api_name,
    date,
    COUNT(*) as total_calls,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_calls,
    COUNT(*) - SUM(CASE WHEN success THEN 1 ELSE 0 END) as failed_calls
FROM api_usage
GROUP BY api_name, date
ORDER BY date DESC, api_name;

CREATE VIEW feedback_summary AS
SELECT 
    DATE(timestamp) as date,
    AVG(rating) as average_rating,
    COUNT(*) as total_feedback,
    COUNT(CASE WHEN rating >= 4 THEN 1 END) as positive_feedback,
    COUNT(CASE WHEN rating <= 2 THEN 1 END) as negative_feedback
FROM user_feedback
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Create a function to clean old data (optional)
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
    -- Delete user requests older than 90 days
    DELETE FROM user_requests WHERE timestamp < NOW() - INTERVAL '90 days';
    
    -- Delete API usage older than 90 days
    DELETE FROM api_usage WHERE timestamp < NOW() - INTERVAL '90 days';
    
    -- Delete security events older than 30 days (keep these shorter)
    DELETE FROM security_events WHERE timestamp < NOW() - INTERVAL '30 days';
    
    -- Delete inactive admin sessions older than 7 days
    DELETE FROM admin_sessions 
    WHERE last_activity < NOW() - INTERVAL '7 days' AND NOT is_active;
    
    -- Keep feedback indefinitely for analysis
END;
$$ LANGUAGE plpgsql;

-- Optional: Set up automatic cleanup (uncomment to enable)
-- SELECT cron.schedule('cleanup-old-data', '0 2 * * *', 'SELECT cleanup_old_data();');
