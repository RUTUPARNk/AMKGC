"""
Simple verification script for pipeline executor implementation
"""

import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    # Try to import the PipelineExecutor class
    from pipeline.executor import PipelineExecutor
    print("✅ Successfully imported PipelineExecutor")
    
    # Check if the class has the expected methods
    expected_methods = [
        '__init__',
        'run_pipeline',
        '_build_execution_levels',
        '_get_conditional_edges',
        '_evaluate_condition',
        '_select_optimal_backend',
        '_execute_node',
        '_execute_ollama_model'
    ]
    
    missing_methods = []
    for method in expected_methods:
        if not hasattr(PipelineExecutor, method):
            missing_methods.append(method)
    
    if missing_methods:
        print(f"❌ Missing methods: {missing_methods}")
    else:
        print("✅ All expected methods are present")
    
    # Try to instantiate the executor
    try:
        executor = PipelineExecutor()
        print("✅ Successfully instantiated PipelineExecutor")
        
        # Check if supervisor functionality is available
        if hasattr(executor, 'supervisor'):
            print("✅ Supervisor functionality is available")
        else:
            print("⚠️ Supervisor functionality not available")
            
    except Exception as e:
        print(f"❌ Error instantiating PipelineExecutor: {e}")
        
    print("✅ Pipeline executor verification completed")
    
except ImportError as e:
    print(f"❌ Failed to import PipelineExecutor: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}
    import traceback
    traceback.print_exc()
