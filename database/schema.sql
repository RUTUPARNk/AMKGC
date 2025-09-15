-- Node-Based LLM System Database Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Nodes table
CREATE TABLE nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    context_window TEXT NOT NULL,  -- Stored as JSON or serialized string
    parent_node UUID REFERENCES nodes(id),
    child_nodes JSONB,             -- List of child node UUIDs
    llm_model_used TEXT DEFAULT 'ollama',  -- 'ollama' or 'openai'
    node_type TEXT DEFAULT 'general',       -- 'schema', 'policy', 'general', 'correction'
    status TEXT DEFAULT 'active',           -- 'active', 'resolved', 'conflicting', 'pending'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Node relationships table for better querying
CREATE TABLE node_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    child_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    relationship_type TEXT DEFAULT 'child', -- 'child', 'dependency', 'conflict'
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(parent_id, child_id)
);

-- Node chat history
CREATE TABLE node_chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    sender TEXT NOT NULL, -- 'user', 'llm', 'system'
    llm_model_used TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Node conflicts table
CREATE TABLE node_conflicts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_1_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    node_2_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    conflict_type TEXT NOT NULL, -- 'schema', 'policy', 'data'
    conflict_description TEXT,
    resolution_node_id UUID REFERENCES nodes(id),
    status TEXT DEFAULT 'pending', -- 'pending', 'resolved', 'ignored'
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);

-- Indexes for better performance
CREATE INDEX idx_nodes_parent_node ON nodes(parent_node);
CREATE INDEX idx_nodes_node_type ON nodes(node_type);
CREATE INDEX idx_nodes_status ON nodes(status);
CREATE INDEX idx_nodes_created_at ON nodes(created_at);
CREATE INDEX idx_node_relationships_parent ON node_relationships(parent_id);
CREATE INDEX idx_node_relationships_child ON node_relationships(child_id);
CREATE INDEX idx_node_chat_history_node_id ON node_chat_history(node_id);
CREATE INDEX idx_node_conflicts_nodes ON node_conflicts(node_1_id, node_2_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_nodes_updated_at 
    BEFORE UPDATE ON nodes 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column(); 