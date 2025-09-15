import axios from 'axios';

// Router Agent API service
// Base URL would be configured in environment variables

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export interface RouterPlan {
  plan_id: string;
  query: string;
  nodes: Array<{
    id: string;
    relevance_score: number;
    content: string;
  }>;
  execution_plan: Array<{
    step_id: string;
    node_id: string;
    operation: string;
    estimated_tokens: number;
  }>;
  total_estimated_tokens: number;
}

export interface RouterExecutionResult {
  plan_id: string;
  results: Array<{
    step_id: string;
    node_id: string;
    output: string;
    actual_tokens: number;
    status: 'success' | 'error';
  }>;
  final_output: string;
  total_tokens: number;
  execution_time_ms: number;
}

export interface NodeDependencies {
  node_id: string;
  dependencies: string[];
  dependents: string[];
}

export class RouterService {
  private static instance: RouterService;
  private axiosInstance;
  
  private constructor() {
    this.axiosInstance = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Add auth token to requests if available
    this.axiosInstance.interceptors.request.use((config) => {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }
  
  public static getInstance(): RouterService {
    if (!RouterService.instance) {
      RouterService.instance = new RouterService();
    }
    return RouterService.instance;
  }
  
  // Plan execution based on a query
  public async planExecution(query: string, sessionId: string): Promise<RouterPlan> {
    try {
      // In a real implementation, this would call:
      // POST /api/v1/router/plan_execution
      const response = await this.axiosInstance.post('/router/plan_execution', {
        query,
        session_id: sessionId,
      });
      
      return response.data;
    } catch (error) {
      console.error('Error planning execution:', error);
      throw new Error('Failed to plan execution. Please try again.');
    }
  }
  
  // Execute a planned execution
  public async executePlan(planId: string): Promise<RouterExecutionResult> {
    try {
      // In a real implementation, this would call:
      // POST /api/v1/router/execute_plan
      const response = await this.axiosInstance.post('/router/execute_plan', {
        plan_id: planId,
      });
      
      return response.data;
    } catch (error) {
      console.error('Error executing plan:', error);
      throw new Error('Failed to execute plan. Please try again.');
    }
  }
  
  // Get node dependencies
  public async getNodeDependencies(nodeId: string): Promise<NodeDependencies> {
    try {
      // In a real implementation, this would call:
      // GET /api/v1/router/node_dependencies/{node_id}
      const response = await this.axiosInstance.get(`/router/node_dependencies/${nodeId}`);
      
      return response.data;
    } catch (error) {
      console.error('Error fetching node dependencies:', error);
      throw new Error('Failed to fetch node dependencies. Please try again.');
    }
  }
  
  // Mock implementations for demonstration
  public async mockPlanExecution(query: string): Promise<RouterPlan> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    return {
      plan_id: `plan-${Date.now()}`,
      query,
      nodes: [
        {
          id: 'node-1',
          relevance_score: 0.95,
          content: 'This is relevant information about the query topic.'
        },
        {
          id: 'node-2',
          relevance_score: 0.87,
          content: 'Additional context that might be helpful.'
        }
      ],
      execution_plan: [
        {
          step_id: 'step-1',
          node_id: 'node-1',
          operation: 'retrieve_content',
          estimated_tokens: 150
        },
        {
          step_id: 'step-2',
          node_id: 'node-2',
          operation: 'retrieve_content',
          estimated_tokens: 120
        }
      ],
      total_estimated_tokens: 270
    };
  }
  
  public async mockExecutePlan(planId: string): Promise<RouterExecutionResult> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    return {
      plan_id: planId,
      results: [
        {
          step_id: 'step-1',
          node_id: 'node-1',
          output: 'Based on the retrieved information, here is a comprehensive answer to your query.',
          actual_tokens: 155,
          status: 'success'
        },
        {
          step_id: 'step-2',
          node_id: 'node-2',
          output: 'Additional context that supports the main answer.',
          actual_tokens: 125,
          status: 'success'
        }
      ],
      final_output: 'This is the final synthesized answer based on all retrieved information.',
      total_tokens: 280,
      execution_time_ms: 2150
    };
  }
}
