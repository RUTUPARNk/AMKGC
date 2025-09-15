-- Add continuation nodes support to the nodes table

-- Add continuation_of column to nodes table
ALTER TABLE nodes 
ADD COLUMN IF NOT EXISTS continuation_of UUID REFERENCES nodes(id) ON DELETE SET NULL;

-- Add index for better performance on continuation_of column
CREATE INDEX IF NOT EXISTS idx_nodes_continuation_of ON nodes(continuation_of);

-- Update node_type enum to include 'continuation'
-- Note: PostgreSQL doesn't have a direct way to alter enum types in older versions
-- We'll ensure the application handles 'continuation' as a valid node_type

-- Add a column to track token count for nodes (optional but useful for performance)
ALTER TABLE nodes 
ADD COLUMN IF NOT EXISTS token_count INTEGER DEFAULT 0;

-- Add index for token_count queries
CREATE INDEX IF NOT EXISTS idx_nodes_token_count ON nodes(token_count);

-- Function to update token count (optional helper)
CREATE OR REPLACE FUNCTION update_node_token_count(node_id UUID, new_count INTEGER)
RETURNS VOID AS $$
BEGIN
    UPDATE nodes SET token_count = new_count WHERE id = node_id;
END;
$$ language 'plpgsql';

-- Function to get the root node of a continuation chain
CREATE OR REPLACE FUNCTION get_continuation_root(node_id UUID)
RETURNS UUID AS $$
DECLARE
    current_id UUID := node_id;
    parent_id UUID;
BEGIN
    -- Traverse up the continuation chain to find the root
    LOOP
        SELECT continuation_of INTO parent_id FROM nodes WHERE id = current_id;
        
        -- If there's no parent, we've found the root
        IF parent_id IS NULL THEN
            RETURN current_id;
        END IF;
        
        -- Move to the parent
        current_id := parent_id;
    END LOOP;
END;
$$ language 'plpgsql';

-- Function to get the full continuation chain for a node
CREATE OR REPLACE FUNCTION get_continuation_chain(root_node_id UUID)
RETURNS TABLE(
    id UUID,
    name TEXT,
    node_type TEXT,
    status TEXT,
    position INTEGER
) AS $$
DECLARE
    current_id UUID := root_node_id;
    pos INTEGER := 0;
    node_record RECORD;
BEGIN
    -- Return the root node first
    SELECT * INTO node_record FROM nodes WHERE id = current_id;
    id := node_record.id;
    name := node_record.name;
    node_type := node_record.node_type;
    status := node_record.status;
    position := pos;
    RETURN NEXT;
    
    -- Traverse down the continuation chain
    LOOP
        pos := pos + 1;
        SELECT n.* INTO node_record FROM nodes n WHERE n.continuation_of = current_id;
        
        -- If there's no continuation, we're done
        IF NOT FOUND THEN
            RETURN;
        END IF;
        
        -- Return this continuation node
        id := node_record.id;
        name := node_record.name;
        node_type := node_record.node_type;
        status := node_record.status;
        position := pos;
        RETURN NEXT;
        
        -- Move to the next node in the chain
        current_id := node_record.id;
    END LOOP;
END;
$$ language 'plpgsql';

-- View to easily query continuation chains
CREATE OR REPLACE VIEW node_continuation_chains AS
SELECT 
    root.id as root_node_id,
    root.name as root_node_name,
    chain.id as node_id,
    chain.name as node_name,
    chain.node_type,
    chain.status,
    chain.position
FROM nodes root
CROSS JOIN LATERAL get_continuation_chain(root.id) as chain
WHERE root.continuation_of IS NULL
ORDER BY root.id, chain.position;
