#!/usr/bin/env python3
"""
Backend DELETE Functionality Testing for The Tile Shop
Testing all delete endpoints (tiles, customers, invoices) and WhatsApp share preparation.
"""

import requests
import json
import sys
import time
import urllib.parse
from datetime import datetime

# Backend URL from frontend/.env
BASE_URL = "http://localhost:8001/api"

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
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            result.pass_test("API Health Check - /health endpoint accessible")
        else:
            result.fail_test(f"API Health Check - Unexpected status {response.status_code}")
    except Exception as e:
        result.fail_test(f"API Health Check - Connection failed: {str(e)}")
    
    return result

def test_tiles_delete_functionality():
    """Test Tiles DELETE functionality with soft delete"""
    result = TestResult()
    
    print("🔧 Testing Tiles Delete Functionality...")
    
    try:
        # Step 1: Create a test tile
        tile_data = {
            "size": "600x600mm",
            "coverage": 3.0,
            "box_packing": 4
        }
        
        response = requests.post(f"{BASE_URL}/tiles", json=tile_data)
        if response.status_code == 200:
            tile = response.json()
            tile_id = tile['tile_id']
            result.pass_test(f"Test tile created: {tile['size']} (ID: {tile_id})")
        else:
            result.fail_test(f"Failed to create test tile: {response.status_code}")
            return result
        
        # Step 2: Verify tile exists in GET /tiles list
        response = requests.get(f"{BASE_URL}/tiles")
        if response.status_code == 200:
            tiles = response.json()
            tile_exists = any(t['tile_id'] == tile_id for t in tiles)
            if tile_exists:
                result.pass_test("Tile appears in GET /tiles list before deletion")
            else:
                result.fail_test("Tile not found in GET /tiles list before deletion")
        else:
            result.fail_test(f"Failed to get tiles list: {response.status_code}")
        
        # Step 3: Test DELETE endpoint
        response = requests.delete(f"{BASE_URL}/tiles/{tile_id}")
        if response.status_code == 200:
            result.pass_test("DELETE /tiles/{tile_id} returned success")
        else:
            result.fail_test(f"DELETE /tiles/{tile_id} failed: {response.status_code}")
        
        # Step 4: Verify tile no longer appears in GET /tiles list (soft delete)
        response = requests.get(f"{BASE_URL}/tiles")
        if response.status_code == 200:
            tiles = response.json()
            tile_exists = any(t['tile_id'] == tile_id for t in tiles)
            if not tile_exists:
                result.pass_test("Tile no longer appears in GET /tiles list (soft deleted)")
            else:
                result.fail_test("Tile still appears in GET /tiles list after deletion")
        else:
            result.fail_test(f"Failed to get tiles list after deletion: {response.status_code}")
        
        # Step 5: Test delete non-existent tile
        response = requests.delete(f"{BASE_URL}/tiles/non-existent-id")
        if response.status_code == 404:
            result.pass_test("DELETE returns 404 for non-existent tile")
        else:
            result.fail_test(f"DELETE should return 404 for non-existent tile, got {response.status_code}")
        
    except Exception as e:
        result.fail_test(f"Tiles delete test failed: {str(e)}")
    
    return result

def test_customers_delete_functionality():
    """Test Customers DELETE functionality with soft delete"""
    result = TestResult()
    
    print("👥 Testing Customers Delete Functionality...")
    
    try:
        # Step 1: Create a test customer
        customer_data = {
            "name": "Test Customer",
            "phone": "9876543210",
            "address": "Test Address",
            "gstin": "06TEST1234F1Z5"
        }
        
        response = requests.post(f"{BASE_URL}/customers", json=customer_data)
        if response.status_code == 200:
            customer = response.json()
            customer_id = customer['customer_id']
            result.pass_test(f"Test customer created: {customer['name']} (ID: {customer_id})")
        else:
            result.fail_test(f"Failed to create test customer: {response.status_code}")
            return result
        
        # Step 2: Verify customer exists in GET /customers list
        response = requests.get(f"{BASE_URL}/customers")
        if response.status_code == 200:
            customers = response.json()
            customer_exists = any(c['customer_id'] == customer_id for c in customers)
            if customer_exists:
                result.pass_test("Customer appears in GET /customers list before deletion")
            else:
                result.fail_test("Customer not found in GET /customers list before deletion")
        else:
            result.fail_test(f"Failed to get customers list: {response.status_code}")
        
        # Step 3: Test DELETE endpoint
        response = requests.delete(f"{BASE_URL}/customers/{customer_id}")
        if response.status_code == 200:
            result.pass_test("DELETE /customers/{customer_id} returned success")
        else:
            result.fail_test(f"DELETE /customers/{customer_id} failed: {response.status_code}")
        
        # Step 4: Verify customer no longer appears in GET /customers list (soft delete)
        response = requests.get(f"{BASE_URL}/customers")
        if response.status_code == 200:
            customers = response.json()
            customer_exists = any(c['customer_id'] == customer_id for c in customers)
            if not customer_exists:
                result.pass_test("Customer no longer appears in GET /customers list (soft deleted)")
            else:
                result.fail_test("Customer still appears in GET /customers list after deletion")
        else:
            result.fail_test(f"Failed to get customers list after deletion: {response.status_code}")
        
        # Step 5: Test delete non-existent customer
        response = requests.delete(f"{BASE_URL}/customers/non-existent-id")
        if response.status_code == 404:
            result.pass_test("DELETE returns 404 for non-existent customer")
        else:
            result.fail_test(f"DELETE should return 404 for non-existent customer, got {response.status_code}")
        
    except Exception as e:
        result.fail_test(f"Customers delete test failed: {str(e)}")
    
    return result

