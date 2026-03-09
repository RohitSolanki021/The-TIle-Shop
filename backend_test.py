"""
Backend Test for Swapped Calculation Methods
============================================
Testing the swapped calculation methods for Granite and Tile Pieces:
- Granite: NOW calculated in square feet (total_sqft × rate_per_sqft) instead of pieces
- Tile Pieces: NOW calculated in pieces (quantity × rate_per_piece) instead of sqft
"""

import requests
import json
import uuid

# Get backend URL from frontend .env
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

def test_health_check():
    """Verify API is accessible"""
    print_separator("HEALTH CHECK")
    try:
        response = requests.get(f"{API_URL}/health")
        success = response.status_code == 200
        print_test_result("API Health Check", success, f"Status: {response.status_code}")
        if success:
            data = response.json()
            print(f"    Response: {data}")
        return success
    except Exception as e:
        print_test_result("API Health Check", False, f"Error: {str(e)}")
        return False

def create_test_customer():
    """Create a test customer for invoice testing"""
    print_separator("CREATE TEST CUSTOMER")
    customer_data = {
        "name": "John Smith",
        "phone": "9876543210",
        "address": "123 Test Street, Test City",
        "gstin": "TEST123456789"
    }
    
    try:
        response = requests.post(f"{API_URL}/customers", json=customer_data)
        success = response.status_code == 200
        
        if success:
            customer = response.json()
            print_test_result("Create Customer", True, f"Customer ID: {customer['customer_id']}")
            return customer
        else:
            print_test_result("Create Customer", False, f"Status: {response.status_code}")
            print(f"    Response: {response.text}")
            return None
    except Exception as e:
        print_test_result("Create Customer", False, f"Error: {str(e)}")
        return None

def test_granite_sqft_calculation(customer_id):
    """Test Granite calculation - NOW uses sqft method"""
    print_separator("TEST GRANITE CALCULATION (SQFT-BASED)")
    
    # Test data: Granite with sqft calculation
    # extra_sqft = 50 (total sqft), rate_per_sqft = 100
    # Expected: 50 × 100 = 5000
    
    invoice_data = {
        "customer_id": customer_id,
        "line_items": [{
            "product_type": "granite",
            "location": "Kitchen Counter",
            "tile_name": "Black Galaxy Granite",
            "size": "8ft x 4ft",
            "extra_sqft": 50.0,  # Total sqft input
            "rate_per_sqft": 100.0,  # Rate per sqft
            "discount_percent": 0
        }],
        "transport_charges": 0,
        "unloading_charges": 0
    }
    
    try:
        response = requests.post(f"{API_URL}/invoices", json=invoice_data)
        success = response.status_code == 200
        
        if success:
            invoice = response.json()
            line_item = invoice['line_items'][0]
            
            # Expected calculation: 50 × 100 = 5000
            expected_amount = 50.0 * 100.0
            actual_amount = line_item['amount_before_discount']
            
            calc_correct = abs(actual_amount - expected_amount) < 0.01
            
            print_test_result("Granite Sqft Calculation", calc_correct)
            print(f"    Input: extra_sqft={line_item.get('extra_sqft', 'N/A')}, rate_per_sqft={line_item.get('rate_per_sqft', 'N/A')}")
            print(f"    Expected: {expected_amount}")
            print(f"    Actual: {actual_amount}")
            print(f"    Total Sqft: {line_item.get('total_sqft', 'N/A')}")
            
            # Cleanup
            invoice_id = invoice['invoice_id'].replace(' ', '%20').replace('/', '%2F')
            requests.delete(f"{API_URL}/invoices/{invoice_id}")
            
            return calc_correct
        else:
            print_test_result("Granite Sqft Calculation", False, f"API Error: {response.status_code}")
            print(f"    Response: {response.text}")
            return False
            
    except Exception as e:
        print_test_result("Granite Sqft Calculation", False, f"Error: {str(e)}")
        return False

def test_tile_pieces_calculation(customer_id):
    """Test Tile Pieces calculation - NOW uses pieces method"""
    print_separator("TEST TILE PIECES CALCULATION (PIECES-BASED)")
    
    # Test data: Tile Pieces with pieces calculation
    # quantity = 10, rate_per_piece = 250
    # Expected: 10 × 250 = 2500
    
    invoice_data = {
        "customer_id": customer_id,
        "line_items": [{
            "product_type": "tile_pieces",
            "location": "Bathroom Wall",
            "tile_name": "Ceramic Border Tiles",
            "size": "300x300mm",
            "quantity": 10,  # Number of pieces
            "rate_per_piece": 250.0,  # Rate per piece
            "discount_percent": 0
        }],
        "transport_charges": 0,
        "unloading_charges": 0
    }
    
    try:
        response = requests.post(f"{API_URL}/invoices", json=invoice_data)
        success = response.status_code == 200
        
        if success:
            invoice = response.json()
            line_item = invoice['line_items'][0]
            
            # Expected calculation: 10 × 250 = 2500
            expected_amount = 10 * 250.0
            actual_amount = line_item['amount_before_discount']
            
            calc_correct = abs(actual_amount - expected_amount) < 0.01
            
            print_test_result("Tile Pieces Calculation", calc_correct)
            print(f"    Input: quantity={line_item.get('quantity', 'N/A')}, rate_per_piece={line_item.get('rate_per_piece', 'N/A')}")
            print(f"    Expected: {expected_amount}")
            print(f"    Actual: {actual_amount}")
            print(f"    Total Sqft: {line_item.get('total_sqft', 'N/A')} (should be 0 or minimal for pieces)")
            
            # Cleanup
            invoice_id = invoice['invoice_id'].replace(' ', '%20').replace('/', '%2F')
            requests.delete(f"{API_URL}/invoices/{invoice_id}")
            
            return calc_correct
        else:
            print_test_result("Tile Pieces Calculation", False, f"API Error: {response.status_code}")
            print(f"    Response: {response.text}")
            return False
            
    except Exception as e:
        print_test_result("Tile Pieces Calculation", False, f"Error: {str(e)}")
        return False

