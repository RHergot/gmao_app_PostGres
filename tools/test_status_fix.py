#!/usr/bin/env python3
"""
Test script to verify the status mapping fix for purchase orders.
This script tests the translation functions in both French and English contexts.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import app_config, Language
from app.utils.i18n import reverse_translate_status, translate_status

def test_status_mapping():
    """Test status mapping in both directions and both languages."""
    
    print("=== TESTING STATUS MAPPING FIX ===")
    print()
    
    # Test database statuses (French keys)
    db_statuses = ['Brouillon', 'Validee', 'Envoyee', 'Partielle', 'Livree', 'Annulee']
    
    # Test in French context
    print("🇫🇷 Testing in FRENCH context:")
    app_config.language = Language.FRENCH
    
    for status in db_statuses:
        translated = translate_status(status)
        back_to_db = reverse_translate_status(translated)
        print(f"  {status} -> {translated} -> {back_to_db} {'✅' if back_to_db == status else '❌'}")
    
    print()
    
    # Test in English context  
    print("🇬🇧 Testing in ENGLISH context:")
    app_config.language = Language.ENGLISH
    
    for status in db_statuses:
        translated = translate_status(status)
        back_to_db = reverse_translate_status(translated)
        print(f"  {status} -> {translated} -> {back_to_db} {'✅' if back_to_db == status else '❌'}")
    
    print()
    
    # Test the specific scenario that was causing the error
    print("🔧 Testing the ERROR SCENARIO:")
    app_config.language = Language.ENGLISH
    
    # This simulates what happens in the UI:
    # 1. Combo box is populated with translated values
    combo_values = [translate_status(status) for status in db_statuses]
    print(f"  Combo box contains: {combo_values}")
    
    # 2. User selects "Draft" (which corresponds to "Brouillon")
    selected_ui_value = "Draft"
    print(f"  User selects: '{selected_ui_value}'")
    
    # 3. Our fix converts it back to database value
    db_value = reverse_translate_status(selected_ui_value)
    print(f"  Converted to DB value: '{db_value}'")
    print(f"  Result: {'✅ SUCCESS' if db_value == 'Brouillon' else '❌ FAILED'}")
    
    print()
    print("=== TEST COMPLETED ===")

if __name__ == "__main__":
    test_status_mapping()
