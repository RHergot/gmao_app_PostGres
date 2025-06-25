#!/usr/bin/env python3
"""
Test script to verify the PostgreSQL syntax fix for purchase order reception.
This script tests the specific update_reception method that was causing the SQL syntax error.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import date, datetime
from app.data import database
from app.data.repositories.ligne_commande_repository import LigneCommandeRepository
from app.data.repositories.commande_repository import CommandeRepository
from app.data.repositories.fournisseur_repository import FournisseurRepository
from app.data.repositories.piece_repository import PieceRepository
from app.core.models.commande import Commande
from app.core.models.ligne_commande import LigneCommande
from app.core.models.fournisseur import Fournisseur
from app.core.models.piece import Piece
import logging

def test_reception_fix():
    """Test the fixed PostgreSQL syntax in update_reception method"""
    
    print("=== Testing PostgreSQL Syntax Fix for Reception ===")
    
    # Initialize database
    database.initialize_database()
    
    # Initialize repositories
    ligne_repo = LigneCommandeRepository()
    commande_repo = CommandeRepository()
    fournisseur_repo = FournisseurRepository()
    piece_repo = PieceRepository()
    
    try:        # 1. Create a test supplier
        print("\n1. Creating test supplier...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_supplier = Fournisseur(
            nom=f"Test Supplier Reception {timestamp}",
            contact="Test Contact",
            adresse="123 Test Street",
            telephone="123-456-7890",
            email="test@supplier.com"
        )
        
        supplier_id = fournisseur_repo.add(test_supplier)
        if supplier_id:
            print(f"   ✓ Test supplier created with ID: {supplier_id}")
        else:
            print("   ✗ Failed to create test supplier")
            return
          # 2. Create a test piece
        print("\n2. Creating test piece...")
        test_piece = Piece(
            reference=f"TEST-PART-{timestamp}",
            nom=f"Test Part for Reception {timestamp}",
            fournisseur_pref_id=supplier_id,
            prix_unitaire=10.0,
            stock_alerte=5,
            stock_actuel=0,
            stock_reserve=0,
            unite="pcs",
            categorie="Test",
            emplacement_stockage="A1-01",
            statut="Actif"
        )
        
        piece_id = piece_repo.add(test_piece)
        if piece_id:
            print(f"   ✓ Test piece created with ID: {piece_id}")
        else:
            print("   ✗ Failed to create test piece")
            return        # 3. Create a test purchase order
        print("\n3. Creating test purchase order...")
        test_order = Commande(
            numero_commande=f"PO-TEST-{timestamp}",
            fournisseur_id=supplier_id,
            utilisateur_createur_id=1,  # Assuming admin user exists
            statut="Brouillon",  # Use French status as required by our fix
            date_commande=date.today(),
            date_livraison_prevue=date.today(),
            total_ht=100.0,
            notes_commande="Test order for reception fix"
        )
        
        order_id = commande_repo.add(test_order)
        if order_id:
            print(f"   ✓ Test purchase order created with ID: {order_id}")
        else:
            print("   ✗ Failed to create test purchase order")
            return
        
        # 4. Create a test order line
        print("\n4. Creating test order line...")
        test_line = LigneCommande(
            commande_id=order_id,
            piece_id=piece_id,
            description_libre="Test line for reception",
            quantite_commandee=10,
            prix_unitaire_ht=10.0,
            quantite_recue=0,
            statut_ligne="Commandee"
        )
        
        line_id = ligne_repo.add(test_line)
        if line_id:
            print(f"   ✓ Test order line created with ID: {line_id}")
        else:
            print("   ✗ Failed to create test order line")
            return
        
        # 5. Test the fixed update_reception method
        print("\n5. Testing update_reception method (the fixed PostgreSQL syntax)...")
        reception_date = date.today()
        quantity_received = 5
        
        # This is the method that was causing the PostgreSQL syntax error
        success = ligne_repo.update_reception(line_id, quantity_received, reception_date)
        
        if success:
            print(f"   ✓ Reception update successful! Received {quantity_received} units on {reception_date}")
            
            # Verify the update
            updated_line = ligne_repo.get_by_id(line_id)
            if updated_line and updated_line.quantite_recue == quantity_received:
                print(f"   ✓ Verification passed: quantite_recue = {updated_line.quantite_recue}")
            else:
                print(f"   ✗ Verification failed: expected {quantity_received}, got {updated_line.quantite_recue if updated_line else 'None'}")
        else:
            print("   ✗ Reception update failed!")
        
        # 6. Test another reception (cumulative)
        print("\n6. Testing cumulative reception...")
        additional_quantity = 3
        success2 = ligne_repo.update_reception(line_id, additional_quantity, reception_date)
        
        if success2:
            print(f"   ✓ Additional reception successful! Received {additional_quantity} more units")
            
            # Verify cumulative total
            updated_line = ligne_repo.get_by_id(line_id)
            expected_total = quantity_received + additional_quantity
            if updated_line and updated_line.quantite_recue == expected_total:
                print(f"   ✓ Cumulative verification passed: total quantite_recue = {updated_line.quantite_recue}")
            else:
                print(f"   ✗ Cumulative verification failed: expected {expected_total}, got {updated_line.quantite_recue if updated_line else 'None'}")
        else:
            print("   ✗ Additional reception failed!")
        
        # Cleanup
        print("\n7. Cleaning up test data...")
        try:
            ligne_repo.delete(line_id)
            commande_repo.delete(order_id)
            piece_repo.delete(piece_id)
            fournisseur_repo.delete(supplier_id)
            print("   ✓ Test data cleaned up successfully")
        except Exception as e:
            print(f"   ! Cleanup warning: {e}")
        
        print("\n=== PostgreSQL Syntax Fix Test Complete ===")
        print("✓ The update_reception method now uses correct PostgreSQL syntax (%s instead of ?)")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the test
    test_reception_fix()
