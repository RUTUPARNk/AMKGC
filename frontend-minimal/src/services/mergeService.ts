import axios from 'axios';

// Merge Agent API service
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export interface MergePreview {
  merge_id: string;
  text_diff: string;
  json_patch: any[];
  diff_summary: string;
  impact: {
    added_lines: number;
    removed_lines: number;
    total_changes: number;
  };
  conflict: boolean;
  conflict_node_id: string | null;
  error?: string;
}

export interface ApplyMergeResult {
  merge_id: string;
  parent_id: string;
  child_id: string;
  applied_at: string;
  nodes_marked_stale: string[];
  execution_time_ms: number;
}

export class MergeService {
  private static instance: MergeService;
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
  
  public static getInstance(): MergeService {
    if (!MergeService.instance) {
      MergeService.instance = new MergeService();
    }
    return MergeService.instance;
  }
  
  // Get merge preview
  public async getMergePreview(childId: string): Promise<MergePreview> {
    try {
      const response = await this.axiosInstance.get(`/merge/${childId}`);
      
      // Check if there's an error in the response
      if (response.data.error) {
        throw new Error(response.data.error);
      }
      
      return response.data;
    } catch (error: any) {
      console.error('Error fetching merge preview:', error);
      if (error.response?.data?.error) {
        throw new Error(error.response.data.error);
      }
      throw new Error('Failed to fetch merge preview. Please try again.');
    }
  }
  
  // Apply merge
  public async applyMerge(childId: string, approvalNotes?: string): Promise<ApplyMergeResult> {
    try {
      const response = await this.axiosInstance.post(`/merge/${childId}/approve`, {
        approver: approvalNotes || 'User',
      });
      
      // Check if there's an error in the response
      if (!response.data.success) {
        throw new Error(response.data.error || 'Failed to apply merge');
      }
      
      return {
        merge_id: response.data.commit_id,
        parent_id: '', // Not provided in response
        child_id: childId,
        applied_at: new Date().toISOString(),
        nodes_marked_stale: [], // Not provided in response
        execution_time_ms: 0 // Not provided in response
      };
    } catch (error: any) {
      console.error('Error applying merge:', error);
      if (error.response?.data?.error) {
        throw new Error(error.response.data.error);
      }
      throw new Error('Failed to apply merge. Please try again.');
    }
  }
  
  // Mock implementations for demonstration
  public async mockGetMergePreview(): Promise<MergePreview> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 800));
    
    return {
      merge_id: `merge-${Date.now()}`,
      text_diff: `--- Parent Node Content\n+++ Child Node Content\n@@ -1,7 +1,7 @@\n # API Endpoint Documentation\n \n-This document describes the v1.0 API endpoints.\n+This document describes the v1.2 API endpoints with enhanced functionality.\n \n ## Authentication\n \n@@ -15,7 +15,7 @@\n \n ## Endpoints\n \n-- GET /users - Retrieve user information\n-- POST /users - Create a new user\n+- GET /users - Retrieve user information with pagination\n+- POST /users - Create a new user with validation\n+- PUT /users/{id} - Update user information\n \n ## Error Handling\n \n@@ -25,3 +25,6 @@\n 500 - Internal server error\n \n For detailed error responses, see the Error Handling section.\n+\n+## Rate Limiting\n+\n+All endpoints are rate limited to 1000 requests per hour per API key.`,
      json_patch: [{"op":"replace","path":"/","value":"Updated content"}],
      diff_summary: 'The child node introduces corrections to the parent node\'s content. Key changes include updated technical specifications for API endpoints, corrected example code snippets, added missing error handling scenarios, and improved clarity in documentation sections.',
      impact: {
        added_lines: 5,
        removed_lines: 2,
        total_changes: 7
      },
      conflict: false,
      conflict_node_id: null
    };
  }
  
  public async mockApplyMerge(childId: string): Promise<ApplyMergeResult> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    return {
      merge_id: `merge-${Date.now()}`,
      parent_id: `parent-${Date.now()}`,
      child_id: childId,
      applied_at: new Date().toISOString(),
      nodes_marked_stale: [`node-${Date.now()}-1`, `node-${Date.now()}-2`],
      execution_time_ms: 1450
    };
  }
}
