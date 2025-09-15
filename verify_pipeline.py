"""
Simple verification script for pipeline functionality
"""

import json
import os

def verify_pipeline_config():
    """Verify that the pipeline configuration file exists and is valid"""
    config_path = "pipelines/graph_config.json"
    
    print("🔍 Checking pipeline configuration...")
    
    # Check if file exists
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    print(f"✅ Configuration file found: {config_path}")
    
    # Try to load and parse JSON
    try:
        with open(config_path, "r") as f:
            data = json.load(f)
        print(f"✅ Successfully parsed JSON with {len(data)} pipeline(s)")
        
        # Print pipeline information
        for i, pipeline in enumerate(data):
            print(f"  Pipeline {i+1}: {pipeline.get('id', 'Unknown ID')}")
            print(f"    Description: {pipeline.get('description', 'No description')}")
            print(f"    Nodes: {len(pipeline.get('nodes', []))}")
            print(f"    Edges: {len(pipeline.get('edges', []))}")
            
        return True
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
        return False

def verify_pipeline_structure():
    """Verify the pipeline directory structure"""
    print("\n🔍 Checking pipeline directory structure...")
    
    required_files = [
        "pipelines/__init__.py",
        "pipelines/graph_config.json",
        "backend/pipeline/__init__.py",
        "backend/pipeline/executor.py",
        "backend/api/pipelines.py"
    ]
    
    all_good = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (missing)")
            all_good = False
    
    return all_good

def main():
    """Main verification function"""
    print("🚀 Verifying pipeline functionality...")
    
    config_ok = verify_pipeline_config()
    structure_ok = verify_pipeline_structure()
    
    if config_ok and structure_ok:
        print("\n✅ All pipeline components verified successfully!")
        print("\nYou can now test the pipeline execution with the backend server.")
        return True
    else:
        print("\n❌ Some pipeline components have issues.")
        return False

if __name__ == "__main__":
    main()
