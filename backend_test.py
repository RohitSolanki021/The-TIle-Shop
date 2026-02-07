import requests
import sys
import json
from datetime import datetime

class TileShopAPITester:
    def __init__(self, base_url="https://8fee7af5-8b36-4847-8c09-b747b3cd7bd6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_customer_id = None
        self.created_tile_id = None
        self.created_invoice_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            print(f"   Status: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json() if response.content else {}
                    return success, response_data
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test API health check"""
        return self.run_test("Health Check", "GET", "health", 200)

    def test_create_customer(self):
        """Test customer creation"""
        customer_data = {
            "name": f"Test Customer {datetime.now().strftime('%H%M%S')}",
            "phone": "+91 9876543210",
            "address": "123 Test Street, Test City, Test State - 123456",
            "gstin": "27ABCDE1234F1Z5"
        }
        
        success, response = self.run_test(
            "Create Customer",
            "POST",
            "customers",
            200,
            data=customer_data
        )
        
        if success and 'customer_id' in response:
            self.created_customer_id = response['customer_id']
            print(f"   Created customer ID: {self.created_customer_id}")
            return True
        return False

    def test_create_tile(self):
        """Test tile creation"""
        tile_data = {
            "size": "600x600mm",
            "coverage": 23.68,
            "box_packing": 4
        }
        
        success, response = self.run_test(
            "Create Tile",
            "POST",
            "tiles",
            200,
            data=tile_data
        )
        
        if success and 'tile_id' in response:
            self.created_tile_id = response['tile_id']
            print(f"   Created tile ID: {self.created_tile_id}")
            return True
        return False

    def test_create_custom_tile_size(self):
        """Test creating custom tile size that should persist"""
        custom_tile_data = {
            "size": "750x1500mm",  # Custom size not in predefined list
            "coverage": 28.5,
            "box_packing": 3
        }
        
        success, response = self.run_test(
            "Create Custom Tile Size",
            "POST",
            "tiles",
            200,
            data=custom_tile_data
        )
        
        if success and 'tile_id' in response:
            custom_tile_id = response['tile_id']
            print(f"   Created custom tile ID: {custom_tile_id}")
            
            # Verify it appears in GET /api/tiles
            success2, tiles_response = self.run_test(
                "Verify Custom Tile in List",
                "GET",
                "tiles",
                200
            )
            
            if success2:
                custom_tile_found = any(
                    tile.get('size') == '750x1500mm' for tile in tiles_response
                )
                if custom_tile_found:
                    print("   ✅ Custom tile size persists in database")
                    return True
                else:
                    print("   ❌ Custom tile size not found in tiles list")
            return False
        return False

    def test_create_invoice_multiple_locations(self):
        """Test invoice creation with multiple locations for SR NO. reset testing"""
        if not self.created_customer_id:
            print("❌ Cannot test invoice creation - no customer created")
            return False
            
        invoice_data = {
            "customer_id": self.created_customer_id,
            "line_items": [
                {
                    "location": "Kitchen",
                    "tile_name": "Kitchen Floor Tiles",
                    "size": "600x600mm",
                    "box_qty": 3,
                    "extra_sqft": 5.0,
                    "rate_per_sqft": 50.0,
                    "rate_per_box": 0,
                    "discount_percent": 0.0,
                    "coverage": 23.68,
                    "box_packing": 4
                },
                {
                    "location": "Kitchen",
                    "tile_name": "Kitchen Wall Tiles",
                    "size": "300x600mm",
                    "box_qty": 2,
                    "extra_sqft": 0.0,
                    "rate_per_sqft": 40.0,
                    "rate_per_box": 0,
                    "discount_percent": 0.0,
                    "coverage": 15.0,
                    "box_packing": 6
                },
                {
                    "location": "Kitchen",
                    "tile_name": "Kitchen Border Tiles",
                    "size": "100x600mm",
                    "box_qty": 1,
                    "extra_sqft": 0.0,
                    "rate_per_sqft": 60.0,
                    "rate_per_box": 0,
                    "discount_percent": 0.0,
                    "coverage": 8.0,
                    "box_packing": 10
                },
                {
                    "location": "Bathroom",
                    "tile_name": "Bathroom Floor Tiles",
                    "size": "300x300mm",
                    "box_qty": 2,
                    "extra_sqft": 0.0,
                    "rate_per_sqft": 45.0,
                    "rate_per_box": 0,
                    "discount_percent": 0.0,
                    "coverage": 12.0,
                    "box_packing": 8
                },
                {
                    "location": "Bathroom",
                    "tile_name": "Bathroom Wall Tiles",
                    "size": "200x300mm",
                    "box_qty": 3,
                    "extra_sqft": 0.0,
                    "rate_per_sqft": 35.0,
                    "rate_per_box": 0,
                    "discount_percent": 0.0,
                    "coverage": 10.0,
                    "box_packing": 12
                }
            ],
            "transport_charges": 300.0,
            "unloading_charges": 150.0,
            "amount_paid": 500.0,
            "status": "Draft",
            "gst_percent": 0  # Empty GST for testing placeholder text
        }
        
        success, response = self.run_test(
            "Create Invoice with Multiple Locations",
            "POST",
            "invoices",
            200,
            data=invoice_data
        )
        
        if success and 'invoice_id' in response:
            self.created_invoice_id = response['invoice_id']
            print(f"   Created invoice ID: {self.created_invoice_id}")
            
            # Verify GST is 0 for empty state testing
            if response.get('gst_percent') == 0 and response.get('gst_amount') == 0:
                print("   ✅ GST empty state configured correctly")
            else:
                print(f"   ❌ GST not empty: percent={response.get('gst_percent')}, amount={response.get('gst_amount')}")
            
            return True
        return False

    def test_get_invoice(self):
        """Test retrieving invoice"""
        if not self.created_invoice_id:
            print("❌ Cannot test get invoice - no invoice created")
            return False
            
        return self.run_test(
            "Get Invoice",
            "GET",
            f"invoices/{self.created_invoice_id}",
            200
        )[0]

    def test_invoice_id_format(self):
        """Test that new invoices use TTS / XXX / YYYY-YY format and auto-increment"""
        if not self.created_customer_id:
            print("❌ Cannot test invoice ID format - no customer created")
            return False
            
        invoice_data = {
            "customer_id": self.created_customer_id,
            "line_items": [
                {
                    "location": "Testing Area",
                    "tile_name": "Test Tile for ID Format",
                    "size": "600x600mm",
                    "box_qty": 1,
                    "extra_sqft": 0.0,
                    "rate_per_sqft": 100.0,
                    "rate_per_box": 0,
                    "discount_percent": 0.0,
                    "coverage": 23.68,
                    "box_packing": 4
                }
            ],
            "transport_charges": 0.0,
            "unloading_charges": 0.0,
            "amount_paid": 0.0,
            "status": "Draft",
            "gst_percent": 0
        }
        
        # Create first invoice
        success1, response1 = self.run_test(
            "Create Invoice 1 - Check ID Format",
            "POST",
            "invoices",
            200,
            data=invoice_data
        )
        
        if not success1 or 'invoice_id' not in response1:
            return False
            
        invoice_id_1 = response1['invoice_id']
        print(f"   First Invoice ID: {invoice_id_1}")
        
        # Verify format: TTS / XXX / YYYY-YY
        import re
        pattern = r'^TTS / \d{3} / \d{4}-\d{2}$'
        if not re.match(pattern, invoice_id_1):
            print(f"❌ Invoice ID format incorrect. Expected: TTS / XXX / YYYY-YY, got: {invoice_id_1}")
            return False
        
        print(f"✅ Invoice ID format is correct: {invoice_id_1}")
        
        # Create second invoice to test auto-increment
        success2, response2 = self.run_test(
            "Create Invoice 2 - Check Auto-increment",
            "POST",
            "invoices",
            200,
            data=invoice_data
        )
        
        if not success2 or 'invoice_id' not in response2:
            return False
            
        invoice_id_2 = response2['invoice_id']
        print(f"   Second Invoice ID: {invoice_id_2}")
        
        # Extract sequence numbers
        seq1 = int(invoice_id_1.split(' / ')[1])
        seq2 = int(invoice_id_2.split(' / ')[1])
        
        if seq2 == seq1 + 1:
            print(f"✅ Auto-increment working: {seq1} → {seq2}")
            # Store the second invoice for PDF testing
            self.created_invoice_id = invoice_id_2
            return True
        else:
            print(f"❌ Auto-increment failed: {seq1} → {seq2}")
            return False

    def test_pdf_generation_with_template_overlay(self):
        """Test PDF generation using template overlay method and verify file size"""
        if not self.created_invoice_id:
            print("❌ Cannot test PDF generation - no invoice created")
            return False
            
        print(f"\n🔍 Testing PDF Generation with Template Overlay...")
        
        # Test with URL encoding to handle TTS / XXX / YYYY-YY format
        import urllib.parse
        encoded_invoice_id = urllib.parse.quote(self.created_invoice_id, safe='')
        url = f"{self.api_url}/invoices/{encoded_invoice_id}/pdf"
        print(f"   URL: {url}")
        print(f"   Invoice ID: {self.created_invoice_id}")
        
        try:
            response = requests.get(url)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                # Check if response is PDF
                content_type = response.headers.get('content-type', '')
                if 'application/pdf' in content_type:
                    file_size = len(response.content)
                    print(f"✅ PDF generated successfully")
                    print(f"   Content-Type: {content_type}")
                    print(f"   Content-Length: {file_size} bytes ({file_size/1024:.1f}KB)")
                    
                    # Check if file size indicates template overlay method (should be substantial)
                    if file_size >= 500000:  # 500KB+ indicates template with overlay
                        print(f"✅ PDF size indicates template overlay method (>{file_size/1024:.0f}KB)")
                    else:
                        print(f"⚠️  PDF size may indicate recreated layout ({file_size/1024:.0f}KB)")
                    
                    # Save PDF for verification
                    safe_filename = self.created_invoice_id.replace(" / ", "-").replace("/", "-")
                    pdf_path = f'/tmp/test_invoice_{safe_filename}.pdf'
                    with open(pdf_path, 'wb') as f:
                        f.write(response.content)
                    print(f"   📄 PDF saved to {pdf_path} for verification")
                    
                    self.tests_passed += 1
                    return True
                else:
                    print(f"❌ Wrong content type: {content_type}")
            else:
                print(f"❌ Failed - Status: {response.status_code}")
                try:
                    error = response.json()
                    print(f"   Error: {error}")
                except:
                    print(f"   Response: {response.text[:200]}")
                    
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            
        self.tests_run += 1
        return False

    def test_get_customers(self):
        """Test getting all customers"""
        return self.run_test("Get All Customers", "GET", "customers", 200)[0]

    def test_get_tiles(self):
        """Test getting all tiles"""
        return self.run_test("Get All Tiles", "GET", "tiles", 200)[0]

    def test_get_invoices(self):
        """Test getting all invoices"""
        return self.run_test("Get All Invoices", "GET", "invoices", 200)[0]

def main():
    print("🚀 Starting Tile Shop API Testing...")
    print("=" * 60)
    
    tester = TileShopAPITester()
    
    # Test sequence
    tests = [
        ("Health Check", tester.test_health_check),
        ("Create Customer", tester.test_create_customer),
        ("Create Tile", tester.test_create_tile),
        ("Create Custom Tile Size", tester.test_create_custom_tile_size),
        ("Create Invoice with Multiple Locations", tester.test_create_invoice_multiple_locations),
        ("Get Invoice", tester.test_get_invoice),
        ("PDF Generation with SR NO. Reset", tester.test_pdf_generation_sr_no_reset),
        ("Get All Customers", tester.test_get_customers),
        ("Get All Tiles", tester.test_get_tiles),
        ("Get All Invoices", tester.test_get_invoices)
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        try:
            if not test_func():
                failed_tests.append(test_name)
        except Exception as e:
            print(f"❌ {test_name} crashed: {str(e)}")
            failed_tests.append(test_name)
            tester.tests_run += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {tester.tests_run}")
    print(f"Passed: {tester.tests_passed}")
    print(f"Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for test in failed_tests:
            print(f"   - {test}")
    else:
        print(f"\n✅ All tests passed!")
    
    # Print created resources for cleanup/reference
    if tester.created_customer_id:
        print(f"\n📝 Created Resources:")
        print(f"   Customer ID: {tester.created_customer_id}")
    if tester.created_tile_id:
        print(f"   Tile ID: {tester.created_tile_id}")
    if tester.created_invoice_id:
        print(f"   Invoice ID: {tester.created_invoice_id}")
        print(f"   PDF URL: {tester.api_url}/invoices/{tester.created_invoice_id}/pdf")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())