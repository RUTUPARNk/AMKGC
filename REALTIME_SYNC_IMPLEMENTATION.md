# Real-Time Session Graph Synchronization Implementation

## Overview
This document describes the implementation of real-time WebSocket synchronization between the backend and frontend to enable live updates of session graph data.

## Backend Implementation

### WebSocket Endpoint
- **Endpoint**: `/api/v1/ws/sessions`
- **Protocol**: WebSocket
- **Purpose**: Broadcast session events (created, updated, deleted) to all connected clients

### Event Broadcasting
The backend broadcasts session events through the following mechanisms:

1. **Session Created**: When a new node is created via `create_node()` method
2. **Session Updated**: When a node's context is updated via `update_node_context()` method
3. **Session Deleted**: When a node is deleted via `delete_node()` method

### Implementation Details
- **File**: `backend/api/websocket.py` - WebSocket router and connection management
- **File**: `backend/api/events.py` - Session event broadcasting functions
- **File**: `backend/services/node_service.py` - Integration of event broadcasting in node operations

## Frontend Implementation

### WebSocket Hook
- **File**: `frontend-minimal/src/hooks/useSessionWS.ts`
- **Function**: `useSessionWS()` - Custom hook to manage WebSocket connection
- **Endpoint**: `ws://localhost:8000/api/v1/ws/sessions`

### State Management
- **Library**: Zustand
- **File**: `frontend-minimal/src/store.ts`
- **Store**: `useStore` - Manages session data state

### Graph View Integration
- **File**: `frontend-minimal/src/components/GraphView.tsx`
- **Integration**: Uses `useSessionWS()` hook and `useStore()` for real-time updates

## Data Flow

1. **Session Creation**:
   - User creates a new session/node
   - Backend `create_node()` method is called
   - Node is persisted to database
   - `session_created()` event is broadcasted via WebSocket
   - Frontend receives event and updates Zustand store
   - GraphView re-renders with new session node

2. **Session Update**:
   - User updates a session/node
   - Backend `update_node_context()` method is called
   - Node is updated in database
   - `session_updated()` event is broadcasted via WebSocket
   - Frontend receives event and updates Zustand store
   - GraphView re-renders with updated session node

3. **Session Deletion**:
   - User deletes a session/node
   - Backend `delete_node()` method is called
   - Node is removed from database
   - `session_deleted()` event is broadcasted via WebSocket
   - Frontend receives event and updates Zustand store
   - GraphView re-renders with session node removed

## Dependencies

### Backend
- `fastapi` - WebSocket support
- `websockets` - WebSocket protocol implementation

### Frontend
- `zustand` - State management
- `reactflow` - Graph visualization

## Testing
To test the real-time synchronization:

1. Start the backend server
2. Start the frontend application
3. Open the Graph View in the dashboard
4. Create, update, or delete sessions/nodes
5. Observe real-time updates in the graph visualization

## Future Improvements

1. **Authentication**: Add JWT token validation for WebSocket connections
2. **Error Handling**: Implement comprehensive error handling and reconnection logic
3. **Performance**: Optimize event broadcasting for large numbers of connected clients
4. **Security**: Add rate limiting and message validation for WebSocket messages
