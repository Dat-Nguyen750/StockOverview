#!/usr/bin/env python3

import sys
import traceback

def test_imports():
    """Test importing each module to identify the issue"""
    
    modules_to_test = [
        'modules.data_fetcher',
        'modules.scoring', 
        'modules.llm_orchestrator',
        'modules.models',
        'modules.evaluator'
    ]
    
    for module_name in modules_to_test:
        print(f"\nTesting import of {module_name}:")
        try:
            module = __import__(module_name, fromlist=['*'])
            print(f"  ✓ Successfully imported {module_name}")
            print(f"  Available names: {[name for name in dir(module) if not name.startswith('_')]}")
        except Exception as e:
            print(f"  ✗ Failed to import {module_name}: {e}")
            print(f"  Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_imports() 