def test_tiles_box_unchanged(customer_id):
    """Test Tiles Box calculation - should remain unchanged"""
    print_separator("TEST TILES BOX CALCULATION (UNCHANGED)")
    
    # Test data: Tiles Box calculation should remain the same
    # (box_qty × coverage + extra_sqft) × rate_per_sqft
    # (5 × 20 + 10) × 50 = 110 × 50 = 5500
    
    invoice_data = {
        "customer_id": customer_id,
        "line_items": [{
            "product_type": "tiles_box",
            "location": "Living Room",
            "tile_name": "Vitrified Floor Tiles",
            "size": "600x600mm",
            "box_qty": 5,
            "coverage": 20.0,
            "extra_sqft": 10.0,
            "rate_per_sqft": 50.0,
            "discount_percent": 0
        }],
        "transport_charges": 0,
        "unloading_charges": 0
    }
    
    try:
        response = requests.post(f"{API_URL}/invoices", json=invoice_data)
        success = response.status_code == 200
        
        if success:
            invoice = response.json()
            line_item = invoice['line_items'][0]
            
            # Expected calculation: (5 × 20 + 10) × 50 = 5500
            expected_total_sqft = (5 * 20.0) + 10.0  # 110
            expected_amount = expected_total_sqft * 50.0  # 5500
            actual_amount = line_item['amount_before_discount']
            
            calc_correct = abs(actual_amount - expected_amount) < 0.01
            
            print_test_result("Tiles Box Calculation (Unchanged)", calc_correct)
            print(f"    Input: box_qty={line_item.get('box_qty', 'N/A')}, coverage={line_item.get('coverage', 'N/A')}, extra_sqft={line_item.get('extra_sqft', 'N/A')}, rate_per_sqft={line_item.get('rate_per_sqft', 'N/A')}")
            print(f"    Expected Total Sqft: {expected_total_sqft}")
            print(f"    Actual Total Sqft: {line_item.get('total_sqft', 'N/A')}")
            print(f"    Expected Amount: {expected_amount}")
            print(f"    Actual Amount: {actual_amount}")
            
            # Cleanup
            invoice_id = invoice['invoice_id'].replace(' ', '%20').replace('/', '%2F')
            requests.delete(f"{API_URL}/invoices/{invoice_id}")
            
            return calc_correct
        else:
            print_test_result("Tiles Box Calculation", False, f"API Error: {response.status_code}")
            print(f"    Response: {response.text}")
            return False
            
    except Exception as e:
        print_test_result("Tiles Box Calculation", False, f"Error: {str(e)}")
        return False

def cleanup_customer(customer_id):
    """Clean up test customer"""
    try:
        response = requests.delete(f"{API_URL}/customers/{customer_id}")
        success = response.status_code == 200
        print_test_result("Cleanup Test Customer", success)
        return success
    except Exception as e:
        print_test_result("Cleanup Test Customer", False, f"Error: {str(e)}")
        return False

def main():
    """Run all backend tests for swapped calculations"""
    print("Backend Testing: Swapped Calculation Methods")
    print(f"API URL: {API_URL}")
    
    results = {
        'health_check': False,
        'granite_sqft': False,
        'tile_pieces': False,
        'tiles_box_unchanged': False
    }
    
    # 1. Health check
    results['health_check'] = test_health_check()
    
    if not results['health_check']:
        print("\n❌ API not accessible. Stopping tests.")
        return results
    
    # 2. Create test customer
    customer = create_test_customer()
    if not customer:
        print("\n❌ Failed to create test customer. Stopping tests.")
        return results
    
    customer_id = customer['customer_id']
    
    try:
        # 3. Test swapped calculations
        results['granite_sqft'] = test_granite_sqft_calculation(customer_id)
        results['tile_pieces'] = test_tile_pieces_calculation(customer_id)
        results['tiles_box_unchanged'] = test_tiles_box_unchanged(customer_id)
        
    finally:
        # 4. Cleanup
        print_separator("CLEANUP")
        cleanup_customer(customer_id)
    
    # 5. Summary
    print_separator("TEST SUMMARY")
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests PASSED! Swapped calculations working correctly.")
    else:
        print("⚠️  Some tests FAILED. Please check the calculation logic.")
    
    return results

if __name__ == "__main__":
    main()