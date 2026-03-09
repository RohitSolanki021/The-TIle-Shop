"""
Additional Backend Tests for Edge Cases
======================================
Testing edge cases and validations for the swapped calculation methods
"""

import requests
import json
import uuid

BASE_URL = "https://granite-tile-swap.preview.emergentagent.com"
API_URL = f"{BASE_URL}/api"

def print_separator(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)

def print_test_result(test_name, success, details=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"    {details}")

def create_test_customer():
    """Create a test customer for invoice testing"""
    customer_data = {
        "name": "Edge Case Tester",
        "phone": "8888777766",
        "address": "456 Edge Test Road"
    }
    
    try:
        response = requests.post(f"{API_URL}/customers", json=customer_data)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

def test_granite_with_discount(customer_id):
    """Test Granite calculation with discount"""
    print_separator("GRANITE WITH DISCOUNT")
    
    invoice_data = {
        "customer_id": customer_id,
        "line_items": [{
            "product_type": "granite",
            "location": "Master Bedroom",
            "tile_name": "White Marble Granite",
            "extra_sqft": 25.0,
            "rate_per_sqft": 200.0,
            "discount_percent": 15  # 15% discount
        }]
    }
    
    try:
        response = requests.post(f"{API_URL}/invoices", json=invoice_data)
        if response.status_code == 200:
            invoice = response.json()
            line_item = invoice['line_items'][0]
            
            # Expected: 25 × 200 = 5000, 15% discount = 750, final = 4250
            expected_before_discount = 25.0 * 200.0  # 5000
            expected_discount = expected_before_discount * 0.15  # 750
            expected_final = expected_before_discount - expected_discount  # 4250
            
            before_discount_correct = abs(line_item['amount_before_discount'] - expected_before_discount) < 0.01
            discount_correct = abs(line_item['discount_amount'] - expected_discount) < 0.01
            final_correct = abs(line_item['final_amount'] - expected_final) < 0.01
            
            all_correct = before_discount_correct and discount_correct and final_correct
            
            print_test_result("Granite with 15% Discount", all_correct)
            print(f"    Before Discount - Expected: {expected_before_discount}, Actual: {line_item['amount_before_discount']}")
            print(f"    Discount Amount - Expected: {expected_discount}, Actual: {line_item['discount_amount']}")
            print(f"    Final Amount - Expected: {expected_final}, Actual: {line_item['final_amount']}")
            
            # Cleanup
            invoice_id = invoice['invoice_id'].replace(' ', '%20').replace('/', '%2F')
            requests.delete(f"{API_URL}/invoices/{invoice_id}")
            
            return all_correct
        else:
            print_test_result("Granite with Discount", False, f"API Error: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("Granite with Discount", False, f"Error: {str(e)}")
        return False

def test_tile_pieces_edge_cases(customer_id):
    """Test Tile Pieces with edge cases"""
    print_separator("TILE PIECES EDGE CASES")
    
    # Test with quantity = 1 and high rate
    invoice_data = {
        "customer_id": customer_id,
        "line_items": [{
            "product_type": "tile_pieces",
            "location": "Accent Wall",
            "tile_name": "Designer Border Tile",
            "quantity": 1,
            "rate_per_piece": 1500.0,
            "discount_percent": 5
        }]
    }
    
    try:
        response = requests.post(f"{API_URL}/invoices", json=invoice_data)
        if response.status_code == 200:
            invoice = response.json()
            line_item = invoice['line_items'][0]
            
            # Expected: 1 × 1500 = 1500, 5% discount = 75, final = 1425
            expected_before_discount = 1 * 1500.0
            expected_final = expected_before_discount * 0.95
            
            before_correct = abs(line_item['amount_before_discount'] - expected_before_discount) < 0.01
            final_correct = abs(line_item['final_amount'] - expected_final) < 0.01
            
            all_correct = before_correct and final_correct
            
            print_test_result("Tile Pieces (Single Unit)", all_correct)
            print(f"    Quantity: {line_item['quantity']}, Rate per piece: {line_item['rate_per_piece']}")
            print(f"    Before Discount: {line_item['amount_before_discount']} (Expected: {expected_before_discount})")
            print(f"    Final Amount: {line_item['final_amount']} (Expected: {expected_final})")
            
            # Cleanup
            invoice_id = invoice['invoice_id'].replace(' ', '%20').replace('/', '%2F')
            requests.delete(f"{API_URL}/invoices/{invoice_id}")
            
            return all_correct
        else:
            print_test_result("Tile Pieces Edge Case", False, f"API Error: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("Tile Pieces Edge Case", False, f"Error: {str(e)}")
        return False

def test_mixed_invoice_calculations(customer_id):
    """Test invoice with all three product types to ensure calculations don't interfere"""
    print_separator("MIXED PRODUCT TYPES INVOICE")
    
    invoice_data = {
        "customer_id": customer_id,
        "line_items": [
            {
                "product_type": "granite",
                "location": "Kitchen",
                "tile_name": "Black Granite",
                "extra_sqft": 30.0,
                "rate_per_sqft": 150.0,
                "discount_percent": 10
            },
            {
                "product_type": "tile_pieces",
                "location": "Bathroom",
                "tile_name": "Mosaic Tiles",
                "quantity": 20,
                "rate_per_piece": 50.0,
                "discount_percent": 5
            },
            {
                "product_type": "tiles_box",
                "location": "Living Room",
                "tile_name": "Floor Tiles",
                "box_qty": 8,
                "coverage": 25.0,
                "extra_sqft": 15.0,
                "rate_per_sqft": 75.0,
                "discount_percent": 0
            }
        ],
        "transport_charges": 500,
        "gst_percent": 18
    }
    
    try:
        response = requests.post(f"{API_URL}/invoices", json=invoice_data)
        if response.status_code == 200:
            invoice = response.json()
            
            # Calculate expected amounts
            # Granite: 30 × 150 = 4500, 10% discount = 4050
            granite_expected = 30.0 * 150.0 * 0.9  # 4050
            
            # Tile pieces: 20 × 50 = 1000, 5% discount = 950
            tile_pieces_expected = 20 * 50.0 * 0.95  # 950
            
            # Tiles box: (8 × 25 + 15) × 75 = 215 × 75 = 16125
            tiles_box_expected = ((8 * 25.0) + 15.0) * 75.0  # 16125
            
            subtotal_expected = granite_expected + tile_pieces_expected + tiles_box_expected  # 21125
            gst_expected = subtotal_expected * 0.18  # 3802.5
            grand_total_expected = subtotal_expected + 500 + gst_expected  # 25427.5
            
            # Check individual line items
            granite_item = next(item for item in invoice['line_items'] if item['product_type'] == 'granite')
            tile_pieces_item = next(item for item in invoice['line_items'] if item['product_type'] == 'tile_pieces')
            tiles_box_item = next(item for item in invoice['line_items'] if item['product_type'] == 'tiles_box')
            
            granite_correct = abs(granite_item['final_amount'] - granite_expected) < 0.01
            tile_pieces_correct = abs(tile_pieces_item['final_amount'] - tile_pieces_expected) < 0.01
            tiles_box_correct = abs(tiles_box_item['final_amount'] - tiles_box_expected) < 0.01
            subtotal_correct = abs(invoice['subtotal'] - subtotal_expected) < 0.01
            gst_correct = abs(invoice['gst_amount'] - gst_expected) < 0.01
            grand_total_correct = abs(invoice['grand_total'] - grand_total_expected) < 0.01
            
            all_correct = all([granite_correct, tile_pieces_correct, tiles_box_correct, 
                             subtotal_correct, gst_correct, grand_total_correct])
            
            print_test_result("Mixed Product Types Invoice", all_correct)
            print(f"    Granite final: {granite_item['final_amount']} (Expected: {granite_expected})")
            print(f"    Tile Pieces final: {tile_pieces_item['final_amount']} (Expected: {tile_pieces_expected})")
            print(f"    Tiles Box final: {tiles_box_item['final_amount']} (Expected: {tiles_box_expected})")
            print(f"    Subtotal: {invoice['subtotal']} (Expected: {subtotal_expected})")
            print(f"    GST: {invoice['gst_amount']} (Expected: {gst_expected})")
            print(f"    Grand Total: {invoice['grand_total']} (Expected: {grand_total_expected})")
            
            # Cleanup
            invoice_id = invoice['invoice_id'].replace(' ', '%20').replace('/', '%2F')
            requests.delete(f"{API_URL}/invoices/{invoice_id}")
            
            return all_correct
        else:
            print_test_result("Mixed Products Invoice", False, f"API Error: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("Mixed Products Invoice", False, f"Error: {str(e)}")
        return False

def main():
    """Run edge case tests"""
    print("Backend Testing: Edge Cases for Swapped Calculations")
    print(f"API URL: {API_URL}")
    
    # Create test customer
    customer = create_test_customer()
    if not customer:
        print("❌ Failed to create test customer. Stopping tests.")
        return
    
    customer_id = customer['customer_id']
    
    results = {}
    
    try:
        # Run edge case tests
        results['granite_discount'] = test_granite_with_discount(customer_id)
        results['tile_pieces_edge'] = test_tile_pieces_edge_cases(customer_id)
        results['mixed_products'] = test_mixed_invoice_calculations(customer_id)
        
    finally:
        # Cleanup
        print_separator("CLEANUP")
        try:
            response = requests.delete(f"{API_URL}/customers/{customer_id}")
            print_test_result("Cleanup Customer", response.status_code == 200)
        except Exception:
            print_test_result("Cleanup Customer", False)
    
    # Summary
    print_separator("EDGE CASE TEST SUMMARY")
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    print(f"\nEdge Cases: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All edge case tests PASSED!")
    else:
        print("⚠️  Some edge case tests FAILED.")

if __name__ == "__main__":
    main()