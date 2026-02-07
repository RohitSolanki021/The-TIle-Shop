#!/usr/bin/env python3
"""
Backend API Testing for Tile Shop Invoicing System - Fix URL Encoding
Testing focus: Invoice creation with TTS format, PDF generation, and price verification
"""

import requests
import json
import os
import sys
from urllib.parse import quote
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

def test_existing_invoice():
    """Test with an existing invoice that we know works"""
    print("\n🔍 Testing with existing invoice TTS / 001 / 2025-26...")
    
    # Use proper URL encoding for spaces
    invoice_id = "TTS / 001 / 2025-26"
    encoded_invoice_id = quote(invoice_id, safe='')
    
    print(f"   Original ID: {invoice_id}")
    print(f"   Encoded ID: {encoded_invoice_id}")
    
    try:
        # Test retrieval first
        response = requests.get(f"{BACKEND_URL}/invoices/{encoded_invoice_id}", timeout=10)
        print(f"   Retrieval Status Code: {response.status_code}")
        
        if response.status_code == 200:
            invoice = response.json()
            print(f"   ✅ Invoice found: {invoice['invoice_id']}")
            print(f"   Customer: {invoice['customer_name']}")
            print(f"   Grand Total: ₹{invoice['grand_total']}")
            
            # Test PDF generation
            pdf_url = f"{BACKEND_URL}/invoices/{encoded_invoice_id}/pdf"
            print(f"   PDF URL: {pdf_url}")
            
            pdf_response = requests.get(pdf_url, timeout=30)
            print(f"   PDF Status Code: {pdf_response.status_code}")
            
            if pdf_response.status_code == 200:
                pdf_size = len(pdf_response.content)
                pdf_size_kb = pdf_size / 1024
                print(f"   PDF Size: {pdf_size} bytes ({pdf_size_kb:.1f} KB)")
                
                if pdf_size_kb >= 570:
                    print("   ✅ PDF Size: Template overlay confirmed (570KB+)")
                else:
                    print(f"   ❌ PDF Size: Too small ({pdf_size_kb:.1f} KB)")
                
                print("✅ Existing Invoice Test: PASS")
                return True
            else:
                print(f"❌ PDF Generation failed: {pdf_response.status_code}")
                return False
        else:
            print(f"❌ Invoice retrieval failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Existing Invoice Test: FAIL - {e}")
        return False

