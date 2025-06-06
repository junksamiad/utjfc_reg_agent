#!/usr/bin/env python3
# Edge case tests for person name validation

from person_name_validation import validate_person_name

def test_edge_cases():
    """Test challenging edge cases for name validation"""
    
    print('🧪 CHALLENGING NAME VALIDATION TESTS')
    print('=' * 50)
    print()
    
    # Test cases with expected results
    tests = [
        # Three-part double-barrel surnames
        ('Sarah Jane Smith-Jones', True),
        ('Mary Elizabeth Foster-Brown', True),
        
        # Irish names with straight apostrophes
        ("Patrick O'Boyle", True),
        ("Siobhan O'Connor", True),
        ("Michael O'Sullivan", True),
        
        # Scottish names
        ('Donald McDonald', True),
        ('Fiona McGregor', True),
        ('Ian MacLeod', True),
        
        # Single letter cases
        ('Mark X', True),
        ('X Y', True),
        ('A B', True),
        
        # Special characters (should fail)
        ('% %', False),
        ('John Smith123', False),
        ('Mary@Jane', False),
        ('Bob#Smith', False),
        ('Lisa & Tom', False),
        ('Mike_Johnson', False),
        ('Sam.Wilson', False),
        
        # Whitespace handling
        ('  John   Smith  ', True),
        
        # Minimal cases
        ('', False),
        ('   ', False),
        ('J', False),
        ('John', False),
        
        # Complex valid cases
        ("D'Angelo Martinez", True),
        ("La'Shawn Johnson", True),
        ('Mary-Kate Ashley-Smith', True),
        ('Von Der Berg', True),
        
        # Very long names
        ('A' * 30 + ' ' + 'B' * 30, True),
    ]
    
    passed = 0
    failed = 0
    
    for i, (name, expected_valid) in enumerate(tests, 1):
        result = validate_person_name(name)
        actual_valid = result['valid']
        
        if actual_valid == expected_valid:
            status = '✅ PASS'
            passed += 1
        else:
            status = '❌ FAIL'  
            failed += 1
        
        print(f'{i:2d}. {status} | Input: "{name}"')
        print(f'    Expected: {"VALID" if expected_valid else "INVALID"}')
        print(f'    Actual: {"VALID" if actual_valid else "INVALID"}')
        print(f'    Message: {result["message"]}')
        
        if actual_valid:
            print(f'    Parts: {result["parts"]}')
            print(f'    Normalized: "{result["normalized_name"]}"')
        
        print()
    
    print('=' * 50)
    print(f'📊 RESULTS: {passed} passed, {failed} failed')
    print('=' * 50)
    
    return failed == 0

if __name__ == "__main__":
    success = test_edge_cases()
    exit(0 if success else 1) 