def test_invoices_delete_functionality():
    """Test Invoices DELETE functionality with soft delete and customer pending balance recalculation"""
    result = TestResult()
    
    print("📄 Testing Invoices Delete Functionality...")
    
    try:
        # Step 1: Create a test customer first
        customer_data = {
            "name": "Test Invoice Customer",
            "phone": "9876543210",
            "address": "Test Address for Invoice",
            "gstin": "06TESTINV1234F1Z5"
        }
        
        response = requests.post(f"{BASE_URL}/customers", json=customer_data)
        if response.status_code == 200:
            customer = response.json()
            customer_id = customer['customer_id']
            result.pass_test(f"Test customer created for invoice: {customer['name']}")
        else:
            result.fail_test(f"Failed to create customer for invoice test: {response.status_code}")
            return result
        
        # Step 2: Create a test tile for the invoice
        tile_data = {
            "size": "600x600mm", 
            "coverage": 3.0,
            "box_packing": 4
        }
        
        response = requests.post(f"{BASE_URL}/tiles", json=tile_data)
        if response.status_code == 200:
            tile = response.json()
            result.pass_test(f"Test tile created for invoice: {tile['size']}")
        else:
            result.fail_test(f"Failed to create tile for invoice test: {response.status_code}")
        
        # Step 3: Create a test invoice
        line_items = [
            {
                "tile_name": "Test Tile for Invoice",
                "size": "600x600mm",
                "location": "LIVING ROOM",
                "rate_per_box": 1000.0,
                "rate_per_sqft": 50.0,
                "box_qty": 5,
                "discount_percent": 0.0,
                "coverage": 3.0,
                "box_packing": 4
            }
        ]
        
        invoice_data = {
            "customer_id": customer_id,
            "line_items": line_items,
            "transport_charges": 500.0,
            "unloading_charges": 200.0,
            "gst_percent": 18.0
        }
        
        response = requests.post(f"{BASE_URL}/invoices", json=invoice_data)
        if response.status_code == 200:
            invoice = response.json()
            invoice_id = invoice['invoice_id']
            result.pass_test(f"Test invoice created: {invoice_id}")
        else:
            result.fail_test(f"Failed to create test invoice: {response.status_code}")
            return result
        
        # Step 4: Verify invoice exists in GET /invoices list
        response = requests.get(f"{BASE_URL}/invoices")
        if response.status_code == 200:
            invoices = response.json()
            invoice_exists = any(i['invoice_id'] == invoice_id for i in invoices)
            if invoice_exists:
                result.pass_test("Invoice appears in GET /invoices list before deletion")
            else:
                result.fail_test("Invoice not found in GET /invoices list before deletion")
        else:
            result.fail_test(f"Failed to get invoices list: {response.status_code}")
        
        # Step 5: Check customer's total_pending before deletion
        response = requests.get(f"{BASE_URL}/customers/{customer_id}")
        if response.status_code == 200:
            customer_before = response.json()
            pending_before = customer_before.get('total_pending', 0)
            result.pass_test(f"Customer pending balance before deletion: ₹{pending_before:.2f}")
        
        # Step 6: Test DELETE endpoint (URL-encoded invoice ID)
        encoded_invoice_id = urllib.parse.quote(invoice_id, safe='')
        response = requests.delete(f"{BASE_URL}/invoices/{encoded_invoice_id}")
        if response.status_code == 200:
            result.pass_test(f"DELETE /invoices/{invoice_id} returned success")
        else:
            result.fail_test(f"DELETE /invoices/{invoice_id} failed: {response.status_code}")
        
        # Step 7: Verify invoice no longer appears in GET /invoices list (soft delete)
        response = requests.get(f"{BASE_URL}/invoices")
        if response.status_code == 200:
            invoices = response.json()
            invoice_exists = any(i['invoice_id'] == invoice_id for i in invoices)
            if not invoice_exists:
                result.pass_test("Invoice no longer appears in GET /invoices list (soft deleted)")
            else:
                result.fail_test("Invoice still appears in GET /invoices list after deletion")
        else:
            result.fail_test(f"Failed to get invoices list after deletion: {response.status_code}")
        
        # Step 8: Verify customer's total_pending is recalculated after invoice deletion
        response = requests.get(f"{BASE_URL}/customers/{customer_id}")
        if response.status_code == 200:
            customer_after = response.json()
            pending_after = customer_after.get('total_pending', 0)
            result.pass_test(f"Customer pending balance after deletion: ₹{pending_after:.2f}")
            
            if pending_after == 0:
                result.pass_test("Customer's total_pending correctly recalculated to 0 after invoice deletion")
            else:
                result.fail_test(f"Customer's total_pending not properly recalculated (should be 0, got {pending_after})")
        
        # Step 9: Test delete non-existent invoice
        response = requests.delete(f"{BASE_URL}/invoices/NON-EXISTENT-INVOICE")
        if response.status_code == 404:
            result.pass_test("DELETE returns 404 for non-existent invoice")
        else:
            result.fail_test(f"DELETE should return 404 for non-existent invoice, got {response.status_code}")
        
    except Exception as e:
        result.fail_test(f"Invoices delete test failed: {str(e)}")
    
    return result

