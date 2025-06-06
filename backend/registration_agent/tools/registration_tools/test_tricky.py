#!/usr/bin/env python3
# Test the trickiest edge cases for name validation

from person_name_validation import validate_person_name

def test_tricky_cases():
    """Test the most challenging edge cases"""
    
    # Test curly apostrophes and unusual cases
    tricky_cases = [
        ('Patrick O'Boyle', 'Curly apostrophe (should fail)'),
        ('Deh'yrus Marsh', 'Curly apostrophe in middle (should fail)'),
        ("Mary's Child", "Possessive-like name"),
        ("Jo-Ann O'Brien-Smith", "Complex combination"),
        ('MArk X', 'Mixed case with single letter'),
        ('john smith', 'All lowercase'),
        ('JOHN SMITH', 'All uppercase'),
        ('Jean-Pierre', 'Single hyphenated name (should fail - only 1 part)'),
        ('Anne- Marie', 'Space after hyphen (should fail)'),
        ('Anne -Marie', 'Space before hyphen (should fail)'),
        ('O'Malley Smith', 'Straight apostrophe at start'),
        ('José María', 'Accented characters (should fail)'),
        ('François', 'Single French name with accent (should fail)'),
        ('李 明', 'Chinese characters (should fail)'),
        ('Mc Donald', 'Mc with space (valid - 2 parts)'),
        ('MacDonald-Smith', 'Mac with hyphen'),
        ("D'Angelo O'Brien", "Multiple apostrophes"),
        ('Van Der Berg-Jones', 'Noble prefix with hyphen'),
        (' John Smith', 'Leading space'),
        ('John Smith ', 'Trailing space'),
    ]
    
    print('🔍 TESTING TRICKIEST EDGE CASES')
    print('=' * 50)
    print()
    
    for i, (name, description) in enumerate(tricky_cases, 1):
        result = validate_person_name(name)
        status = '✅ VALID' if result['valid'] else '❌ INVALID'
        
        print(f'{i:2d}. {status} | {description}')
        print(f'    Input: "{name}"')
        print(f'    Result: {result["message"]}')
        
        if result['valid']:
            print(f'    Parts: {result["parts"]}')
            print(f'    Normalized: "{result["normalized_name"]}"')
        
        print()

if __name__ == "__main__":
    test_tricky_cases() 