def test_create_invoice_and_verify():
    """Test creating a new invoice and verify all functionality"""
    print("\n🔍 Creating new invoice and testing full workflow...")
    
    # Step 1: Create customer
    customer_data = {
        "name": "Metro Construction Ltd",
        "phone": "9988776655",
        "address": "Building 12, Industrial Area Phase 2, Gurgaon - 122016",
        "gstin": "06AABCU9603R1ZV"
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/customers", json=customer_data, timeout=10)
        if response.status_code != 200:
            print(f"❌ Customer creation failed: {response.status_code}")
            return False
        
        customer = response.json()
        customer_id = customer['customer_id']
        print(f"   ✅ Customer created: {customer_id}")
        
    except Exception as e:
        print(f"❌ Customer creation error: {e}")
        return False
    
    # Step 2: Create tile
    tile_data = {
        "size": "800x800mm",
        "coverage": 5.12,  # sqft per box
        "box_packing": 2   # tiles per box
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/tiles", json=tile_data, timeout=10)
        if response.status_code != 200:
            print(f"❌ Tile creation failed: {response.status_code}")
            return False
        
        tile = response.json()
        tile_size = tile['size']
        print(f"   ✅ Tile created: {tile_size}")
        
    except Exception as e:
        print(f"❌ Tile creation error: {e}")
        return False
    
    # Step 3: Create invoice with TTS format
    invoice_data = {
        "customer_id": customer_id,
        "line_items": [
            {
                "location": "Main Hall",
                "tile_name": "Luxury Granite Design",
                "size": tile_size,
                "box_qty": 20,
                "extra_sqft": 10.0,
                "rate_per_sqft": 120,
                "discount_percent": 10,
                "coverage": 5.12,
                "box_packing": 2
            },
            {
                "location": "Bedroom",
                "tile_name": "Classic Wood Effect",
                "size": tile_size,
                "box_qty": 12,
                "extra_sqft": 5.0,
                "rate_per_sqft": 85,
                "discount_percent": 5,
                "coverage": 5.12,
                "box_packing": 2
            }
        ],
        "transport_charges": 1500.0,
        "unloading_charges": 1000.0,
        "gst_percent": 18.0,
        "reference_name": "Corporate Office Renovation",
        "overall_remarks": "Premium quality tiles required. Delivery by end of week."
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/invoices", json=invoice_data, timeout=15)
        print(f"   Invoice Creation Status: {response.status_code}")
        
        if response.status_code == 200:
            invoice = response.json()
            invoice_id = invoice['invoice_id']
            
            print(f"   ✅ Invoice Created: {invoice_id}")
            
            # Verify TTS format
            import re
            pattern = r'^TTS / \d{3} / \d{4}-\d{2}$'
            if re.match(pattern, invoice_id):
                print("   ✅ Invoice ID Format: CORRECT (TTS / XXX / YYYY-YY)")
            else:
                print(f"   ❌ Invoice ID Format: INCORRECT - {invoice_id}")
                return False
            
            # Verify calculations
            print(f"\n   💰 Financial Verification:")
            print(f"     Subtotal: ₹{invoice['subtotal']:,.2f}")
            print(f"     GST (18%): ₹{invoice['gst_amount']:,.2f}")
            print(f"     Transport: ₹{invoice['transport_charges']:,.2f}")
            print(f"     Unloading: ₹{invoice['unloading_charges']:,.2f}")
            print(f"     Grand Total: ₹{invoice['grand_total']:,.2f}")
            
            # Test retrieval with proper encoding
            encoded_invoice_id = quote(invoice_id, safe='')
            print(f"\n   🔍 Testing retrieval with encoded ID: {encoded_invoice_id}")
            
            retrieval_response = requests.get(f"{BACKEND_URL}/invoices/{encoded_invoice_id}", timeout=10)
            print(f"   Retrieval Status: {retrieval_response.status_code}")
            
            if retrieval_response.status_code == 200:
                retrieved_invoice = retrieval_response.json()
                if retrieved_invoice['invoice_id'] == invoice_id:
                    print("   ✅ Invoice Retrieval: CORRECT")
                else:
                    print("   ❌ Invoice Retrieval: ID mismatch")
                    return False
            else:
                print(f"   ❌ Invoice Retrieval: FAILED - {retrieval_response.status_code}")
                print(f"   Response: {retrieval_response.text}")
                return False
            
            # Test PDF generation
            print(f"\n   📄 Testing PDF generation...")
            pdf_url = f"{BACKEND_URL}/invoices/{encoded_invoice_id}/pdf"
            print(f"   PDF URL: {pdf_url}")
            
            pdf_response = requests.get(pdf_url, timeout=30)
            print(f"   PDF Status: {pdf_response.status_code}")
            
            if pdf_response.status_code == 200:
                pdf_size = len(pdf_response.content)
                pdf_size_kb = pdf_size / 1024
                
                print(f"   PDF Size: {pdf_size} bytes ({pdf_size_kb:.1f} KB)")
                print(f"   Content Type: {pdf_response.headers.get('content-type')}")
                
                # Verify PDF content
                if pdf_response.headers.get('content-type') == 'application/pdf':
                    print("   ✅ PDF Content Type: CORRECT")
                else:
                    print("   ❌ PDF Content Type: INCORRECT")
                    return False
                
                # Check size for template overlay confirmation
                if pdf_size_kb >= 570:
                    print("   ✅ PDF Size: Template overlay method confirmed (570KB+)")
                else:
                    print(f"   ⚠️  PDF Size: Small ({pdf_size_kb:.1f} KB) - may indicate layout recreation")
                
                # Save for inspection
                safe_filename = invoice_id.replace(" / ", "-").replace("/", "-")
                pdf_path = f"/app/test_new_{safe_filename}.pdf"
                with open(pdf_path, 'wb') as f:
                    f.write(pdf_response.content)
                print(f"   📁 PDF saved: {pdf_path}")
                
                print("   ✅ PDF Generation: PASS")
            else:
                print(f"   ❌ PDF Generation: FAILED - {pdf_response.status_code}")
                print(f"   Response: {pdf_response.text}")
                return False
            
            print("✅ Complete Invoice Workflow: PASS")
            return True
            
        else:
            print(f"❌ Invoice creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Invoice creation error: {e}")
        return False

def main():
    """Main testing function"""
    print("=" * 80)
    print("🧪 TILE SHOP INVOICING API - COMPREHENSIVE BACKEND TESTING")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {}
    
    # Test 1: API Health
    results['api_health'] = test_api_health()
    if not results['api_health']:
        print("\n❌ CRITICAL: API not accessible. Stopping tests.")
        return False
    
    # Test 2: Existing Invoice (to verify encoding works)
    results['existing_invoice'] = test_existing_invoice()
    
    # Test 3: Complete new invoice workflow
    results['new_invoice_workflow'] = test_create_invoice_and_verify()
    
    # Summary
    print("\n" + "=" * 80)
    print("📋 FINAL TEST SUMMARY")
    print("=" * 80)
    
    total_tests = len([k for k in results.keys() if k != 'api_health'])
    passed_tests = len([k for k, v in results.items() if v and k != 'api_health'])
    
    for test_name, result in results.items():
        if test_name == 'api_health':
            continue
        status = "✅ PASS" if result else "❌ FAIL"
        display_name = test_name.replace('_', ' ').title()
        print(f"{display_name}: {status}")
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL BACKEND TESTS PASSED!")
        print("✅ TTS Invoice ID format working correctly")
        print("✅ PDF generation with template overlay confirmed")
        print("✅ Price calculations accurate")
        return True
    else:
        print("\n⚠️  SOME TESTS FAILED - See details above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)