#!/usr/bin/env python3
# Comprehensive test for person name validation with challenging edge cases

from person_name_validation import validate_person_name
import json

def run_comprehensive_tests():
    """Run comprehensive tests on the name validation function"""
    
    # Comprehensive test cases
    test_cases = [
        # Three-part names with double-barrel surnames
        ('Sarah Jane Smith-Jones', 'Three parts with double-barrel surname'),
        ('Mary Elizabeth Foster-Brown', 'Three parts with double-barrel surname'),
        ('James Robert Wilson-Taylor', 'Three parts with double-barrel surname'),
        
        # Irish names with O' prefix (straight apostrophe)
        ("Patrick O'Boyle", "Irish O' name with straight apostrophe"),
        ("Siobhan O'Connor", "Irish O' name"),
        ("Michael O'Sullivan", "Irish O' name"),
        
        # Names with slanted/curly apostrophes (Unicode characters)
        ('Patrick O'Boyle', 'Irish name with curly apostrophe (U+2019)'),
        ('Sarah O'Neill', 'Irish name with curly apostrophe'),
        ('Deh'yrus Marsh', 'Name with curly apostrophe in middle'),
        
        # Scottish names with Mc prefix
        ('Donald McDonald', 'Scottish Mc name'),
        ('Fiona McGregor', 'Scottish Mc name'),
        ('Ian MacLeod', 'Scottish Mac name'),
        ('Hamish MacPherson', 'Scottish Mac name'),
        
        # Edge cases with special characters
        ('% %', 'Special characters only'),
        ('Mark X', 'Single letter surname'),
        ('X Y', 'Single letter names'),
        ('A B', 'Single letter names'),
        ('J K', 'Single letter names'),
        
        # Complex valid cases
        ('Mary-Jane O'Connor-Smith', 'Complex hyphenated name with apostrophe'),
        ('Jean-Pierre Van Der Berg', 'Four-part hyphenated name'),
        ('Anne-Marie Dubois-Martin', 'French double-barrel'),
        ('Carlos García-López', 'Spanish double surname'),
        
        # Invalid cases with numbers/symbols
        ('John Smith123', 'Name with numbers'),
        ('Mary@Jane', 'Name with @ symbol'),
        ('Bob#Smith', 'Name with # symbol'),
        ('Lisa & Tom', 'Name with & symbol'),
        ('Mike_Johnson', 'Name with underscore'),
        ('Sam.Wilson', 'Name with period'),
        ('Tom+Jerry', 'Name with plus symbol'),
        ('Anna*Belle', 'Name with asterisk'),
        
        # Edge whitespace cases
        ('  John   Smith  ', 'Extra whitespace'),
        ('Mary\t\tJane', 'Tab characters (should be invalid)'),
        
        # Empty and minimal cases
        ('', 'Empty string'),
        ('   ', 'Only whitespace'),
        ('J', 'Single name only'),
        ('John', 'First name only'),
        
        # Tricky valid cases
        ("D'Angelo Martinez", "Name starting with D'"),
        ("La'Shawn Johnson", "Name with apostrophe in middle"),
        ("Mary-Kate Ashley-Smith", 'Multiple hyphens'),
        ("Von Der Berg", 'German nobility prefix'),
        
        # Unicode and international characters (should be invalid in our system)
        ('José María', 'Spanish name with accent'),
        ('François Müller', 'French/German with umlauts'),
        ('李明', 'Chinese characters'),
        
        # Boundary cases
        ('A' * 50 + ' ' + 'B' * 50, 'Very long names'),
        ('Jo-Anne Smith-Jones-Brown', 'Triple-barrel surname'),
    ]

    print('🧪 COMPREHENSIVE NAME VALIDATION TEST')
    print('=' * 60)
    print()

    valid_count = 0
    invalid_count = 0
    
    for i, (name, description) in enumerate(test_cases, 1):
        result = validate_person_name(name)
        status = '✅ VALID' if result['valid'] else '❌ INVALID'
        
        if result['valid']:
            valid_count += 1
        else:
            invalid_count += 1
        
        print(f'{i:2d}. {status} | {description}')
        print(f'    Input: "{name}"')
        print(f'    Result: {result["message"]}')
        
        if result['valid']:
            print(f'    Parts: {result["parts"]}')
            print(f'    Normalized: "{result["normalized_name"]}"')
        
        print()
    
    print('=' * 60)
    print(f'📊 SUMMARY: {valid_count} valid, {invalid_count} invalid out of {len(test_cases)} total tests')
    print('=' * 60)

if __name__ == "__main__":
    run_comprehensive_tests() 