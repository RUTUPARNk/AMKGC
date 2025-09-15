-- Add pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create fragments table for storing text embeddings
CREATE TABLE fragments (
    fragment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    embedding VECTOR(1536),  -- Adjust dimension based on your embedding model
    commit_id UUID,
    offset INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_fragments_node_id ON fragments(node_id);
CREATE INDEX idx_fragments_commit_id ON fragments(commit_id);
CREATE INDEX idx_fragments_created_at ON fragments(created_at);

-- Vector similarity search index (adjust based on your distance metric)
-- For cosine similarity
CREATE INDEX idx_fragments_embedding_cosine ON fragments 
    USING hnsw (embedding vector_cosine_ops);

-- For L2 distance
-- CREATE INDEX idx_fragments_embedding_l2 ON fragments 
--     USING hnsw (embedding vector_l2_ops);

-- For inner product
-- CREATE INDEX idx_fragments_embedding_ip ON fragments 
--     USING hnsw (embedding vector_ip_ops);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_fragments_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_fragments_updated_at 
    BEFORE UPDATE ON fragments 
    FOR EACH ROW 
    EXECUTE FUNCTION update_fragments_updated_at();

-- Add vector_index_id to nodes table for referencing fragments
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS vector_index_id UUID;
