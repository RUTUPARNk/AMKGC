-- Add hallucinations table for tracking LLM response issues

-- Hallucinations table
CREATE TABLE hallucinations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('MissingFact', 'WrongAssumption', 'Speculation')),
    snippet TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT
);

-- Indexes for performance
CREATE INDEX idx_hallucinations_node_id ON hallucinations(node_id);
CREATE INDEX idx_hallucinations_type ON hallucinations(type);
CREATE INDEX idx_hallucinations_created_at ON hallucinations(created_at);
CREATE INDEX idx_hallucinations_resolved ON hallucinations(resolved);

-- Composite indexes
CREATE INDEX idx_hallucinations_node_type ON hallucinations(node_id, type);
CREATE INDEX idx_hallucinations_node_resolved ON hallucinations(node_id, resolved);

-- Add a column to nodes table to track hallucination count
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS hallucination_count INTEGER DEFAULT 0;

-- Function to update hallucination count
CREATE OR REPLACE FUNCTION update_hallucination_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE nodes SET hallucination_count = hallucination_count + 1 WHERE id = NEW.node_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE nodes SET hallucination_count = hallucination_count - 1 WHERE id = OLD.node_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

-- Trigger to automatically update hallucination count
CREATE TRIGGER update_node_hallucination_count 
    AFTER INSERT OR DELETE ON hallucinations 
    FOR EACH ROW 
    EXECUTE FUNCTION update_hallucination_count();
