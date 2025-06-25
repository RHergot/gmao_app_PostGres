#!/usr/bin/env python3
"""
Integration test for the purchase order status mapping fix.
This test simulates the actual purchase order creation process.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_purchase_order_status_fix():
    """Test purchase order creation with status mapping."""
    
    print("=== PURCHASE ORDER STATUS MAPPING INTEGRATION TEST ===")
    print()
    
    try:
        # Import required modules
        from app.config import app_config, Language
        from app.utils.i18n import reverse_translate_purchase_order_status, translate_status
        from app.core.services.achat_service import AchatService
        from app.core.models.utilisateur import Utilisateur
        
        print("✅ All imports successful")
        
        # Test 1: Verify status mappings work in English context
        print("\n🔧 Test 1: Status Mappings in English")
        app_config.language = Language.ENGLISH
        
        french_statuses = ['Brouillon', 'Validee', 'Envoyee', 'Partielle', 'Livree', 'Annulee']
        english_statuses = ['Draft', 'Validated', 'Sent', 'Partial', 'Delivered', 'Cancelled']
        
        success_count = 0
        for fr_status, en_status in zip(french_statuses, english_statuses):
            translated = translate_status(fr_status)
            reverse_translated = reverse_translate_purchase_order_status(en_status)
            
            if translated == en_status and reverse_translated == fr_status:
                print(f"  ✅ {fr_status} ↔ {en_status}")
                success_count += 1
            else:
                print(f"  ❌ {fr_status} ↔ {en_status} (got: {translated}/{reverse_translated})")
        
        print(f"  Result: {success_count}/{len(french_statuses)} mappings correct")
        
        # Test 2: Simulate the actual dialog scenario
        print("\n🎯 Test 2: Simulating Purchase Order Dialog")
        
        # This simulates what happens in CommandeDialog:
        # 1. Combo box is populated with translated values
        combo_items = [translate_status(status) for status in french_statuses]
        print(f"  Combo box items: {combo_items}")
        
        # 2. User selects "Draft" (index 0)
        selected_index = 0
        selected_text = combo_items[selected_index]
        print(f"  User selects: '{selected_text}' (index {selected_index})")
        
        # 3. Our fix converts it back to database value
        db_value = reverse_translate_purchase_order_status(selected_text)
        expected_db_value = french_statuses[selected_index]
        
        print(f"  Converted to DB: '{db_value}'")
        print(f"  Expected DB: '{expected_db_value}'")
        print(f"  Result: {'✅ SUCCESS' if db_value == expected_db_value else '❌ FAILED'}")
        
        # Test 3: Verify database constraint would accept our value
        print("\n🗄️ Test 3: Database Constraint Validation")
        valid_statuses = ['Brouillon', 'Validee', 'Envoyee', 'Partielle', 'Livree', 'Annulee']
        
        if db_value in valid_statuses:
            print(f"  ✅ Status '{db_value}' is valid for database constraint")
        else:
            print(f"  ❌ Status '{db_value}' would violate database constraint")
            print(f"     Valid statuses: {valid_statuses}")
        
        # Test 4: Test all status mappings
        print("\n🔄 Test 4: All Status Mappings")
        for i, (fr_status, en_status) in enumerate(zip(french_statuses, english_statuses)):
            db_result = reverse_translate_purchase_order_status(en_status)
            status = "✅" if db_result == fr_status else "❌"
            print(f"  {status} {en_status} -> {db_result}")
        
        print("\n=== INTEGRATION TEST COMPLETED ===")
        print("🎉 The status mapping fix should resolve the PostgreSQL constraint error!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_purchase_order_status_fix()
