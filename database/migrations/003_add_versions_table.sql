-- Add versions table for node versioning/snapshots

-- Versions table
CREATE TABLE versions (
    commit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    content_snapshot JSONB NOT NULL,  -- Complete snapshot of node content
    diff_summary TEXT,                 -- LLM-generated summary of changes
    diff_patch JSONB,                  -- Structured diff representation (JSON Patch)
    author TEXT,                       -- User who made the change
    reason TEXT,                       -- Reason for the change (e.g., "merge", "manual edit")
    created_at TIMESTAMP DEFAULT NOW(),
    parent_commit_id UUID REFERENCES versions(commit_id)  -- For commit history
);

-- Indexes for performance
CREATE INDEX idx_versions_node_id ON versions(node_id);
CREATE INDEX idx_versions_created_at ON versions(created_at);
CREATE INDEX idx_versions_author ON versions(author);
CREATE INDEX idx_versions_reason ON versions(reason);
CREATE INDEX idx_versions_parent_commit ON versions(parent_commit_id);

-- Composite indexes
CREATE INDEX idx_versions_node_created ON versions(node_id, created_at);

-- Function to create a snapshot when a node is updated
CREATE OR REPLACE FUNCTION create_node_snapshot()
RETURNS TRIGGER AS $$
DECLARE
    snapshot JSONB;
BEGIN
    -- Create snapshot of the node's current state
    snapshot := jsonb_build_object(
        'id', NEW.id,
        'name', NEW.name,
        'context_window', NEW.context_window,
        'parent_node', NEW.parent_node,
        'child_nodes', NEW.child_nodes,
        'llm_model_used', NEW.llm_model_used,
        'node_type', NEW.node_type,
        'status', NEW.status,
        'created_at', NEW.created_at,
        'updated_at', NEW.updated_at
    );
    
    -- Insert snapshot into versions table
    INSERT INTO versions (node_id, content_snapshot, author, reason)
    VALUES (NEW.id, snapshot, 'system', 'auto_snapshot');
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically create snapshots (optional - can be enabled/disabled)
-- CREATE TRIGGER auto_create_node_snapshot 
--     AFTER UPDATE ON nodes 
--     FOR EACH ROW 
--     EXECUTE FUNCTION create_node_snapshot();

-- Add a column to nodes table to track the current commit ID
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS current_commit_id UUID REFERENCES versions(commit_id);
