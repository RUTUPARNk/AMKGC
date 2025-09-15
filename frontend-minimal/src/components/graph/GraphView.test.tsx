import React from 'react';
import { render } from '@testing-library/react';
import { GraphView } from './GraphView';

// Mock the reactflow dependency
jest.mock('reactflow', () => ({
  ReactFlow: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Background: () => <div></div>,
  Controls: () => <div></div>,
  ReactFlowProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Mock the zustand store
jest.mock('../../store/graph', () => ({
  useGraphStore: () => ({
    nodes: {},
    edges: {},
  }),
}));

describe('GraphView', () => {
  it('renders without crashing', () => {
    render(<GraphView sessionId="test-session" />);
  });
});
