#!/usr/bin/env python3
"""
Backend API Testing for Tile Shop Invoicing System
Testing focus: Invoice creation with TTS format, PDF generation, and price verification
"""

import requests
import json
import os
import sys
from urllib.parse import quote_plus
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://8fee7af5-8b36-4847-8c09-b747b3cd7bd6.preview.emergentagent.com/api"

def test_api_health():
    """Test basic API connectivity"""
    print("🔍 Testing API Health...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data}")
            print("✅ API Health: PASS")
            return True
        else:
            print(f"❌ API Health: FAIL - Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API Health: FAIL - {e}")
        return False

def test_create_customer():
    """Create a test customer for invoice testing"""
    print("\n🔍 Creating test customer...")
    
    customer_data = {
        "name": "Rajesh Kumar Builders",
        "phone": "9876543210",
        "address": "Shop No. 45, Construction Market, Sector 12, New Delhi - 110001",
        "gstin": "07AABCU9603R1ZM"
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/customers", json=customer_data, timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            customer = response.json()
            print(f"   Customer ID: {customer['customer_id']}")
            print(f"   Customer Name: {customer['name']}")
            print("✅ Customer Creation: PASS")
            return customer['customer_id']
        else:
            print(f"❌ Customer Creation: FAIL - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Customer Creation: FAIL - {e}")
        return None

def test_create_tile():
    """Create a test tile for invoice line items"""
    print("\n🔍 Creating test tile...")
    
    tile_data = {
        "size": "600x600mm",
        "coverage": 3.6,  # sqft per box
        "box_packing": 4   # tiles per box
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/tiles", json=tile_data, timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            tile = response.json()
            print(f"   Tile ID: {tile['tile_id']}")
            print(f"   Size: {tile['size']}")
            print(f"   Coverage: {tile['coverage']} sqft/box")
            print("✅ Tile Creation: PASS")
            return tile['size']
        else:
            print(f"❌ Tile Creation: FAIL - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Tile Creation: FAIL - {e}")
        return None

def test_create_invoice_with_new_format(customer_id, tile_size):
    """Test 1: Create Invoice with TTS format and verify calculations"""
    print("\n🔍 TEST 1: Creating invoice with TTS format...")
    
    invoice_data = {
        "customer_id": customer_id,
        "line_items": [
            {
                "location": "Living Room",
                "tile_name": "Premium Marble Finish",
                "size": tile_size,
                "box_qty": 15,
                "extra_sqft": 5.5,
                "rate_per_sqft": 95,  # Will auto-calculate rate_per_box
                "discount_percent": 8,
                "coverage": 3.6,
                "box_packing": 4
            },
            {
                "location": "Kitchen",
                "tile_name": "Anti-Slip Floor Tiles", 
                "size": tile_size,
                "box_qty": 8,
                "extra_sqft": 2.0,
                "rate_per_box": 280,  # Will auto-calculate rate_per_sqft
                "discount_percent": 5,
                "coverage": 3.6,
                "box_packing": 4
            }
        ],
        "transport_charges": 1200.0,
        "unloading_charges": 800.0,
        "gst_percent": 18.0,
        "reference_name": "Project Sunshine Apartments",
        "overall_remarks": "Please handle tiles with care during transport. Installation to start next Monday."
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/invoices", json=invoice_data, timeout=15)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            invoice = response.json()
            
            # Test Invoice ID format
            invoice_id = invoice['invoice_id']
            print(f"   Invoice ID: {invoice_id}")
            
            # Verify TTS / XXX / YYYY-YY format
            import re
            pattern = r'^TTS / \d{3} / \d{4}-\d{2}$'
            if re.match(pattern, invoice_id):
                print("✅ Invoice ID Format: CORRECT (TTS / XXX / YYYY-YY)")
            else:
                print(f"❌ Invoice ID Format: INCORRECT - Expected TTS / XXX / YYYY-YY, got {invoice_id}")
                return None
            
            # Verify Price Calculations
            print(f"\n   📊 Price Verification:")
            
            # Check line items calculations
            for i, item in enumerate(invoice['line_items']):
                print(f"   Item {i+1} ({item['location']}):")
                
                # Calculate expected values
                total_sqft = (item['box_qty'] * item['coverage']) + item['extra_sqft']
                amount_before_discount = total_sqft * item['rate_per_sqft']
                discount_amount = amount_before_discount * (item['discount_percent'] / 100)
                final_amount = amount_before_discount - discount_amount
                
                print(f"     Total SqFt: {item['total_sqft']} (expected: {total_sqft})")
                print(f"     Rate/SqFt: ₹{item['rate_per_sqft']}")
                print(f"     Rate/Box: ₹{item['rate_per_box']}")
                print(f"     Amount Before Discount: ₹{item['amount_before_discount']}")
                print(f"     Discount ({item['discount_percent']}%): ₹{item['discount_amount']}")
                print(f"     Final Amount: ₹{item['final_amount']}")
                
                # Verify calculations
                if abs(item['total_sqft'] - total_sqft) < 0.01:
                    print(f"     ✅ Total SqFt calculation: CORRECT")
                else:
                    print(f"     ❌ Total SqFt calculation: INCORRECT")
                
                if abs(item['final_amount'] - final_amount) < 0.01:
                    print(f"     ✅ Final amount calculation: CORRECT")
                else:
                    print(f"     ❌ Final amount calculation: INCORRECT")
            
            # Check invoice totals
            print(f"\n   💰 Invoice Totals:")
            print(f"     Subtotal: ₹{invoice['subtotal']}")
            print(f"     Transport: ₹{invoice['transport_charges']}")
            print(f"     Unloading: ₹{invoice['unloading_charges']}")
            print(f"     GST (18%): ₹{invoice['gst_amount']}")
            print(f"     Grand Total: ₹{invoice['grand_total']}")
            
            # Verify GST calculation
            expected_gst = invoice['subtotal'] * 0.18
            if abs(invoice['gst_amount'] - expected_gst) < 0.01:
                print(f"     ✅ GST calculation: CORRECT")
            else:
                print(f"     ❌ GST calculation: INCORRECT (expected: ₹{expected_gst})")
            
            # Verify Grand Total
            expected_grand_total = invoice['subtotal'] + invoice['transport_charges'] + invoice['unloading_charges'] + invoice['gst_amount']
            if abs(invoice['grand_total'] - expected_grand_total) < 0.01:
                print(f"     ✅ Grand Total calculation: CORRECT")
            else:
                print(f"     ❌ Grand Total calculation: INCORRECT (expected: ₹{expected_grand_total})")
            
            print("✅ Invoice Creation with TTS Format: PASS")
            return invoice_id
            
        else:
            print(f"❌ Invoice Creation: FAIL - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Invoice Creation: FAIL - {e}")
        return None

def test_pdf_generation(invoice_id):
    """Test 2: PDF Generation with URL encoding and size verification"""
    print(f"\n🔍 TEST 2: PDF Generation for invoice {invoice_id}...")
    
    # URL encode the invoice ID for the request
    encoded_invoice_id = quote_plus(invoice_id)
    pdf_url = f"{BACKEND_URL}/invoices/{encoded_invoice_id}/pdf"
    
    print(f"   PDF URL: {pdf_url}")
    
    try:
        response = requests.get(pdf_url, timeout=30)
        print(f"   Status Code: {response.status_code}")
        print(f"   Content Type: {response.headers.get('content-type')}")
        
        if response.status_code == 200:
            # Verify content type
            if response.headers.get('content-type') == 'application/pdf':
                print("✅ PDF Content Type: CORRECT")
            else:
                print(f"❌ PDF Content Type: INCORRECT - {response.headers.get('content-type')}")
                return False
            
            # Check PDF size (should be ~590KB+ for template overlay)
            pdf_size = len(response.content)
            pdf_size_kb = pdf_size / 1024
            
            print(f"   PDF Size: {pdf_size} bytes ({pdf_size_kb:.1f} KB)")
            
            # Template overlay method should produce larger files (~590KB+)
            if pdf_size_kb >= 570:  # Allow some margin
                print("✅ PDF Size: CORRECT (Template overlay confirmed - 570KB+)")
            else:
                print(f"❌ PDF Size: Too small ({pdf_size_kb:.1f} KB) - May indicate layout recreation instead of template overlay")
            
            # Verify PDF headers
            pdf_header = response.content[:8]
            if pdf_header.startswith(b'%PDF-'):
                print("✅ PDF Header: VALID")
            else:
                print("❌ PDF Header: INVALID")
                return False
            
            # Save PDF for manual inspection (optional)
            safe_filename = invoice_id.replace(" / ", "-").replace("/", "-")
            pdf_path = f"/app/test_{safe_filename}.pdf"
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            print(f"   PDF saved to: {pdf_path}")
            
            print("✅ PDF Generation: PASS")
            return True
            
        else:
            print(f"❌ PDF Generation: FAIL - Status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ PDF Generation: FAIL - {e}")
        return False

def test_invoice_retrieval(invoice_id):
    """Test 3: Verify invoice retrieval and data integrity"""
    print(f"\n🔍 TEST 3: Invoice Retrieval Verification...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/invoices/{quote_plus(invoice_id)}", timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            invoice = response.json()
            
            print(f"   Retrieved Invoice ID: {invoice['invoice_id']}")
            print(f"   Customer: {invoice['customer_name']}")
            print(f"   Line Items Count: {len(invoice['line_items'])}")
            print(f"   Grand Total: ₹{invoice['grand_total']}")
            
            # Verify data integrity
            if invoice['invoice_id'] == invoice_id:
                print("✅ Invoice ID Match: CORRECT")
            else:
                print("❌ Invoice ID Match: INCORRECT")
                return False
            
            if len(invoice['line_items']) == 2:  # We created 2 line items
                print("✅ Line Items Count: CORRECT")
            else:
                print("❌ Line Items Count: INCORRECT")
                return False
            
            print("✅ Invoice Retrieval: PASS")
            return True
            
        else:
            print(f"❌ Invoice Retrieval: FAIL - Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Invoice Retrieval: FAIL - {e}")
        return False

def main():
    """Main testing function"""
    print("=" * 70)
    print("🧪 TILE SHOP INVOICING API - BACKEND TESTING")
    print("=" * 70)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {}
    
    # Test 1: API Health
    results['api_health'] = test_api_health()
    
    if not results['api_health']:
        print("\n❌ CRITICAL: API not accessible. Stopping tests.")
        return
    
    # Test 2: Create test data
    customer_id = test_create_customer()
    if not customer_id:
        print("\n❌ CRITICAL: Cannot create customer. Stopping tests.")
        return
    
    tile_size = test_create_tile()
    if not tile_size:
        print("\n❌ CRITICAL: Cannot create tile. Stopping tests.")
        return
    
    # Test 3: Create Invoice with TTS format
    invoice_id = test_create_invoice_with_new_format(customer_id, tile_size)
    results['invoice_creation'] = invoice_id is not None
    
    if not invoice_id:
        print("\n❌ CRITICAL: Cannot create invoice. Stopping PDF tests.")
        return
    
    # Test 4: PDF Generation
    results['pdf_generation'] = test_pdf_generation(invoice_id)
    
    # Test 5: Invoice Retrieval
    results['invoice_retrieval'] = test_invoice_retrieval(invoice_id)
    
    # Summary
    print("\n" + "=" * 70)
    print("📋 TEST SUMMARY")
    print("=" * 70)
    
    total_tests = len([k for k in results.keys() if k != 'api_health'])
    passed_tests = len([k for k, v in results.items() if v and k != 'api_health'])
    
    for test_name, result in results.items():
        if test_name == 'api_health':
            continue
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nTests Passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        print("⚠️  SOME TESTS FAILED!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)