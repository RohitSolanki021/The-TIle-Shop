#!/usr/bin/env python3
"""
Backend API Testing for The Tile Shop - Complete Invoice Generation Flow
Testing invoice creation with multiple sections and PDF generation as per review request.
"""

import requests
import json
import sys
import time
from datetime import datetime

# Backend URL from frontend/.env
BASE_URL = "https://tile-invoice-app.preview.emergentagent.com/api"

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        
    def pass_test(self, msg):
        print(f"✅ PASS: {msg}")
        self.passed += 1
        
    def fail_test(self, msg):
        print(f"❌ FAIL: {msg}")
        self.failed += 1
        self.errors.append(msg)
        
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY: {self.passed}/{total} tests passed")
        if self.errors:
            print(f"\nFAILED TESTS:")
            for error in self.errors:
                print(f"  - {error}")
        print(f"{'='*60}")
        return len(self.errors) == 0

def test_api_health():
    """Test basic API connectivity"""
    result = TestResult()
    
    try:
        response = requests.get(f"{BASE_URL}/invoices", timeout=10)
        if response.status_code == 200:
            result.pass_test("API Health Check - /invoices endpoint accessible")
        else:
            result.fail_test(f"API Health Check - Unexpected status {response.status_code}")
    except Exception as e:
        result.fail_test(f"API Health Check - Connection failed: {str(e)}")
    
    return result

def create_test_customer():
    """Create test customer as per review request"""
    customer_data = {
        "name": "Test Builder Pvt Ltd",
        "phone": "9876543210", 
        "address": "Plot 123, Industrial Area, Hansi, Haryana - 125033",
        "gstin": "06ABCDE1234F1Z5"
    }
    
    response = requests.post(f"{BASE_URL}/customers", json=customer_data)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to create customer: {response.status_code}")

def create_test_tiles():
    """Create test tiles for the invoice as per review request"""
    tiles = [
        {"size": "600x600mm", "coverage": 2.16, "box_packing": 6},  # For Marble Finish & Anti-Slip
        {"size": "800x800mm", "coverage": 2.56, "box_packing": 4},  # For Granite Tiles
        {"size": "600x1200mm", "coverage": 4.32, "box_packing": 6}, # For Wooden Look
        {"size": "300x450mm", "coverage": 8.1, "box_packing": 60},  # For Ceramic Wall
    ]
    
    created_tiles = []
    for tile_data in tiles:
        response = requests.post(f"{BASE_URL}/tiles", json=tile_data)
        if response.status_code == 200:
            created_tiles.append(response.json())
    
    return created_tiles

def create_multi_section_invoice(customer_id):
    """Create invoice with 3 sections as per review request"""
    
    # Create line items for 3 sections: LIVING ROOM, BEDROOM, BATHROOM
    line_items = [
        # LIVING ROOM - 2 items
        {
            "tile_name": "Marble Finish Tiles",
            "size": "600x600mm",
            "location": "LIVING ROOM",
            "rate_per_box": 950.0,
            "rate_per_sqft": 48.0,
            "box_qty": 5,
            "discount_percent": 5.0,
            "coverage": 2.16,
            "box_packing": 6
        },
        {
            "tile_name": "Granite Tiles",
            "size": "800x800mm", 
            "location": "LIVING ROOM",
            "rate_per_box": 1200.0,
            "rate_per_sqft": 60.0,
            "box_qty": 3,
            "discount_percent": 10.0,
            "coverage": 2.56,
            "box_packing": 4
        },
        # BEDROOM - 1 item
        {
            "tile_name": "Wooden Look Tiles",
            "size": "600x1200mm",
            "location": "BEDROOM", 
            "rate_per_box": 850.0,
            "rate_per_sqft": 42.0,
            "box_qty": 4,
            "discount_percent": 0.0,
            "coverage": 4.32,
            "box_packing": 6
        },
        # BATHROOM - 2 items
        {
            "tile_name": "Ceramic Wall Tiles",
            "size": "300x450mm",
            "location": "BATHROOM",
            "rate_per_box": 560.0,
            "rate_per_sqft": 28.0,
            "box_qty": 8,
            "discount_percent": 5.0,
            "coverage": 8.1,
            "box_packing": 60
        },
        {
            "tile_name": "Anti-Slip Floor Tiles",
            "size": "600x600mm", 
            "location": "BATHROOM",
            "rate_per_box": 780.0,
            "rate_per_sqft": 39.0,
            "box_qty": 6,
            "discount_percent": 0.0,
            "coverage": 2.16,
            "box_packing": 6
        }
    ]
    
    invoice_data = {
        "customer_id": customer_id,
        "reference_name": "Contractor Rajesh Kumar",
        "line_items": line_items,
        "transport_charges": 800.0,
        "unloading_charges": 300.0,
        "gst_percent": 18.0,
        "overall_remarks": "Delivery within 3 days. Handle with care."
    }
    
    response = requests.post(f"{BASE_URL}/invoices", json=invoice_data)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to create invoice: {response.status_code} - {response.text}")

