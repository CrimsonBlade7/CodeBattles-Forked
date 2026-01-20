"""
utils.py

This file contains helper functions that perform specific tasks.
The complex logic for running the user's Python code securely (well, somewhat securely)
is kept here to keep the main code clean.
"""

import json
import subprocess
from typing import List, Dict, Any

def execute_code(code: str, function_signature: str, test_cases: List[Dict]) -> Dict[str, Any]:
    """
    Execute Python code submitted by a player against a set of test cases.
    
    Args:
        code: The Python code written by the player.
        function_signature: The definition of the function they need to write (e.g., 'def twoSum(...)').
        test_cases: A list of inputs and expected outputs to test their code.
        
    Returns:
        A dictionary containing:
        - passed: Boolean, True if all tests passed.
        - testResults: List of results for each test case.
        - error: String, error message if something crashed.
    """
    
    # 1. SPECIAL DEBUG TRICK
    # If the code contains this specific comment, we automatically pass it.
    # This is useful for testing the game flow without writing real algorithms.
    if '# DEBUG: Auto-complete' in code:
        return {
            'passed': True,
            'testResults': [{'passed': True, 'input': 'DEBUG', 'expected': 'SKIP', 'actual': 'SKIP'}],
            'error': None
        }
    
    try:
        # 2. BUILD THE TEST SCRIPT
        # We are going to create a temporary Python script that includes:
        # - The player's code
        # - A test runner that loops through inputs and checks outputs
        script = f"""
{code}

# Test runner setup
import json
test_results = []
"""
        
        # Add code to run each test case
        for i, test_case in enumerate(test_cases):
            input_dict = test_case['input']
            expected = test_case['expectedOutput']
            
            # Extract function name from signature (e.g., 'def twoSum(...)' -> 'twoSum')
            function_name = function_signature.split('(')[0].replace('def ', '').strip()
            
            # Format arguments (e.g., "nums=[2,7], target=9")
            args_str = ', '.join([f"{k}={repr(v)}" for k, v in input_dict.items()])
            
            # Add the test logic to the script
            script += f"""
try:
    # Call the user's function
    result_{i} = {function_name}({args_str})
    expected_{i} = {repr(expected)}
    
    # Check if result matches expected
    passed_{i} = result_{i} == expected_{i}
    
    # Record the result
    test_results.append({{
        'passed': passed_{i},
        'input': {json.dumps(input_dict)},
        'expected': expected_{i},
        'actual': result_{i}
    }})
except Exception as e:
    # If the user's code crashes, record the error
    test_results.append({{
        'passed': False,
        'input': {json.dumps(input_dict)},
        'expected': {repr(expected)},
        'actual': None,
        'error': str(e)
    }})
"""
        
        # Finally, print the results as JSON so we can read them back
        script += """
print(json.dumps(test_results))
"""
        
        # 3. RUN THE SCRIPT
        # We use subprocess to run this script in a separate process.
        # This prevents the user's code from crashing OUR server.
        process = subprocess.Popen(
            ['python', '-c', script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for max 10 seconds
        stdout, stderr = process.communicate(timeout=10)
        
        # 4. HANDLE ERRORS
        if process.returncode != 0:
            return {
                'passed': False,
                'testResults': [],
                'error': stderr or 'Execution failed'
            }
        
        # 5. PARSE RESULTS
        try:
            # The last line of output should be our JSON results
            test_results = json.loads(stdout.strip().split('\n')[-1])
            all_passed = all(t.get('passed', False) for t in test_results)
            return {
                'passed': all_passed,
                'testResults': test_results,
                'error': None
            }
        except json.JSONDecodeError:
            return {
                'passed': False,
                'testResults': [],
                'error': 'Could not parse test results'
            }
            
    except subprocess.TimeoutExpired:
        return {
            'passed': False,
            'testResults': [],
            'error': 'Code execution timed out (10 seconds max)'
        }
    except Exception as e:
        return {
            'passed': False,
            'testResults': [],
            'error': str(e)
        }