def test_whatsapp_pdf_generation():
    """Test PDF generation for WhatsApp share functionality"""
    result = TestResult()
    
    print("📱 Testing WhatsApp PDF Generation...")
    
    try:
        # Step 1: Create customer and invoice for PDF testing
        customer_data = {
            "name": "WhatsApp Test Customer",
            "phone": "9876543210",
            "address": "WhatsApp Test Address",
            "gstin": "06WHATSAPP1234F1Z5"
        }
        
        response = requests.post(f"{BASE_URL}/customers", json=customer_data)
        if response.status_code == 200:
            customer = response.json()
            customer_id = customer['customer_id']
            result.pass_test(f"WhatsApp test customer created: {customer['name']}")
        else:
            result.fail_test(f"Failed to create WhatsApp test customer: {response.status_code}")
            return result
        
        # Step 2: Create invoice for PDF generation
        line_items = [
            {
                "tile_name": "WhatsApp Share Test Tile",
                "size": "600x600mm",
                "location": "TEST ROOM",
                "rate_per_box": 800.0,
                "rate_per_sqft": 40.0,
                "box_qty": 3,
                "discount_percent": 5.0,
                "coverage": 3.0,
                "box_packing": 4
            }
        ]
        
        invoice_data = {
            "customer_id": customer_id,
            "line_items": line_items,
            "transport_charges": 300.0,
            "unloading_charges": 150.0,
            "gst_percent": 18.0,
            "reference_name": "WhatsApp Test Reference"
        }
        
        response = requests.post(f"{BASE_URL}/invoices", json=invoice_data)
        if response.status_code == 200:
            invoice = response.json()
            invoice_id = invoice['invoice_id']
            result.pass_test(f"WhatsApp test invoice created: {invoice_id}")
        else:
            result.fail_test(f"Failed to create WhatsApp test invoice: {response.status_code}")
            return result
        
        # Step 3: Test PDF generation endpoint
        encoded_invoice_id = urllib.parse.quote(invoice_id, safe='')
        pdf_url = f"{BASE_URL}/invoices/{encoded_invoice_id}/pdf"
        
        print(f"📋 Testing PDF URL: {pdf_url}")
        
        try:
            pdf_response = requests.get(pdf_url, timeout=30)
            
            if pdf_response.status_code == 200:
                result.pass_test("PDF generation endpoint returned success")
                
                # Check Content-Type header
                content_type = pdf_response.headers.get('Content-Type', '')
                if content_type == 'application/pdf':
                    result.pass_test("PDF Content-Type header is correct")
                else:
                    result.fail_test(f"PDF Content-Type incorrect: {content_type}")
                
                # Check PDF file size
                pdf_size = len(pdf_response.content)
                print(f"📊 PDF Size: {pdf_size:,} bytes ({pdf_size/1024:.1f} KB)")
                
                if pdf_size > 100000:  # >100KB
                    result.pass_test(f"PDF size {pdf_size/1024:.1f} KB is reasonable (>100KB)")
                else:
                    result.fail_test(f"PDF size {pdf_size/1024:.1f} KB seems too small (<100KB)")
                
                # Save PDF for inspection
                with open("/tmp/whatsapp_test_invoice.pdf", "wb") as f:
                    f.write(pdf_response.content)
                result.pass_test("PDF saved to /tmp/whatsapp_test_invoice.pdf")
                
            else:
                result.fail_test(f"PDF generation failed: {pdf_response.status_code}")
                print(f"Error response: {pdf_response.text}")
                
        except requests.exceptions.Timeout:
            result.fail_test("PDF generation request timed out (>30 seconds)")
        except Exception as e:
            result.fail_test(f"PDF generation request failed: {str(e)}")
        
        # Step 4: Test public PDF endpoint (for WhatsApp sharing)
        public_pdf_url = f"{BASE_URL}/public/invoices/{encoded_invoice_id}/pdf"
        print(f"📋 Testing Public PDF URL: {public_pdf_url}")
        
        try:
            public_pdf_response = requests.get(public_pdf_url, timeout=30)
            
            if public_pdf_response.status_code == 200:
                result.pass_test("Public PDF generation endpoint returned success")
                
                # Check that it returns the same PDF content
                if len(public_pdf_response.content) > 100000:
                    result.pass_test("Public PDF endpoint returns valid PDF content")
                else:
                    result.fail_test("Public PDF endpoint returns invalid content")
                    
            else:
                result.fail_test(f"Public PDF generation failed: {public_pdf_response.status_code}")
                
        except requests.exceptions.Timeout:
            result.fail_test("Public PDF generation request timed out (>30 seconds)")
        except Exception as e:
            result.fail_test(f"Public PDF generation request failed: {str(e)}")
        
    except Exception as e:
        result.fail_test(f"WhatsApp PDF generation test failed: {str(e)}")
    
    return result