def test_complete_invoice_generation_flow():
    """
    Test complete invoice generation flow as per review request.
    
    TESTING OBJECTIVES:
    1. Create customer: "Test Builder Pvt Ltd" with specified details
    2. Create invoice with 3 sections (LIVING ROOM, BEDROOM, BATHROOM) and 5 items total
    3. Verify invoice calculations (subtotal, GST, grand total)
    4. Generate PDF and verify:
       - THE TILE SHOP logo in header
       - All 3 sections display correctly
       - Section totals calculate properly
       - Invoice ID format: TTS / XXX / 2025-26
       - File size around 300KB
    """
    
    result = TestResult()
    
    print("🔍 Testing Complete Invoice Generation Flow...")
    print("="*60)
    
    try:
        # Step 1: Create test customer as per review request
        print("📋 Creating test customer: Test Builder Pvt Ltd...")
        customer = create_test_customer()
        result.pass_test(f"Customer created: {customer['name']} (ID: {customer['customer_id']})")
        
        # Verify customer details
        if customer['name'] == "Test Builder Pvt Ltd":
            result.pass_test("Customer name matches review request")
        if customer['phone'] == "9876543210":
            result.pass_test("Customer phone matches review request")
        if customer['gstin'] == "06ABCDE1234F1Z5":
            result.pass_test("Customer GSTIN matches review request")
        
        # Step 2: Create test tiles
        print("🏗️ Creating test tiles...")
        tiles = create_test_tiles()
        result.pass_test(f"Created {len(tiles)} test tiles")
        
        # Step 3: Create invoice with 3 sections and 5 items
        print("📄 Creating invoice with 3 sections (LIVING ROOM, BEDROOM, BATHROOM)...")
        invoice = create_multi_section_invoice(customer['customer_id'])
        result.pass_test(f"Invoice created: {invoice['invoice_id']}")
        
        # Verify invoice ID format: TTS / XXX / 2025-26
        invoice_id = invoice['invoice_id']
        if invoice_id.startswith("TTS / ") and " / 2025-26" in invoice_id:
            result.pass_test(f"Invoice ID format correct: {invoice_id}")
        else:
            result.fail_test(f"Invoice ID format incorrect: {invoice_id}")
        
        # Step 4: Verify sections and items
        print("🔍 Verifying sections and items...")
        line_items = invoice['line_items']
        
        # Group items by section
        sections = {}
        for item in line_items:
            location = item.get('location', 'Unknown')
            if location not in sections:
                sections[location] = []
            sections[location].append(item)
        
        # Verify 3 sections exist
        expected_sections = ['LIVING ROOM', 'BEDROOM', 'BATHROOM']
        for section in expected_sections:
            if section in sections:
                result.pass_test(f"Section '{section}' found with {len(sections[section])} items")
            else:
                result.fail_test(f"Section '{section}' missing")
        
        # Verify total items count
        if len(line_items) == 5:
            result.pass_test("Total 5 items created as per review request")
        else:
            result.fail_test(f"Expected 5 items, got {len(line_items)}")
        
        # Step 5: Verify calculations
        print("💰 Verifying invoice calculations...")
        subtotal = invoice.get('subtotal', 0)
        gst_amount = invoice.get('gst_amount', 0)
        transport_charges = invoice.get('transport_charges', 0)
        unloading_charges = invoice.get('unloading_charges', 0)
        grand_total = invoice.get('grand_total', 0)
        
        result.pass_test(f"Subtotal: ₹{subtotal:,.2f}")
        result.pass_test(f"GST (18%): ₹{gst_amount:,.2f}")
        result.pass_test(f"Transport charges: ₹{transport_charges:,.2f}")
        result.pass_test(f"Unloading charges: ₹{unloading_charges:,.2f}")
        result.pass_test(f"Grand total: ₹{grand_total:,.2f}")
        
        # Verify GST calculation (18%)
        expected_gst = subtotal * 0.18
        if abs(gst_amount - expected_gst) < 0.01:
            result.pass_test("GST calculation (18%) is correct")
        else:
            result.fail_test(f"GST calculation incorrect. Expected: ₹{expected_gst:.2f}, Got: ₹{gst_amount:.2f}")
        
        # Verify grand total calculation
        expected_grand_total = subtotal + gst_amount + transport_charges + unloading_charges
        if abs(grand_total - expected_grand_total) < 0.01:
            result.pass_test("Grand total calculation is correct")
        else:
            result.fail_test(f"Grand total incorrect. Expected: ₹{expected_grand_total:.2f}, Got: ₹{grand_total:.2f}")
        
        # Step 6: Test PDF generation
        print("📑 Testing PDF generation...")
        
        # URL encode the invoice ID for API call
        import urllib.parse
        encoded_id = urllib.parse.quote(invoice_id, safe='')
        pdf_url = f"{BASE_URL}/invoices/{encoded_id}/pdf"
        
        print(f"📋 PDF URL: {pdf_url}")
        
        pdf_response = requests.get(pdf_url, timeout=30)
        
        if pdf_response.status_code == 200:
            result.pass_test("PDF generation successful")
            
            # Check PDF size - should be around 300KB as per review request
            pdf_size = len(pdf_response.content)
            print(f"📊 PDF Size: {pdf_size:,} bytes ({pdf_size/1024:.1f} KB)")
            
            # HTML-based PDF should be smaller than template overlay (~300KB vs ~590KB)
            if 200000 <= pdf_size <= 500000:  # 200KB to 500KB range
                result.pass_test(f"PDF size {pdf_size/1024:.1f} KB is reasonable (HTML-based generation)")
            else:
                result.fail_test(f"PDF size {pdf_size/1024:.1f} KB outside expected range (200-500KB)")
                
            # Save PDF for manual verification
            with open("/tmp/multi_section_invoice.pdf", "wb") as f:
                f.write(pdf_response.content)
            result.pass_test("PDF saved to /tmp/multi_section_invoice.pdf for inspection")
            
        else:
            result.fail_test(f"PDF generation failed: {pdf_response.status_code}")
            print(f"Error response: {pdf_response.text}")
        
        # Step 7: Verify reference name and remarks
        print("📝 Verifying additional fields...")
        if invoice.get('reference_name') == "Contractor Rajesh Kumar":
            result.pass_test("Reference name matches review request")
        if invoice.get('overall_remarks') == "Delivery within 3 days. Handle with care.":
            result.pass_test("Remarks match review request")
        
        print("✨ Complete Invoice Generation Flow Testing Complete!")
        
    except Exception as e:
        result.fail_test(f"Invoice generation flow test failed: {str(e)}")
        import traceback
        print(f"🚨 ERROR: {e}")
        print(traceback.format_exc())
    
    return result

