# Node-LLM System Frontend Implementation Plan

## Overview
This document outlines the implementation plan for the Node-LLM System frontend based on the buildout document. The frontend will be a graph-based chat workspace with canvas UI, node panels, and integration with Router and Merge Agents.

## Current State Analysis
The frontend-minimal directory already contains:
- React + TypeScript + Vite setup
- Tailwind CSS configured
- React Flow for graph visualization
- Zustand for state management (basic implementation)
- Basic chat functionality
- Graph view with nodes and edges

## Implementation Roadmap

### Milestone 1 — Enhanced Graph + Node Basics

#### Tasks:
1. Replace React Flow with tldraw for enhanced canvas functionality
2. Implement node CRUD operations:
   - Create nodes via right-click context menu
   - Drag nodes
   - Connect nodes with edges
   - Delete nodes
3. Enhance sidebar with filters and search:
   - Status filters (Fresh, Stale, Merge Pending, Archived)
   - Fuzzy search by name/content
   - Status badges
4. Extend state management:
   - Graph slice: nodes, edges, statuses
   - Add node status tracking (fresh, stale, merge_pending)

#### Components to Create:
- `CanvasView.tsx` - Enhanced canvas with tldraw
- `Sidebar.tsx` - Enhanced sidebar with filters
- `NodeContextMenu.tsx` - Right-click context menu
- `StatusBar.tsx` - Status indicators

### Milestone 2 — Chat Integration

#### Tasks:
1. Implement Node Chat Panel:
   - Tabs per node (multiple open chats)
   - Chat history (user + assistant + system)
   - Composer box with send button
2. API integration with Router Agent:
   - `/api/v1/router/plan_execution` for preview execution plan
   - `/api/v1/router/execute_plan` for running queries
   - `/api/v1/router/node_dependencies/{node_id}` for showing edges
3. WebSocket integration:
   - `/api/v1/ws/router/{session_id}` for live updates
   - Event handling for plan creation, execution start, completion, errors

#### Components to Create:
- `NodeChatPanel.tsx` - Chat panel for individual nodes
- `ChatTab.tsx` - Individual chat tab
- `MessageBubble.tsx` - Enhanced message display
- `Composer.tsx` - Message input composer
- `WebSocketProvider.tsx` - WebSocket connection management

### Milestone 3 — Merge Flow

#### Tasks:
1. Implement child node creation UI:
   - Mark hallucination → system creates child node
   - Child chat session runs
2. Create Diff Viewer:
   - Side-by-side view (semantic summary + textual diff)
   - Visual highlighting (insertions = green, deletions = red)
3. Implement merge approval workflow:
   - Approve/Reject buttons
   - API integration with Merge Agent
   - `/api/v1/merge/{child_id}` for preview merge diff
   - `/api/v1/merge/{child_id}/approve` for approving merges

#### Components to Create:
- `DiffViewer.tsx` - Side-by-side diff visualization
- `MergePreviewModal.tsx` - Modal for merge previews
- `MergeApprovalPanel.tsx` - Approval/rejection interface

### Milestone 4 — Polish & Advanced Features

#### Tasks:
1. Add notifications and status indicators:
   - Toast notifications for Router/Merge events
   - Inline warnings for hallucinations/stale dependencies
   - Loading spinners + "live updating" badges
2. Implement animations and UI polish:
   - Framer Motion for smooth transitions
   - shadcn/ui for buttons, modals, toasts
3. Add error handling and retry UX
4. Implement advanced features:
   - Multi-user collaboration (presence, live cursors)
   - Advanced diff resolution UI
   - Knowledge-gap dashboard
   - Snapshot mode toggle

#### Components to Create:
- `NotificationProvider.tsx` - Toast notification system
- `StatusIndicator.tsx` - Status badges and indicators
- `LoadingSpinner.tsx` - Loading indicators
- `CollaborationCursor.tsx` - Live cursor indicators

## Technical Architecture

### State Management
Extend Zustand implementation with slices:
- `graphSlice` - Nodes, edges, statuses
- `chatSlice` - Per-node messages, LLM responses
- `routerSlice` - Execution plans, token usage
- `mergeSlice` - Preview diffs, approvals

### Component Structure
```
App.tsx
├── Navbar.tsx
├── MainLayout.tsx
│   ├── Sidebar.tsx
│   ├── CanvasView.tsx
│   │   ├── NodeContextMenu.tsx
│   │   └── StatusBar.tsx
│   └── NodeChatPanel.tsx
│       ├── ChatTab.tsx
│       ├── MessageBubble.tsx
│       └── Composer.tsx
├── DiffViewer.tsx
├── MergePreviewModal.tsx
└── NotificationProvider.tsx
```

### API Integration
Create service modules for backend communication:
- `routerService.ts` - Router Agent API calls
- `mergeService.ts` - Merge Agent API calls
- `nodeService.ts` - Node CRUD operations
- `websocketService.ts` - WebSocket connection management

## File Structure Plan
```
src/
├── components/
│   ├── canvas/
│   │   ├── CanvasView.tsx
│   │   ├── NodeContextMenu.tsx
│   │   └── StatusBar.tsx
│   ├── chat/
│   │   ├── NodeChatPanel.tsx
│   │   ├── ChatTab.tsx
│   │   ├── MessageBubble.tsx
│   │   └── Composer.tsx
│   ├── diff/
│   │   ├── DiffViewer.tsx
│   │   └── MergePreviewModal.tsx
│   ├── sidebar/
│   │   └── Sidebar.tsx
│   ├── notifications/
│   │   ├── NotificationProvider.tsx
│   │   └── Toast.tsx
│   └── ui/
│       ├── Button.tsx
│       ├── Modal.tsx
│       └── Badge.tsx
├── services/
│   ├── routerService.ts
│   ├── mergeService.ts
│   ├── nodeService.ts
│   └── websocketService.ts
├── store/
│   ├── index.ts
│   ├── graphSlice.ts
│   ├── chatSlice.ts
│   ├── routerSlice.ts
│   └── mergeSlice.ts
├── hooks/
│   ├── useGraph.ts
│   ├── useChat.ts
│   ├── useRouter.ts
│   └── useMerge.ts
└── pages/
    └── Dashboard.tsx
```

## Implementation Priority
1. **Core Functionality** (Milestones 1-2)
   - Enhanced canvas with tldraw
   - Node CRUD operations
   - Chat panel integration
   - Router API integration

2. **Merge Functionality** (Milestone 3)
   - Diff viewer
   - Merge approval workflow
   - Merge API integration

3. **Polish & Advanced Features** (Milestone 4)
   - Notifications
   - Animations
   - Advanced features

## Dependencies to Install
```bash
npm install tldraw @monaco-editor/react framer-motion
```

## Testing Strategy
1. Unit tests for components using Jest and React Testing Library
2. Integration tests for API services
3. End-to-end tests for key user flows
4. Visual regression tests for UI components

## Success Metrics
1. Canvas with node CRUD operations working
2. Chat panel with live updates via WebSocket
3. Diff viewer with semantic and textual diffs
4. Merge approval workflow functional
5. Responsive UI with proper error handling
6. Performance metrics (load time, rendering speed)

This implementation plan provides a structured approach to building the Node-LLM System frontend while leveraging the existing codebase and incrementally adding the required functionality.
