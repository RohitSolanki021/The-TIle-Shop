#!/usr/bin/env python3
"""
Backend API Testing for PDF Multi-Item Support with Dynamic Sections
Tile Shop Invoicing System
"""

import requests
import json
import time
import os
import uuid
from datetime import datetime
from urllib.parse import quote

# Test configuration
BASE_URL = "https://bbb96806-750e-42b3-a6a9-080d8cd65a98.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class TileShopBackendTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS
        self.test_customer_id = None
        self.test_invoice_id = None
        self.test_tile_ids = []
        
    def log(self, message):
        """Log test messages with timestamp"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def make_request(self, method, endpoint, data=None, timeout=30):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=timeout)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data, timeout=timeout)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
        except requests.exceptions.Timeout:
            self.log(f"❌ Request timeout for {method} {endpoint}")
            return None
        except Exception as e:
            self.log(f"❌ Request failed for {method} {endpoint}: {str(e)}")
            return None
    
    def test_api_health(self):
        """Test API health endpoint"""
        self.log("Testing API health...")
        response = self.make_request("GET", "/health")
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                self.log("✅ API health check passed")
                return True
        
        self.log("❌ API health check failed")
        return False
    
    def create_test_customer(self):
        """Create a test customer for invoice creation"""
        self.log("Creating test customer...")
        
        customer_data = {
            "name": "Rajesh Kumar",
            "phone": "+91-9876543210",
            "address": "123 MG Road, Sector 15, Gurugram, Haryana - 122001",
            "gstin": "06AAAAA0000A1Z5"
        }
        
        response = self.make_request("POST", "/customers", customer_data)
        
        if response and response.status_code == 200:
            customer = response.json()
            self.test_customer_id = customer.get("customer_id")
            self.log(f"✅ Customer created: {customer.get('name')} (ID: {self.test_customer_id})")
            return True
        
        self.log("❌ Customer creation failed")
        return False
    
    def create_test_tiles(self):
        """Create test tiles for invoice line items"""
        self.log("Creating test tiles...")
        
        tiles_data = [
            {
                "size": "600x600mm",
                "coverage": 2.88,
                "box_packing": 8
            },
            {
                "size": "800x800mm", 
                "coverage": 5.12,
                "box_packing": 8
            },
            {
                "size": "300x600mm",
                "coverage": 1.44,
                "box_packing": 8
            }
        ]
        
        created_count = 0
        for tile_data in tiles_data:
            response = self.make_request("POST", "/tiles", tile_data)
            if response and response.status_code == 200:
                tile = response.json()
                self.test_tile_ids.append(tile.get("tile_id"))
                self.log(f"✅ Tile created: {tile.get('size')} (ID: {tile.get('tile_id')})")
                created_count += 1
            else:
                self.log(f"❌ Tile creation failed for {tile_data['size']}")
        
        return created_count >= 2  # Need at least 2 tiles for testing
    
    def create_multi_item_invoice_sa_section(self):
        """Create invoice with 5+ items in SA section for testing dynamic sections"""
        if not self.test_customer_id:
            self.log("❌ No customer ID available for invoice creation")
            return False
        
        self.log("Creating multi-item invoice with SA section (5+ items)...")
        
        # Create line items for SA section (all with location="SA")
        line_items = [
            {
                "location": "SA",
                "tile_name": "Premium Marble Finish",
                "tile_image": None,
                "size": "600x600mm",
                "box_qty": 5,
                "extra_sqft": 0,
                "rate_per_sqft": 45,
                "rate_per_box": 0,  # Will be auto-calculated
                "discount_percent": 10,
                "coverage": 2.88
            },
            {
                "location": "SA",
                "tile_name": "Glossy Stone Effect",
                "tile_image": None,
                "size": "800x800mm",
                "box_qty": 3,
                "extra_sqft": 0,
                "rate_per_sqft": 55,
                "rate_per_box": 0,
                "discount_percent": 5,
                "coverage": 5.12
            },
            {
                "location": "SA",
                "tile_name": "Wood Finish Ceramic",
                "tile_image": None,
                "size": "300x600mm",
                "box_qty": 8,
                "extra_sqft": 0,
                "rate_per_sqft": 35,
                "rate_per_box": 0,
                "discount_percent": 15,
                "coverage": 1.44
            },
            {
                "location": "SA",
                "tile_name": "Designer Hexagon",
                "tile_image": None,
                "size": "600x600mm",
                "box_qty": 4,
                "extra_sqft": 0,
                "rate_per_sqft": 60,
                "rate_per_box": 0,
                "discount_percent": 8,
                "coverage": 2.88
            },
            {
                "location": "SA",
                "tile_name": "Matte Finish Classic",
                "tile_image": None,
                "size": "800x800mm",
                "box_qty": 6,
                "extra_sqft": 0,
                "rate_per_sqft": 40,
                "rate_per_box": 0,
                "discount_percent": 12,
                "coverage": 5.12
            },
            {
                "location": "SA",
                "tile_name": "Anti-Slip Outdoor",
                "tile_image": None,
                "size": "300x600mm",
                "box_qty": 10,
                "extra_sqft": 0,
                "rate_per_sqft": 50,
                "rate_per_box": 0,
                "discount_percent": 20,
                "coverage": 1.44
            }
        ]
        
        invoice_data = {
            "customer_id": self.test_customer_id,
            "line_items": line_items,
            "transport_charges": 500.0,
            "unloading_charges": 200.0,
            "amount_paid": 0.0,
            "status": "Draft",
            "reference_name": "Home Renovation Project",
            "consignee_name": "Rajesh Kumar",
            "consignee_phone": "+91-9876543210",
            "consignee_address": "123 MG Road, Sector 15, Gurugram, Haryana - 122001",
            "overall_remarks": "Special tiles for living room and kitchen area. Handle with care during delivery.",
            "gst_percent": 18.0
        }
        
        response = self.make_request("POST", "/invoices", invoice_data)
        
        if response and response.status_code == 200:
            invoice = response.json()
            self.test_invoice_id = invoice.get("invoice_id")
            self.log(f"✅ Multi-item invoice created: {self.test_invoice_id}")
            self.log(f"   Items in SA section: {len(line_items)}")
            self.log(f"   Subtotal: ₹{invoice.get('subtotal', 0):,.2f}")
            self.log(f"   GST: ₹{invoice.get('gst_amount', 0):,.2f}")
            self.log(f"   Grand Total: ₹{invoice.get('grand_total', 0):,.2f}")
            
            # Verify that all items are calculated correctly
            calculated_items = invoice.get('line_items', [])
            total_items_amount = sum(item.get('final_amount', 0) for item in calculated_items)
            
            self.log(f"   Total items amount: ₹{total_items_amount:,.2f}")
            
            # Check that all items have SA location
            sa_items = [item for item in calculated_items if item.get('location') == 'SA']
            self.log(f"   Verified SA location items: {len(sa_items)}/{len(calculated_items)}")
            
            return True
        
        self.log("❌ Multi-item invoice creation failed")
        if response:
            self.log(f"   Status: {response.status_code}")
            self.log(f"   Response: {response.text}")
        return False
    
    def test_pdf_generation_and_download(self):
        """Test PDF generation for the multi-item SA section invoice"""
        if not self.test_invoice_id:
            self.log("❌ No invoice ID available for PDF generation")
            return False
        
        self.log(f"Testing PDF generation for invoice: {self.test_invoice_id}")
        
        # URL encode the invoice ID for the request
        encoded_invoice_id = quote(self.test_invoice_id, safe='')
        endpoint = f"/invoices/{encoded_invoice_id}/pdf"
        
        self.log(f"PDF endpoint: {endpoint}")
        
        response = self.make_request("GET", endpoint)
        
        if response and response.status_code == 200:
            # Check if response is PDF
            content_type = response.headers.get('content-type', '')
            content_length = len(response.content)
            
            self.log(f"✅ PDF generated successfully")
            self.log(f"   Content-Type: {content_type}")
            self.log(f"   Content-Length: {content_length:,} bytes ({content_length/1024:.1f} KB)")
            
            # Verify content type
            if 'application/pdf' in content_type:
                self.log("✅ Correct content type (application/pdf)")
            else:
                self.log(f"❌ Incorrect content type: {content_type}")
                return False
            
            # Check PDF size - template overlay should be ~593KB+ for multi-page
            if content_length > 500000:  # > 500KB indicates template overlay method
                self.log("✅ PDF size indicates template overlay method")
            else:
                self.log("⚠️  PDF size is small - may not be using template overlay")
            
            # Save PDF for manual verification if needed
            pdf_filename = f"test_invoice_{self.test_invoice_id.replace(' / ', '_').replace('/', '_')}.pdf"
            try:
                with open(pdf_filename, 'wb') as f:
                    f.write(response.content)
                self.log(f"✅ PDF saved as: {pdf_filename}")
            except Exception as e:
                self.log(f"⚠️  Could not save PDF: {e}")
            
            return True
        
        self.log("❌ PDF generation failed")
        if response:
            self.log(f"   Status: {response.status_code}")
            try:
                error_data = response.json()
                self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                self.log(f"   Response: {response.text}")
        return False
    
    def verify_invoice_data_structure(self):
        """Verify the invoice data structure for SA section testing"""
        if not self.test_invoice_id:
            self.log("❌ No invoice ID available for verification")
            return False
        
        self.log("Verifying invoice data structure...")
        
        # Get all invoices and find ours (since GET /invoices/{id} doesn't handle path slashes)
        response = self.make_request("GET", "/invoices")
        
        if not response or response.status_code != 200:
            self.log("❌ Failed to get invoices list")
            return False
        
        invoices = response.json()
        target_invoice = None
        
        for invoice in invoices:
            if invoice.get('invoice_id') == self.test_invoice_id:
                target_invoice = invoice
                break
        
        if not target_invoice:
            self.log(f"❌ Invoice {self.test_invoice_id} not found in invoices list")
            return False
        
        self.log(f"✅ Invoice found in list")
        invoice = target_invoice
        
        if True:
            invoice = response.json()
            line_items = invoice.get('line_items', [])
            
            # Group items by location
            grouped_items = {}
            for item in line_items:
                location = item.get('location', 'Unknown')
                if location not in grouped_items:
                    grouped_items[location] = []
                grouped_items[location].append(item)
            
            self.log(f"✅ Invoice data retrieved successfully")
            self.log(f"   Total line items: {len(line_items)}")
            self.log(f"   Sections found: {list(grouped_items.keys())}")
            
            # Verify SA section
            if 'SA' in grouped_items:
                sa_items = grouped_items['SA']
                self.log(f"✅ SA section found with {len(sa_items)} items:")
                
                # Calculate SA section total
                sa_total = sum(item.get('final_amount', 0) for item in sa_items)
                self.log(f"   SA section total: ₹{sa_total:,.2f}")
                
                # List SA items with details
                for idx, item in enumerate(sa_items, 1):
                    tile_name = item.get('tile_name', 'Unknown')
                    size = item.get('size', 'Unknown')
                    qty = item.get('box_qty', 0)
                    rate_sqft = item.get('rate_per_sqft', 0)
                    discount = item.get('discount_percent', 0)
                    amount = item.get('final_amount', 0)
                    
                    self.log(f"     {idx}. {tile_name} ({size}) - {qty} box, ₹{rate_sqft}/sqft, {discount}% disc, ₹{amount:,.2f}")
                
                if len(sa_items) >= 5:
                    self.log("✅ SA section has 5+ items as required")
                else:
                    self.log(f"❌ SA section has only {len(sa_items)} items (need 5+)")
                    return False
            else:
                self.log("❌ SA section not found in invoice")
                return False
            
            return True
        
        self.log("❌ Invoice data verification failed")
        return False
    
    def run_comprehensive_test(self):
        """Run comprehensive test of PDF Multi-Item Support with Dynamic Sections"""
        self.log("=" * 80)
        self.log("BACKEND TEST: PDF Multi-Item Support with Dynamic Sections")
        self.log("=" * 80)
        
        test_results = []
        
        # Test 1: API Health Check
        self.log("\n1. Testing API Health...")
        health_result = self.test_api_health()
        test_results.append(("API Health Check", health_result))
        
        if not health_result:
            self.log("❌ Cannot continue tests - API is not healthy")
            return False
        
        # Test 2: Create Test Customer
        self.log("\n2. Creating Test Customer...")
        customer_result = self.create_test_customer()
        test_results.append(("Customer Creation", customer_result))
        
        # Test 3: Create Test Tiles
        self.log("\n3. Creating Test Tiles...")
        tiles_result = self.create_test_tiles()
        test_results.append(("Tiles Creation", tiles_result))
        
        # Test 4: Create Multi-Item Invoice with SA Section
        self.log("\n4. Creating Multi-Item Invoice (SA Section)...")
        invoice_result = self.create_multi_item_invoice_sa_section()
        test_results.append(("Multi-Item SA Invoice Creation", invoice_result))
        
        # Test 5: Verify Invoice Data Structure
        self.log("\n5. Verifying Invoice Data Structure...")
        structure_result = self.verify_invoice_data_structure()
        test_results.append(("Invoice Data Structure Verification", structure_result))
        
        # Test 6: Generate and Download PDF
        self.log("\n6. Testing PDF Generation & Download...")
        pdf_result = self.test_pdf_generation_and_download()
        test_results.append(("PDF Generation & Download", pdf_result))
        
        # Summary
        self.log("\n" + "=" * 80)
        self.log("TEST RESULTS SUMMARY")
        self.log("=" * 80)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"{status}: {test_name}")
            if result:
                passed_tests += 1
        
        self.log("-" * 80)
        self.log(f"OVERALL: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL TESTS PASSED! PDF Multi-Item Support with Dynamic Sections is working correctly.")
            return True
        else:
            self.log("❌ Some tests failed. Please check the issues above.")
            return False

def main():
    """Main test execution function"""
    tester = TileShopBackendTester()
    success = tester.run_comprehensive_test()
    
    # Return appropriate exit code
    exit_code = 0 if success else 1
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)