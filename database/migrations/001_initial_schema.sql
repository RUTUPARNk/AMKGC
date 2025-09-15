-- Initial database schema migration
-- This migration creates the base tables with optimized indexes for performance

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create nodes table with optimized indexes
CREATE TABLE nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    context_window TEXT NOT NULL,
    parent_node_id UUID REFERENCES nodes(id) ON DELETE SET NULL,
    child_nodes JSONB DEFAULT '[]',
    llm_model_used VARCHAR(50) DEFAULT 'ollama',
    node_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'resolved', 'conflicting')),
    conflict_with UUID REFERENCES nodes(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create optimized indexes for frequently queried fields
CREATE INDEX idx_nodes_name ON nodes(name);
CREATE INDEX idx_nodes_type ON nodes(node_type);
CREATE INDEX idx_nodes_status ON nodes(status);
CREATE INDEX idx_nodes_parent ON nodes(parent_node_id);
CREATE INDEX idx_nodes_created_at ON nodes(created_at);
CREATE INDEX idx_nodes_updated_at ON nodes(updated_at);
CREATE INDEX idx_nodes_conflict_with ON nodes(conflict_with);

-- Composite indexes for common query patterns
CREATE INDEX idx_nodes_type_status ON nodes(node_type, status);
CREATE INDEX idx_nodes_parent_status ON nodes(parent_node_id, status);
CREATE INDEX idx_nodes_created_type ON nodes(created_at, node_type);

-- GIN index for JSONB child_nodes field
CREATE INDEX idx_nodes_child_nodes_gin ON nodes USING GIN (child_nodes);

-- Create node_relationships table for explicit relationships
CREATE TABLE node_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    target_node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_node_id, target_node_id, relationship_type)
);

-- Indexes for node_relationships
CREATE INDEX idx_node_relationships_source ON node_relationships(source_node_id);
CREATE INDEX idx_node_relationships_target ON node_relationships(target_node_id);
CREATE INDEX idx_node_relationships_type ON node_relationships(relationship_type);
CREATE INDEX idx_node_relationships_source_type ON node_relationships(source_node_id, relationship_type);

-- Create node_chat_history table
CREATE TABLE node_chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    message TEXT NOT NULL,
    response TEXT,
    llm_model_used VARCHAR(50),
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for chat history
CREATE INDEX idx_chat_history_node_id ON node_chat_history(node_id);
CREATE INDEX idx_chat_history_user_id ON node_chat_history(user_id);
CREATE INDEX idx_chat_history_created_at ON node_chat_history(created_at);
CREATE INDEX idx_chat_history_node_created ON node_chat_history(node_id, created_at);

-- Create node_conflicts table
CREATE TABLE node_conflicts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node1_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    node2_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    priority INTEGER NOT NULL CHECK (priority BETWEEN 1 AND 10),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'resolved')),
    resolution_node_id UUID REFERENCES nodes(id) ON DELETE SET NULL,
    user_feedback TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    UNIQUE(node1_id, node2_id)
);

-- Indexes for conflicts
CREATE INDEX idx_conflicts_node1 ON node_conflicts(node1_id);
CREATE INDEX idx_conflicts_node2 ON node_conflicts(node2_id);
CREATE INDEX idx_conflicts_severity ON node_conflicts(severity);
CREATE INDEX idx_conflicts_priority ON node_conflicts(priority);
CREATE INDEX idx_conflicts_status ON node_conflicts(status);
CREATE INDEX idx_conflicts_created_at ON node_conflicts(created_at);
CREATE INDEX idx_conflicts_priority_status ON node_conflicts(priority, status);
CREATE INDEX idx_conflicts_severity_status ON node_conflicts(severity, status);

-- Create users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for users
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);

-- Create api_keys table
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_name VARCHAR(100) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

-- Indexes for API keys
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_active ON api_keys(is_active);
CREATE INDEX idx_api_keys_expires_at ON api_keys(expires_at);

-- Create token_blacklist table
CREATE TABLE token_blacklist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMP NOT NULL,
    blacklisted_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for token blacklist
CREATE INDEX idx_token_blacklist_hash ON token_blacklist(token_hash);
CREATE INDEX idx_token_blacklist_expires_at ON token_blacklist(expires_at);
CREATE INDEX idx_token_blacklist_user_id ON token_blacklist(user_id);

-- Create audit_log table for monitoring
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for audit log
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_resource ON audit_log(resource_type, resource_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX idx_audit_log_user_action ON audit_log(user_id, action);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_nodes_updated_at BEFORE UPDATE ON nodes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to clean up expired tokens
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM token_blacklist WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create function to get node statistics
CREATE OR REPLACE FUNCTION get_node_stats()
RETURNS TABLE(
    total_nodes BIGINT,
    nodes_by_type JSONB,
    nodes_by_status JSONB,
    conflicting_nodes BIGINT,
    resolved_nodes BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_nodes,
        jsonb_object_agg(node_type, count) as nodes_by_type,
        jsonb_object_agg(status, count) as nodes_by_status,
        COUNT(*) FILTER (WHERE status = 'conflicting')::BIGINT as conflicting_nodes,
        COUNT(*) FILTER (WHERE status = 'resolved')::BIGINT as resolved_nodes
    FROM (
        SELECT node_type, status, COUNT(*) as count
        FROM nodes
        GROUP BY node_type, status
    ) stats;
END;
$$ LANGUAGE plpgsql;

-- Create function to get conflict statistics
CREATE OR REPLACE FUNCTION get_conflict_stats()
RETURNS TABLE(
    total_conflicts BIGINT,
    conflicts_by_severity JSONB,
    conflicts_by_status JSONB,
    avg_priority NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_conflicts,
        jsonb_object_agg(severity, count) as conflicts_by_severity,
        jsonb_object_agg(status, count) as conflicts_by_status,
        AVG(priority)::NUMERIC as avg_priority
    FROM (
        SELECT severity, status, COUNT(*) as count
        FROM node_conflicts
        GROUP BY severity, status
    ) stats;
END;
$$ LANGUAGE plpgsql;

-- Create view for node graph data
CREATE VIEW node_graph_view AS
SELECT 
    n.id,
    n.name,
    n.node_type,
    n.status,
    n.parent_node_id,
    n.child_nodes,
    n.created_at,
    n.updated_at,
    COUNT(nr.id) as relationship_count
FROM nodes n
LEFT JOIN node_relationships nr ON n.id = nr.source_node_id
GROUP BY n.id, n.name, n.node_type, n.status, n.parent_node_id, n.child_nodes, n.created_at, n.updated_at;

-- Create materialized view for frequently accessed data
CREATE MATERIALIZED VIEW node_summary_mv AS
SELECT 
    node_type,
    status,
    COUNT(*) as count,
    AVG(LENGTH(context_window)) as avg_context_length,
    MAX(created_at) as latest_created
FROM nodes
GROUP BY node_type, status;

-- Create index on materialized view
CREATE INDEX idx_node_summary_mv_type_status ON node_summary_mv(node_type, status);

-- Create function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_node_summary()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW node_summary_mv;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO your_app_user; 