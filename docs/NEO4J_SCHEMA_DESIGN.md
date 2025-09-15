# Neo4j Schema Design for Node-LLM System

## Overview
This document outlines the Neo4j schema design for the Node-LLM System, including nodes, relationships, versioning, and merge tracking.

## Node Structure

### Node Labels
- `Node`: Primary entity representing a knowledge node
- `VersionSnapshot`: Historical snapshots of node content
- `MergeRequest`: Pending merge operations

### Node Properties

#### Node Properties
| Property | Type | Description |
|----------|------|-------------|
| id | String | Unique identifier (UUID) |
| name | String | Human-readable name |
| type | String | Node type (e.g., 'schema', 'policy', 'correction', 'continuation') |
| context_window | String | LLM context content |
| status | String | Current status ('active', 'stale', 'conflicting', 'resolved', 'merge_pending') |
| llm_model_used | String | LLM model that generated content |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |
| stale_at | DateTime | When marked stale (if applicable) |

#### VersionSnapshot Properties
| Property | Type | Description |
|----------|------|-------------|
| version_number | Integer | Sequential version number |
| context_window | String | Node context at time of snapshot |
| created_at | DateTime | Snapshot creation timestamp |

#### MergeRequest Properties
| Property | Type | Description |
|----------|------|-------------|
| id | String | Unique identifier |
| source_node_id | String | Source node ID |
| target_node_id | String | Target node ID |
| status | String | Status ('pending', 'approved', 'rejected', 'merged') |
| diff_content | String | JSON diff between nodes |
| created_at | DateTime | Request creation timestamp |
| updated_at | DateTime | Last update timestamp |

## Relationships

### Node Relationships
| Relationship | From | To | Description |
|-------------|------|----|-------------|
| PARENT_CHILD | Node | Node | Parent-child hierarchy |
| DEPENDS_ON | Node | Node | Dependency relationships |
| HAS_VERSION | Node | VersionSnapshot | Version history |
| MERGE_REQUEST | Node | Node | Merge request between nodes |
| MERGE_SNAPSHOT | MergeRequest | VersionSnapshot | Snapshot at time of merge |

### Relationship Properties

#### PARENT_CHILD
| Property | Type | Description |
|----------|------|-------------|
| created_at | DateTime | Relationship creation timestamp |

#### DEPENDS_ON
| Property | Type | Description |
|----------|------|-------------|
| created_at | DateTime | Relationship creation timestamp |
| weight | Float | Dependency strength (0.0-1.0) |

#### HAS_VERSION
| Property | Type | Description |
|----------|------|-------------|
| created_at | DateTime | Relationship creation timestamp |

#### MERGE_REQUEST
| Property | Type | Description |
|----------|------|-------------|
| created_at | DateTime | Request creation timestamp |
| updated_at | DateTime | Last update timestamp |
| type | String | Merge type ('semantic', 'textual') |

## Indexes

### Node Indexes
```cypher
CREATE INDEX node_id FOR (n:Node) ON (n.id)
CREATE INDEX node_name FOR (n:Node) ON (n.name)
CREATE INDEX node_status FOR (n:Node) ON (n.status)
CREATE INDEX node_created FOR (n:Node) ON (n.created_at)
CREATE INDEX node_updated FOR (n:Node) ON (n.updated_at)
CREATE INDEX node_type FOR (n:Node) ON (n.type)

CREATE INDEX version_node_id FOR (v:VersionSnapshot) ON (v.node_id)
CREATE INDEX version_number FOR (v:VersionSnapshot) ON (v.version_number)

CREATE INDEX merge_source FOR (m:MergeRequest) ON (m.source_node_id)
CREATE INDEX merge_target FOR (m:MergeRequest) ON (m.target_node_id)
CREATE INDEX merge_status FOR (m:MergeRequest) ON (m.status)
```

## Constraints

### Node Constraints
```cypher
CREATE CONSTRAINT node_id_unique FOR (n:Node) REQUIRE n.id IS UNIQUE
CREATE CONSTRAINT version_id_unique FOR (v:VersionSnapshot) REQUIRE v.id IS UNIQUE
CREATE CONSTRAINT merge_id_unique FOR (m:MergeRequest) REQUIRE m.id IS UNIQUE
```

## Example Queries

### Create a Node
```cypher
MERGE (n:Node {id: $node_id})
SET n.name = $name,
    n.type = $type,
    n.context_window = $context_window,
    n.status = 'active',
    n.llm_model_used = $model,
    n.created_at = datetime(),
    n.updated_at = datetime()
```

### Create Parent-Child Relationship
```cypher
MATCH (parent:Node {id: $parent_id}), (child:Node {id: $child_id})
MERGE (parent)-[:PARENT_CHILD {created_at: datetime()}]->(child)
```

### Create Version Snapshot
```cypher
MATCH (n:Node {id: $node_id})
CREATE (v:VersionSnapshot {
    id: randomUUID(),
    version_number: $version_number,
    context_window: $context_window,
    created_at: datetime()
})
CREATE (n)-[:HAS_VERSION {created_at: datetime()}]->(v)
```

### Get Node with Children
```cypher
MATCH (n:Node {id: $node_id})
OPTIONAL MATCH (n)-[:PARENT_CHILD]->(child:Node)
RETURN n, collect(child) AS children
```

### Get Stale Nodes
```cypher
MATCH (n:Node)
WHERE n.status = 'stale' 
AND n.stale_at < datetime() - duration({days: $days_threshold})
RETURN n
```

### Propagate Staleness
```cypher
MATCH (n:Node {id: $node_id})-[:DEPENDS_ON*]->(dependent:Node)
WHERE dependent.status <> 'stale'
SET dependent.status = 'stale',
    dependent.stale_at = datetime()
```

## Migration Strategy

1. Create constraints and indexes
2. Migrate existing PostgreSQL nodes to Neo4j
3. Establish relationships between nodes
4. Create initial version snapshots
5. Set up monitoring and maintenance procedures
