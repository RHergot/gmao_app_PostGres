#!/usr/bin/env python3
"""
Test script to verify the purchase order creation fix.
This script simulates the UI interaction to create a purchase order.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTranslator
from app.data.database import DatabaseManager
from app.data.repositories.achat_repository import AchatRepository
from app.data.repositories.fournisseur_repository import FournisseurRepository
from app.core.services.achat_service import AchatService
from app.utils.i18n import reverse_translate_purchase_order_status, translate_status
from app.data.models.commande import Commande
import logging

def test_purchase_order_creation():
    """Test purchase order creation with translated status"""
    
    # Initialize database and repositories
    db_manager = DatabaseManager()
    db_manager.initialize_schema()
    
    achat_repo = AchatRepository(db_manager)
    fournisseur_repo = FournisseurRepository(db_manager)
    achat_service = AchatService(achat_repo, fournisseur_repo)
    
    print("=== Testing Purchase Order Status Translation ===")
    
    # Test 1: Verify reverse translation works
    print("\n1. Testing reverse translation mapping:")
    test_statuses = ["Draft", "Validated", "Sent", "Partial", "Delivered", "Cancelled"]
    expected_french = ["Brouillon", "Validee", "Envoyee", "Partielle", "Livree", "Annulee"]
    
    for english, expected in zip(test_statuses, expected_french):
        french = reverse_translate_purchase_order_status(english)
        print(f"   {english} → {french} {'✓' if french == expected else '✗'}")
        
    # Test 2: Create a purchase order with translated status (simulating UI)
    print("\n2. Testing purchase order creation with 'Draft' status:")
    
    try:
        # Simulate what happens in the UI:
        # 1. User sees "Draft" in the combo box
        # 2. UI gets the text "Draft"
        # 3. We need to convert it back to "Brouillon" for the database
        
        statut_translated = "Draft"  # This is what comes from the UI
        statut_for_db = reverse_translate_purchase_order_status(statut_translated)
        
        print(f"   UI status: {statut_translated}")
        print(f"   DB status: {statut_for_db}")
        
        # Create a test purchase order
        test_commande = Commande(
            numero_commande="TEST-001",
            fournisseur_id=1,  # Assuming supplier ID 1 exists
            statut=statut_for_db,  # Use the converted status
            date_commande="2024-12-19",
            date_livraison_prevue="2024-12-26",
            montant_total=100.0,
            observations="Test purchase order for status translation"
        )
        
        # Try to create the purchase order
        result = achat_service.creer_commande(test_commande)
        
        if result:
            print(f"   ✓ Purchase order created successfully with ID: {result}")
            
            # Verify the status was saved correctly
            created_order = achat_service.get_commande_by_id(result)
            if created_order and created_order.statut == statut_for_db:
                print(f"   ✓ Status saved correctly in database: {created_order.statut}")
                
                # Test loading back to UI
                ui_status = translate_status(created_order.statut)
                print(f"   ✓ Status translated back for UI: {ui_status}")
                
                # Clean up - delete the test order
                try:
                    achat_service.supprimer_commande(result)
                    print(f"   ✓ Test order cleaned up")
                except Exception as e:
                    print(f"   ! Cleanup warning: {e}")
                    
            else:
                print(f"   ✗ Status verification failed")
        else:
            print(f"   ✗ Failed to create purchase order")
            
    except Exception as e:
        print(f"   ✗ Error during purchase order creation: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Test all status translations
    print("\n3. Testing all status round-trip translations:")
    for french_status in expected_french:
        try:
            # French → English → French
            english = translate_status(french_status)
            back_to_french = reverse_translate_purchase_order_status(english)
            success = back_to_french == french_status
            print(f"   {french_status} → {english} → {back_to_french} {'✓' if success else '✗'}")
        except Exception as e:
            print(f"   {french_status} → ERROR: {e}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Set up Qt application (required for translation system)
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Load English translations
    translator = QTranslator()
    translator.load("C:/Users/Richa/.vscode/Projets_Windsurf/gmao_app_PostGres/en_translations/en.qm")
    app.installTranslator(translator)
    
    # Run the test
    test_purchase_order_creation()
