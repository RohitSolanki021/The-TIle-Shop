#!/usr/bin/env python3

"""
Backend Test Suite for Tile Shop API - GST Calculation Verification
Testing GST calculation on TOTAL amount (subtotal + transport + unloading)
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://granite-tile-swap.preview.emergentagent.com/api"

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        
    def add_pass(self, test_name):
        self.passed += 1
        print(f"✅ PASS: {test_name}")
        
    def add_fail(self, test_name, error):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"❌ FAIL: {test_name} - {error}")
        
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY: {self.passed}/{total} tests passed")
        if self.errors:
            print("\nFAILED TESTS:")
            for error in self.errors:
                print(f"  • {error}")
        print(f"{'='*60}")
        return len(self.errors) == 0

def test_api_health():
    """Test basic API connectivity"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if response.status_code == 200:
            return True, "API is accessible"
        else:
            return False, f"Health check failed with status {response.status_code}"
    except Exception as e:
        return False, f"Health check failed: {str(e)}"

def create_test_customer():
    """Create a test customer for GST calculation testing"""
    customer_data = {
        "name": "GST Test Customer",
        "phone": "9876543210",
        "address": "123 Test Street, GST City, Test State - 123456",
        "gstin": "27AAAA0000A1Z5"
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/customers", json=customer_data, timeout=10)
        if response.status_code == 200:
            customer = response.json()
            return True, customer['customer_id'], "Customer created successfully"
        else:
            return False, None, f"Customer creation failed: {response.status_code} - {response.text}"
    except Exception as e:
        return False, None, f"Customer creation error: {str(e)}"

def create_gst_test_invoice(customer_id):
    """
    Create invoice with exact GST test scenario:
    - Line item: ₹10,000
    - Transport: ₹1,000
    - Unloading: ₹500
    - GST: 18%
    
    Expected:
    - Amount before GST: ₹11,500
    - GST: ₹2,070
    - Grand Total: ₹13,570
    """
    invoice_data = {
        "customer_id": customer_id,
        "transport_charges": 1000.0,
        "unloading_charges": 500.0,
        "gst_percent": 18.0,
        "line_items": [
            {
                "product_type": "granite",
                "location": "Main Hall",
                "tile_name": "Premium Black Granite",
                "extra_sqft": 50.0,  # Used as total sqft for granite
                "rate_per_sqft": 200.0,  # 50 * 200 = 10,000
                "discount_percent": 0.0
            }
        ],
        "amount_paid": 0.0,
        "status": "Draft"
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/invoices", json=invoice_data, timeout=10)
        if response.status_code == 200:
            invoice = response.json()
            return True, invoice, "Invoice created successfully"
        else:
            return False, None, f"Invoice creation failed: {response.status_code} - {response.text}"
    except Exception as e:
        return False, None, f"Invoice creation error: {str(e)}"

def verify_gst_calculation(invoice):
    """Verify GST calculation is correct"""
    errors = []
    
    # Expected values
    expected_subtotal = 10000.0
    expected_transport = 1000.0
    expected_unloading = 500.0
    expected_amount_before_gst = 11500.0
    expected_gst = 2070.0  # 11500 * 0.18
    expected_grand_total = 13570.0
    
    # Check subtotal
    if abs(invoice['subtotal'] - expected_subtotal) > 0.01:
        errors.append(f"Subtotal mismatch: expected {expected_subtotal}, got {invoice['subtotal']}")
    
    # Check transport charges
    if abs(invoice['transport_charges'] - expected_transport) > 0.01:
        errors.append(f"Transport charges mismatch: expected {expected_transport}, got {invoice['transport_charges']}")
    
    # Check unloading charges
    if abs(invoice['unloading_charges'] - expected_unloading) > 0.01:
        errors.append(f"Unloading charges mismatch: expected {expected_unloading}, got {invoice['unloading_charges']}")
    
    # Check GST calculation - THIS IS THE CRITICAL TEST
    if abs(invoice['gst_amount'] - expected_gst) > 0.01:
        errors.append(f"GST amount mismatch: expected {expected_gst}, got {invoice['gst_amount']}")
    
    # Check grand total
    if abs(invoice['grand_total'] - expected_grand_total) > 0.01:
        errors.append(f"Grand total mismatch: expected {expected_grand_total}, got {invoice['grand_total']}")
    
    # Verify calculation formula
    calculated_amount_before_gst = invoice['subtotal'] + invoice['transport_charges'] + invoice['unloading_charges']
    if abs(calculated_amount_before_gst - expected_amount_before_gst) > 0.01:
        errors.append(f"Amount before GST calculation error: expected {expected_amount_before_gst}, got {calculated_amount_before_gst}")
    
    return len(errors) == 0, errors

def run_gst_calculation_tests():
    """Main test runner for GST calculation"""
    result = TestResult()
    
    print("=" * 60)
    print("BACKEND GST CALCULATION TEST SUITE")
    print("=" * 60)
    print(f"Testing against: {BACKEND_URL}")
    print(f"Test Scenario: GST on TOTAL amount (subtotal + transport + unloading)")
    print(f"Expected: ₹10,000 + ₹1,000 + ₹500 = ₹11,500 × 18% = ₹2,070 GST")
    print("=" * 60)
    
    # Test 1: API Health Check
    print("\n1. Testing API connectivity...")
    success, message = test_api_health()
    if success:
        result.add_pass("API Health Check")
    else:
        result.add_fail("API Health Check", message)
        return result.summary()
    
    # Test 2: Create Customer
    print("\n2. Creating test customer...")
    success, customer_id, message = create_test_customer()
    if success:
        result.add_pass("Customer Creation")
        print(f"   Customer ID: {customer_id}")
    else:
        result.add_fail("Customer Creation", message)
        return result.summary()
    
    # Test 3: Create Invoice with GST scenario
    print("\n3. Creating invoice with GST test scenario...")
    success, invoice, message = create_gst_test_invoice(customer_id)
    if success:
        result.add_pass("Invoice Creation")
        print(f"   Invoice ID: {invoice['invoice_id']}")
        print(f"   Subtotal: ₹{invoice['subtotal']}")
        print(f"   Transport: ₹{invoice['transport_charges']}")
        print(f"   Unloading: ₹{invoice['unloading_charges']}")
        print(f"   GST Amount: ₹{invoice['gst_amount']}")
        print(f"   Grand Total: ₹{invoice['grand_total']}")
    else:
        result.add_fail("Invoice Creation", message)
        return result.summary()
    
    # Test 4: Verify GST Calculation
    print("\n4. Verifying GST calculation...")
    success, errors = verify_gst_calculation(invoice)
    if success:
        result.add_pass("GST Calculation Verification")
        print("   ✅ GST is correctly calculated on TOTAL amount")
        print("   ✅ Amount before GST = Subtotal + Transport + Unloading")
        print("   ✅ GST = Amount before GST × GST%")
        print("   ✅ Grand Total = Amount before GST + GST")
    else:
        result.add_fail("GST Calculation Verification", "; ".join(errors))
        for error in errors:
            print(f"   ❌ {error}")
    
    # Test 5: Test Additional Edge Cases
    print("\n5. Testing additional GST scenarios...")
    
    # Test with 0% GST
    print("   Testing 0% GST scenario...")
    invoice_data_zero_gst = {
        "customer_id": customer_id,
        "transport_charges": 500.0,
        "unloading_charges": 300.0,
        "gst_percent": 0.0,
        "line_items": [
            {
                "product_type": "granite",
                "location": "Test Location",
                "tile_name": "Test Granite",
                "extra_sqft": 25.0,
                "rate_per_sqft": 200.0,
                "discount_percent": 0.0
            }
        ],
        "amount_paid": 0.0
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/invoices", json=invoice_data_zero_gst, timeout=10)
        if response.status_code == 200:
            zero_gst_invoice = response.json()
            expected_total_zero = 5000.0 + 500.0 + 300.0  # No GST
            if abs(zero_gst_invoice['grand_total'] - expected_total_zero) < 0.01 and zero_gst_invoice['gst_amount'] == 0:
                result.add_pass("Zero GST Calculation")
                print("   ✅ 0% GST correctly handled")
            else:
                result.add_fail("Zero GST Calculation", f"Expected total {expected_total_zero}, got {zero_gst_invoice['grand_total']}")
        else:
            result.add_fail("Zero GST Invoice Creation", f"Status {response.status_code}")
    except Exception as e:
        result.add_fail("Zero GST Test", str(e))
    
    return result.summary()

if __name__ == "__main__":
    success = run_gst_calculation_tests()
    sys.exit(0 if success else 1)