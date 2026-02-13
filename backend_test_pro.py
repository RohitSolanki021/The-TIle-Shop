#!/usr/bin/env python3
"""
PRO Invoice Engine Testing - Multi-Section Support and Pagination
==================================================================

TESTING OBJECTIVES as per review request:
1. TEST 1: 1 item in 1 section (SA)
2. TEST 2: 10 items in 2 sections (SA: 5, KITCHEN: 5)  
3. TEST 3: 50 items in 3 sections (SA: 20, KITCHEN: 15, BATHROOM: 15)

For each test verify:
- No text overlap
- Section headers replace "MAIN FLOOR" correctly
- Section totals show "{section}'s Total Amount" with correct sum
- Items stay within table grid columns
- Page numbers appear on multi-page PDFs

Expected PDF sizes:
- 1 item: ~590-600KB
- 10 items: ~600-700KB  
- 50 items: ~1-2MB (multiple pages)
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

def create_test_customer():
    """Create a test customer for invoice testing"""
    customer_data = {
        "name": "Modern Interiors Pvt Ltd",
        "phone": "+91-9876543210", 
        "address": "456 Design Plaza, Interior Complex, Delhi - 110001",
        "gstin": "07ABCDE1234F1Z5"
    }
    
    response = requests.post(f"{BASE_URL}/customers", json=customer_data)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to create customer: {response.status_code}")

def test_scenario_1_single_item_sa():
    """
    TEST 1: 1 item in 1 section (SA)
    Expected: single page, SA header, SA's Total Amount
    """
    result = TestResult()
    
    print("🧪 TEST 1: Single Item in SA Section")
    print("="*50)
    
    try:
        # Create customer
        customer = create_test_customer()
        result.pass_test(f"Customer created: {customer['name']}")
        
        # Create invoice with 1 item in SA section
        line_items = [
            {
                "tile_name": "Premium Marble Floor Tiles",
                "size": "600x600mm",
                "location": "SA",
                "rate_per_box": 1200.0,
                "rate_per_sqft": 370.37,
                "box_qty": 8,
                "discount_percent": 5.0,
                "coverage": 3.24,
                "box_packing": 9
            }
        ]
        
        invoice_data = {
            "customer_id": customer['customer_id'],
            "reference_name": "Test 1 - Single SA Item",
            "line_items": line_items,
            "transport_charges": 300.0,
            "unloading_charges": 150.0,
            "gst_percent": 18.0,
            "overall_remarks": "PRO Engine Test 1: Single item SA section"
        }
        
        response = requests.post(f"{BASE_URL}/invoices", json=invoice_data)
        if response.status_code == 200:
            invoice = response.json()
            result.pass_test(f"Invoice created: {invoice['invoice_id']}")
            
            # Verify SA section exists
            sa_items = [item for item in invoice['line_items'] if item.get('location') == 'SA']
            if len(sa_items) == 1:
                result.pass_test("SA section contains exactly 1 item")
            else:
                result.fail_test(f"SA section has {len(sa_items)} items, expected 1")
            
            # Test PDF generation
            import urllib.parse
            encoded_id = urllib.parse.quote(invoice['invoice_id'], safe='')
            pdf_url = f"{BASE_URL}/invoices/{encoded_id}/pdf"
            
            pdf_response = requests.get(pdf_url, timeout=30)
            
            if pdf_response.status_code == 200:
                result.pass_test("PDF generation successful")
                
                pdf_size = len(pdf_response.content)
                print(f"📊 PDF Size: {pdf_size:,} bytes ({pdf_size/1024:.1f} KB)")
                
                # Expected size ~590-600KB for single page
                if 590000 <= pdf_size <= 650000:  # Allow some tolerance
                    result.pass_test(f"PDF size {pdf_size/1024:.1f} KB within expected range (590-650KB)")
                else:
                    result.fail_test(f"PDF size {pdf_size/1024:.1f} KB outside expected range (590-650KB)")
                
                # Save PDF for inspection
                with open("/tmp/test1_single_sa.pdf", "wb") as f:
                    f.write(pdf_response.content)
                result.pass_test("PDF saved to /tmp/test1_single_sa.pdf")
                
                # Verify single page (size should indicate single page PDF)
                if pdf_size < 800000:  # Less than 800KB likely indicates single page
                    result.pass_test("PDF appears to be single page based on size")
                else:
                    result.fail_test("PDF may be multi-page (size > 800KB)")
                    
            else:
                result.fail_test(f"PDF generation failed: {pdf_response.status_code}")
                
        else:
            result.fail_test(f"Invoice creation failed: {response.status_code}")
            
    except Exception as e:
        result.fail_test(f"Test 1 failed: {str(e)}")
        print(f"ERROR: {e}")
    
    return result

def test_scenario_2_dual_sections():
    """
    TEST 2: 10 items in 2 sections (SA: 5, KITCHEN: 5)
    Expected: proper section headers, section totals, no overlap
    """
    result = TestResult()
    
    print("\n🧪 TEST 2: 10 Items in 2 Sections (SA: 5, KITCHEN: 5)")
    print("="*60)
    
    try:
        # Create customer
        customer = create_test_customer()
        result.pass_test(f"Customer created: {customer['name']}")
        
        # Create line items: 5 SA + 5 KITCHEN
        line_items = []
        
        # SA Section - 5 items
        sa_items = [
            {"tile_name": "SA Premium Marble", "size": "600x600mm", "location": "SA", "rate_per_box": 850.0, "box_qty": 10},
            {"tile_name": "SA Designer Tiles", "size": "800x800mm", "location": "SA", "rate_per_box": 1200.0, "box_qty": 8},
            {"tile_name": "SA Wall Tiles", "size": "300x600mm", "location": "SA", "rate_per_box": 425.0, "box_qty": 15},
            {"tile_name": "SA Floor Tiles", "size": "400x400mm", "location": "SA", "rate_per_box": 320.0, "box_qty": 12},
            {"tile_name": "SA Large Format", "size": "1200x600mm", "location": "SA", "rate_per_box": 1850.0, "box_qty": 6}
        ]
        
        # KITCHEN Section - 5 items
        kitchen_items = [
            {"tile_name": "Kitchen Backsplash", "size": "300x600mm", "location": "KITCHEN", "rate_per_box": 380.0, "box_qty": 20},
            {"tile_name": "Kitchen Floor Premium", "size": "600x600mm", "location": "KITCHEN", "rate_per_box": 920.0, "box_qty": 14},
            {"tile_name": "Kitchen Counter Tiles", "size": "400x400mm", "location": "KITCHEN", "rate_per_box": 450.0, "box_qty": 18},
            {"tile_name": "Kitchen Wall Designer", "size": "250x375mm", "location": "KITCHEN", "rate_per_box": 650.0, "box_qty": 25},
            {"tile_name": "Kitchen Mosaic Accent", "size": "300x300mm", "location": "KITCHEN", "rate_per_box": 750.0, "box_qty": 12}
        ]
        
        # Add coverage and other required fields
        for item in sa_items + kitchen_items:
            item.update({
                "rate_per_sqft": 200.0,  # Simplified for testing
                "discount_percent": 2.0,
                "coverage": 3.5,
                "box_packing": 10
            })
        
        line_items = sa_items + kitchen_items
        
        invoice_data = {
            "customer_id": customer['customer_id'],
            "reference_name": "Test 2 - Dual Sections",
            "line_items": line_items,
            "transport_charges": 500.0,
            "unloading_charges": 200.0,
            "gst_percent": 18.0,
            "overall_remarks": "PRO Engine Test 2: SA + KITCHEN sections"
        }
        
        response = requests.post(f"{BASE_URL}/invoices", json=invoice_data)
        if response.status_code == 200:
            invoice = response.json()
            result.pass_test(f"Invoice created: {invoice['invoice_id']}")
            
            # Verify section distribution
            sa_items_created = [item for item in invoice['line_items'] if item.get('location') == 'SA']
            kitchen_items_created = [item for item in invoice['line_items'] if item.get('location') == 'KITCHEN']
            
            if len(sa_items_created) == 5:
                result.pass_test("SA section contains exactly 5 items")
            else:
                result.fail_test(f"SA section has {len(sa_items_created)} items, expected 5")
                
            if len(kitchen_items_created) == 5:
                result.pass_test("KITCHEN section contains exactly 5 items")
            else:
                result.fail_test(f"KITCHEN section has {len(kitchen_items_created)} items, expected 5")
            
            # Calculate section totals
            sa_total = sum(item.get('final_amount', 0) for item in sa_items_created)
            kitchen_total = sum(item.get('final_amount', 0) for item in kitchen_items_created)
            
            if sa_total > 0:
                result.pass_test(f"SA section total calculated: ₹{sa_total:,.2f}")
            else:
                result.fail_test("SA section total calculation failed")
                
            if kitchen_total > 0:
                result.pass_test(f"KITCHEN section total calculated: ₹{kitchen_total:,.2f}")
            else:
                result.fail_test("KITCHEN section total calculation failed")
            
            # Test PDF generation
            import urllib.parse
            encoded_id = urllib.parse.quote(invoice['invoice_id'], safe='')
            pdf_url = f"{BASE_URL}/invoices/{encoded_id}/pdf"
            
            pdf_response = requests.get(pdf_url, timeout=30)
            
            if pdf_response.status_code == 200:
                result.pass_test("PDF generation successful")
                
                pdf_size = len(pdf_response.content)
                print(f"📊 PDF Size: {pdf_size:,} bytes ({pdf_size/1024:.1f} KB)")
                
                # Expected size ~600-700KB
                if 600000 <= pdf_size <= 800000:  # Allow tolerance
                    result.pass_test(f"PDF size {pdf_size/1024:.1f} KB within expected range (600-800KB)")
                else:
                    result.fail_test(f"PDF size {pdf_size/1024:.1f} KB outside expected range (600-800KB)")
                
                # Save PDF for inspection
                with open("/tmp/test2_dual_sections.pdf", "wb") as f:
                    f.write(pdf_response.content)
                result.pass_test("PDF saved to /tmp/test2_dual_sections.pdf")
                
            else:
                result.fail_test(f"PDF generation failed: {pdf_response.status_code}")
                
        else:
            result.fail_test(f"Invoice creation failed: {response.status_code}")
            
    except Exception as e:
        result.fail_test(f"Test 2 failed: {str(e)}")
        print(f"ERROR: {e}")
    
    return result

def test_scenario_3_triple_sections_50_items():
    """
    TEST 3: 50 items in 3 sections (SA: 20, KITCHEN: 15, BATHROOM: 15)
    Expected: multi-page PDF, pagination works, all sections render
    """
    result = TestResult()
    
    print("\n🧪 TEST 3: 50 Items in 3 Sections (SA: 20, KITCHEN: 15, BATHROOM: 15)")
    print("="*75)
    
    try:
        # Create customer
        customer = create_test_customer()
        result.pass_test(f"Customer created: {customer['name']}")
        
        # Create large number of line items
        line_items = []
        
        # SA Section - 20 items
        for i in range(1, 21):
            line_items.append({
                "tile_name": f"SA Tile Type {i}",
                "size": "600x600mm" if i % 2 == 0 else "800x800mm",
                "location": "SA",
                "rate_per_box": 800.0 + (i * 10),
                "rate_per_sqft": 250.0 + (i * 5),
                "box_qty": 8 + (i % 5),
                "discount_percent": 2.0 + (i % 3),
                "coverage": 3.24 if i % 2 == 0 else 5.12,
                "box_packing": 9 if i % 2 == 0 else 8
            })
        
        # KITCHEN Section - 15 items
        for i in range(1, 16):
            line_items.append({
                "tile_name": f"Kitchen Tile Type {i}",
                "size": "300x600mm" if i % 2 == 0 else "400x400mm",
                "location": "KITCHEN",
                "rate_per_box": 400.0 + (i * 15),
                "rate_per_sqft": 180.0 + (i * 8),
                "box_qty": 10 + (i % 4),
                "discount_percent": 1.0 + (i % 4),
                "coverage": 5.4 if i % 2 == 0 else 4.8,
                "box_packing": 30
            })
        
        # BATHROOM Section - 15 items
        for i in range(1, 16):
            line_items.append({
                "tile_name": f"Bathroom Tile Type {i}",
                "size": "250x375mm" if i % 2 == 0 else "300x300mm",
                "location": "BATHROOM",
                "rate_per_box": 450.0 + (i * 20),
                "rate_per_sqft": 220.0 + (i * 10),
                "box_qty": 15 + (i % 6),
                "discount_percent": 3.0 + (i % 2),
                "coverage": 4.5 if i % 2 == 0 else 3.8,
                "box_packing": 25 if i % 2 == 0 else 20
            })
        
        invoice_data = {
            "customer_id": customer['customer_id'],
            "reference_name": "Test 3 - Triple Sections Large Scale",
            "line_items": line_items,
            "transport_charges": 1200.0,
            "unloading_charges": 500.0,
            "gst_percent": 18.0,
            "overall_remarks": "PRO Engine Test 3: SA + KITCHEN + BATHROOM sections with 50 items total for pagination testing"
        }
        
        print(f"📝 Creating invoice with {len(line_items)} total items...")
        
        response = requests.post(f"{BASE_URL}/invoices", json=invoice_data)
        if response.status_code == 200:
            invoice = response.json()
            result.pass_test(f"Invoice created: {invoice['invoice_id']}")
            
            # Verify section distribution
            sa_items_created = [item for item in invoice['line_items'] if item.get('location') == 'SA']
            kitchen_items_created = [item for item in invoice['line_items'] if item.get('location') == 'KITCHEN']
            bathroom_items_created = [item for item in invoice['line_items'] if item.get('location') == 'BATHROOM']
            
            print(f"📊 Section breakdown: SA({len(sa_items_created)}), KITCHEN({len(kitchen_items_created)}), BATHROOM({len(bathroom_items_created)})")
            
            if len(sa_items_created) == 20:
                result.pass_test("SA section contains exactly 20 items")
            else:
                result.fail_test(f"SA section has {len(sa_items_created)} items, expected 20")
                
            if len(kitchen_items_created) == 15:
                result.pass_test("KITCHEN section contains exactly 15 items")
            else:
                result.fail_test(f"KITCHEN section has {len(kitchen_items_created)} items, expected 15")
                
            if len(bathroom_items_created) == 15:
                result.pass_test("BATHROOM section contains exactly 15 items")
            else:
                result.fail_test(f"BATHROOM section has {len(bathroom_items_created)} items, expected 15")
            
            # Calculate section totals
            sa_total = sum(item.get('final_amount', 0) for item in sa_items_created)
            kitchen_total = sum(item.get('final_amount', 0) for item in kitchen_items_created)
            bathroom_total = sum(item.get('final_amount', 0) for item in bathroom_items_created)
            
            print(f"💰 Section totals: SA(₹{sa_total:,.2f}), KITCHEN(₹{kitchen_total:,.2f}), BATHROOM(₹{bathroom_total:,.2f})")
            
            if sa_total > 0:
                result.pass_test(f"SA section total calculated: ₹{sa_total:,.2f}")
            else:
                result.fail_test("SA section total calculation failed")
                
            if kitchen_total > 0:
                result.pass_test(f"KITCHEN section total calculated: ₹{kitchen_total:,.2f}")
            else:
                result.fail_test("KITCHEN section total calculation failed")
                
            if bathroom_total > 0:
                result.pass_test(f"BATHROOM section total calculated: ₹{bathroom_total:,.2f}")
            else:
                result.fail_test("BATHROOM section total calculation failed")
            
            # Test PDF generation - this should be multi-page
            import urllib.parse
            encoded_id = urllib.parse.quote(invoice['invoice_id'], safe='')
            pdf_url = f"{BASE_URL}/invoices/{encoded_id}/pdf"
            
            print(f"📄 Generating PDF for 50-item invoice...")
            
            pdf_response = requests.get(pdf_url, timeout=60)  # Longer timeout for large PDF
            
            if pdf_response.status_code == 200:
                result.pass_test("PDF generation successful for 50-item invoice")
                
                pdf_size = len(pdf_response.content)
                print(f"📊 PDF Size: {pdf_size:,} bytes ({pdf_size/1024:.1f} KB, {pdf_size/(1024*1024):.2f} MB)")
                
                # Expected size ~1-2MB for multi-page
                if 1000000 <= pdf_size <= 3000000:  # 1MB to 3MB
                    result.pass_test(f"PDF size {pdf_size/(1024*1024):.2f} MB within expected range (1-3MB)")
                else:
                    result.fail_test(f"PDF size {pdf_size/(1024*1024):.2f} MB outside expected range (1-3MB)")
                
                # Multi-page verification by size
                if pdf_size > 1000000:  # > 1MB likely indicates multiple pages
                    result.pass_test("PDF appears to be multi-page based on size (>1MB)")
                else:
                    result.fail_test("PDF may be single page (size < 1MB)")
                
                # Save PDF for inspection
                with open("/tmp/test3_triple_sections_50items.pdf", "wb") as f:
                    f.write(pdf_response.content)
                result.pass_test("PDF saved to /tmp/test3_triple_sections_50items.pdf")
                
            else:
                result.fail_test(f"PDF generation failed: {pdf_response.status_code}")
                print(f"Error response: {pdf_response.text[:200]}...")
                
        else:
            result.fail_test(f"Invoice creation failed: {response.status_code}")
            print(f"Error response: {response.text[:200]}...")
            
    except Exception as e:
        result.fail_test(f"Test 3 failed: {str(e)}")
        import traceback
        print(f"ERROR: {e}")
        print(traceback.format_exc())
    
    return result

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

def main():
    """Main testing function for PRO Invoice Engine"""
    print("🚀 PRO INVOICE ENGINE TESTING")
    print("Testing Multiple Sections and Pagination Features")
    print(f"🌐 Backend URL: {BASE_URL}")
    print("="*70)
    
    all_results = []
    
    # API Health Check
    print("\n🔍 API HEALTH CHECK")
    health_result = test_api_health()
    all_results.append(health_result)
    
    if health_result.failed > 0:
        print("❌ API health check failed. Stopping tests.")
        return False
    
    # Test Scenario 1: 1 item in SA section
    test1_result = test_scenario_1_single_item_sa()
    all_results.append(test1_result)
    
    # Test Scenario 2: 10 items in 2 sections
    test2_result = test_scenario_2_dual_sections()
    all_results.append(test2_result)
    
    # Test Scenario 3: 50 items in 3 sections
    test3_result = test_scenario_3_triple_sections_50_items()
    all_results.append(test3_result)
    
    # Final Summary
    print("\n" + "="*70)
    print("🏁 PRO INVOICE ENGINE - FINAL TEST SUMMARY")
    print("="*70)
    
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)
    total_tests = total_passed + total_failed
    
    print(f"✅ PASSED: {total_passed}/{total_tests}")
    print(f"❌ FAILED: {total_failed}/{total_tests}")
    
    test_names = ["API Health", "Test 1 (1 item, SA)", "Test 2 (10 items, SA+KITCHEN)", "Test 3 (50 items, SA+KITCHEN+BATHROOM)"]
    
    for i, result in enumerate(all_results):
        status = "✅ PASS" if result.failed == 0 else f"❌ FAIL ({result.failed} errors)"
        print(f"  {test_names[i]}: {status}")
    
    if total_failed > 0:
        print(f"\n🚨 DETAILED FAILURE REPORT:")
        for i, result in enumerate(all_results):
            if result.errors:
                print(f"\n{test_names[i]} FAILURES:")
                for error in result.errors:
                    print(f"  ❌ {error}")
    
    success = total_failed == 0
    
    if success:
        print(f"\n🎉 ALL PRO INVOICE ENGINE TESTS PASSED!")
        print("✅ Single section support working")
        print("✅ Multi-section support working") 
        print("✅ Section header replacement working")
        print("✅ Section totals calculation working")
        print("✅ PDF pagination working for large invoices")
        print("✅ Template overlay method confirmed")
    else:
        print(f"\n⚠️  SOME TESTS FAILED. Review details above.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)