def main():
    """Main testing function"""
    print("🚀 Starting DELETE Functionality and WhatsApp Share Testing...")
    print(f"🌐 Backend URL: {BASE_URL}")
    print("="*70)
    
    all_results = []
    
    # Test 1: API Health
    print("\n1️⃣ API Health Check")
    health_result = test_api_health()
    all_results.append(health_result)
    
    if health_result.failed > 0:
        print("❌ API health check failed. Stopping tests.")
        return False
    
    # Test 2: Tiles Delete Functionality
    print("\n2️⃣ Tiles Delete Functionality")
    tiles_result = test_tiles_delete_functionality()
    all_results.append(tiles_result)
    
    # Test 3: Customers Delete Functionality
    print("\n3️⃣ Customers Delete Functionality")
    customers_result = test_customers_delete_functionality()
    all_results.append(customers_result)
    
    # Test 4: Invoices Delete Functionality
    print("\n4️⃣ Invoices Delete Functionality")
    invoices_result = test_invoices_delete_functionality()
    all_results.append(invoices_result)
    
    # Test 5: WhatsApp PDF Generation
    print("\n5️⃣ WhatsApp PDF Generation")
    whatsapp_result = test_whatsapp_pdf_generation()
    all_results.append(whatsapp_result)
    
    # Final Summary
    print("\n" + "="*70)
    print("🏁 FINAL TEST SUMMARY")
    print("="*70)
    
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)
    total_tests = total_passed + total_failed
    
    print(f"✅ PASSED: {total_passed}/{total_tests}")
    print(f"❌ FAILED: {total_failed}/{total_tests}")
    
    if total_failed > 0:
        print(f"\n🚨 FAILED TEST DETAILS:")
        test_names = ["API Health", "Tiles Delete", "Customers Delete", "Invoices Delete", "WhatsApp PDF"]
        for i, result in enumerate(all_results):
            if result.errors:
                print(f"\n{test_names[i]}:")
                for error in result.errors:
                    print(f"  ❌ {error}")
    
    success = total_failed == 0
    
    if success:
        print(f"\n🎉 ALL TESTS PASSED! Delete functionality and WhatsApp share preparation working correctly.")
    else:
        print(f"\n⚠️  SOME TESTS FAILED. Review issues above.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)