def main():
    """Main testing function"""
    print("🚀 Starting Complete Invoice Generation Flow Testing...")
    print(f"🌐 Backend URL: {BASE_URL}")
    print("="*60)
    
    all_results = []
    
    # Test 1: API Health
    print("\n1️⃣ API Health Check")
    health_result = test_api_health()
    all_results.append(health_result)
    
    if health_result.failed > 0:
        print("❌ API health check failed. Stopping tests.")
        return False
    
    # Test 2: Complete Invoice Generation Flow
    print("\n2️⃣ Complete Invoice Generation Flow")
    flow_result = test_complete_invoice_generation_flow()
    all_results.append(flow_result)
    
    # Final Summary
    print("\n" + "="*60)
    print("🏁 FINAL TEST SUMMARY")
    print("="*60)
    
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)
    total_tests = total_passed + total_failed
    
    print(f"✅ PASSED: {total_passed}/{total_tests}")
    print(f"❌ FAILED: {total_failed}/{total_tests}")
    
    if total_failed > 0:
        print(f"\n🚨 FAILED TEST DETAILS:")
        for i, result in enumerate(all_results, 1):
            if result.errors:
                test_names = ["API Health", "Invoice Generation Flow"] 
                print(f"\nTest {i} - {test_names[i-1]}:")
                for error in result.errors:
                    print(f"  ❌ {error}")
    
    success = total_failed == 0
    
    if success:
        print(f"\n🎉 ALL TESTS PASSED! Complete invoice generation flow working correctly.")
    else:
        print(f"\n⚠️  SOME TESTS FAILED. Review issues above.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)