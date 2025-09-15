"""
Comprehensive test suite for Router Agent
"""

import sys
import os
import asyncio
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

class TestRouterAgent(unittest.TestCase):
    """Comprehensive test suite for Router Agent"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock Redis client
        self.mock_redis = Mock()
        
        # Mock Neo4j service
        self.mock_neo4j_service = Mock()
        self.mock_neo4j_session = Mock()
        self.mock_neo4j_service.driver.session.return_value.__enter__.return_value = self.mock_neo4j_session
        
        # Mock PipelineExecutor
        self.mock_pipeline_executor = Mock()
        
    @patch('distributed.router.redis.Redis')
    @patch('distributed.router.Neo4jService')
    @patch('distributed.router.PipelineExecutor')
    def test_router_agent_initialization(self, mock_pipeline_executor, mock_neo4j_service, mock_redis):
        """Test Router Agent initialization"""
        # Setup mocks
        mock_redis.return_value = self.mock_redis
        mock_neo4j_service.return_value = self.mock_neo4j_service
        mock_pipeline_executor.return_value = self.mock_pipeline_executor
        
        # Import and instantiate RouterAgent
        from distributed.router import RouterAgent
        router_agent = RouterAgent()
        
        # Assertions
        self.assertIsNotNone(router_agent)
        self.assertEqual(router_agent.redis_client, self.mock_redis)
        self.assertEqual(router_agent.neo4j_service, self.mock_neo4j_service)
        self.assertEqual(router_agent.pipeline_executor, self.mock_pipeline_executor)
        
    @patch('distributed.router.redis.Redis')
    @patch('distributed.router.Neo4jService')
    def test_retrieve_top_k_nodes_success(self, mock_neo4j_service, mock_redis):
        """Test successful retrieval of top-k nodes"""
        # Setup mocks
        mock_redis.return_value = self.mock_redis
        mock_neo4j_service.return_value = self.mock_neo4j_service
        
        # Mock Neo4j response
        mock_record = Mock()
        mock_record.__getitem__.side_effect = lambda key: {
            'n': {'id': 'node1', 'name': 'test node', 'context_window': 'test context'},
            'relationships': []
        }[key]
        
        self.mock_neo4j_session.run.return_value = [mock_record]
        
        # Import and instantiate RouterAgent
        from distributed.router import RouterAgent
        router_agent = RouterAgent()
        
        # Test the method
        result = asyncio.run(router_agent.retrieve_top_k_nodes("test query", 5))
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 'node1')
        
    @patch('distributed.router.redis.Redis')
    @patch('distributed.router.Neo4jService')
    def test_retrieve_top_k_nodes_failure(self, mock_neo4j_service, mock_redis):
        """Test failure in retrieving top-k nodes"""
        # Setup mocks
        mock_redis.return_value = self.mock_redis
        mock_neo4j_service.return_value = self.mock_neo4j_service
        
        # Mock Neo4j to raise an exception
        self.mock_neo4j_session.run.side_effect = Exception("Database error")
        
        # Import and instantiate RouterAgent
        from distributed.router import RouterAgent
        router_agent = RouterAgent()
        
        # Test the method
        result = asyncio.run(router_agent.retrieve_top_k_nodes("test query", 5))
        
        # Assertions
        self.assertEqual(result, [])
        
    def test_calculate_token_budget(self):
        """Test token budget calculation"""
        # Import RouterAgent
        from distributed.router import RouterAgent
        router_agent = RouterAgent.__new__(RouterAgent)  # Create instance without calling __init__
        
        # Test data
        nodes = [
            {'id': 'node1', 'context_window': 'This is a test context with several words'},
            {'id': 'node2', 'context_window': 'Another test context with more words to exceed budget'}
        ]
        
        # Test with sufficient budget
        result = router_agent.calculate_token_budget(nodes, max_tokens=100)
        self.assertEqual(len(result), 2)
        
        # Test with limited budget
        result = router_agent.calculate_token_budget(nodes, max_tokens=5)
        self.assertLessEqual(len(result), 2)
        
    @patch('distributed.router.redis.Redis')
    @patch('distributed.router.Neo4jService')
    @patch('distributed.router.PipelineExecutor')
    def test_plan_execution(self, mock_pipeline_executor, mock_neo4j_service, mock_redis):
        """Test execution planning"""
        # Setup mocks
        mock_redis.return_value = self.mock_redis
        mock_neo4j_service.return_value = self.mock_neo4j_service
        mock_pipeline_executor.return_value = self.mock_pipeline_executor
        
        # Import and instantiate RouterAgent
        from distributed.router import RouterAgent
        router_agent = RouterAgent()
        
        # Mock the retrieve_top_k_nodes method
        with patch.object(router_agent, 'retrieve_top_k_nodes', return_value=[
            {'id': 'node1', 'context_window': 'test context'}
        ]):
            # Test the method
            result = asyncio.run(router_agent.plan_execution("test query", 5, 4096))
            
            # Assertions
            self.assertIn('plan_id', result)
            self.assertIn('execution_plan', result)
            self.assertEqual(result['execution_plan']['query'], 'test query')
            
    @patch('distributed.router.redis.Redis')
    @patch('distributed.router.Neo4jService')
    @patch('distributed.router.PipelineExecutor')
    def test_execute_plan_success(self, mock_pipeline_executor, mock_neo4j_service, mock_redis):
        """Test successful plan execution"""
        # Setup mocks
        mock_redis.return_value = self.mock_redis
        mock_neo4j_service.return_value = self.mock_neo4j_service
        mock_pipeline_executor.return_value = self.mock_pipeline_executor
        
        # Mock Redis get response
        execution_plan = {
            "nodes": [
                {'id': 'node1', 'context_window': 'test context', 'estimated_tokens': 5}
            ],
            "query": "test query"
        }
        self.mock_redis.get.return_value = str(execution_plan).replace("'", '"')
        
        # Mock pipeline execution result
        self.mock_pipeline_executor.run_pipeline.return_value = {
            "status": "success",
            "result": "test result"
        }
        
        # Import and instantiate RouterAgent
        from distributed.router import RouterAgent
        router_agent = RouterAgent()
        
        # Test the method
        result = asyncio.run(router_agent.execute_plan("test_plan_id", "test_pipeline"))
        
        # Assertions
        self.assertEqual(result['plan_id'], 'test_plan_id')
        self.assertEqual(result['successful_executions'], 1)
        
    @patch('distributed.router.redis.Redis')
    @patch('distributed.router.Neo4jService')
    def test_get_node_dependencies(self, mock_neo4j_service, mock_redis):
        """Test getting node dependencies"""
        # Setup mocks
        mock_redis.return_value = self.mock_redis
        mock_neo4j_service.return_value = self.mock_neo4j_service
        
        # Mock Neo4j response
        mock_record = Mock()
        mock_record.__getitem__.return_value = {'id': 'dep1', 'name': 'dependency node'}
        self.mock_neo4j_session.run.return_value = [mock_record]
        
        # Import and instantiate RouterAgent
        from distributed.router import RouterAgent
        router_agent = RouterAgent()
        
        # Test the method
        result = router_agent.get_node_dependencies("test_node_id")
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 'dep1')
        
    @patch('distributed.router.redis.Redis')
    @patch('distributed.router.Neo4jService')
    def test_get_node_subgraph(self, mock_neo4j_service, mock_redis):
        """Test getting node subgraph"""
        # Setup mocks
        mock_redis.return_value = self.mock_redis
        mock_neo4j_service.return_value = self.mock_neo4j_service
        
        # Mock Neo4j response
        mock_record = Mock()
        mock_record.__getitem__.side_effect = lambda key: {
            'nodes': [{'id': 'node1'}, {'id': 'node2'}],
            'rels': [{'start': 1, 'end': 2, 'type': 'CONNECTED'}]
        }[key]
        self.mock_neo4j_session.run.return_value.single.return_value = mock_record
        
        # Import and instantiate RouterAgent
        from distributed.router import RouterAgent
        router_agent = RouterAgent()
        
        # Test the method
        result = router_agent.get_node_subgraph("test_node_id", 2)
        
        # Assertions
        self.assertIn('nodes', result)
        self.assertIn('relationships', result)
        self.assertEqual(result['center_node'], 'test_node_id')
        
    @patch('distributed.router.redis.Redis')
    @patch('distributed.router.Neo4jService')
    def test_update_node_relevance(self, mock_neo4j_service, mock_redis):
        """Test updating node relevance"""
        # Setup mocks
        mock_redis.return_value = self.mock_redis
        mock_neo4j_service.return_value = self.mock_neo4j_service
        
        # Import and instantiate RouterAgent
        from distributed.router import RouterAgent
        router_agent = RouterAgent()
        
        # Test the method
        result = router_agent.update_node_relevance("test_node_id", 0.8)
        
        # Assertions
        self.assertTrue(result)
        self.mock_neo4j_session.run.assert_called_once()

if __name__ == '__main__':
    unittest.main()
