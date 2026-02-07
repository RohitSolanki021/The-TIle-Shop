import requests
import sys
import json
from datetime import datetime

class TileShopAPITester:
    def __init__(self, base_url="https://tile-boutique.preview.emergentagent.com"):
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

    def test_create_invoice_with_optional_fields(self):
        """Test invoice creation with new optional fields"""
        if not self.created_customer_id:
            print("❌ Cannot test invoice creation - no customer created")
            return False
            
        invoice_data = {
            "customer_id": self.created_customer_id,
            "line_items": [
                {
                    "location": "Main Floor",
                    "tile_name": "Premium Vitrified Tiles",
                    "size": "600x600mm",
                    "box_qty": 5,
                    "extra_sqft": 10.5,
                    "rate_per_sqft": 45.0,
                    "rate_per_box": 0,
                    "discount_percent": 5.0,
                    "coverage": 23.68,
                    "box_packing": 4
                }
            ],
            "transport_charges": 500.0,
            "unloading_charges": 200.0,
            "amount_paid": 1000.0,
            "status": "Draft",
            # New optional fields
            "reference_name": "Mr. John Doe",
            "consignee_name": "ABC Construction Ltd",
            "consignee_phone": "+91 9876543211",
            "consignee_address": "456 Construction Site, Building City - 654321",
            "overall_remarks": "Please handle with care. Delivery required by end of week.",
            "gst_percent": 18.0
        }
        
        success, response = self.run_test(
            "Create Invoice with Optional Fields",
            "POST",
            "invoices",
            200,
            data=invoice_data
        )
        
        if success and 'invoice_id' in response:
            self.created_invoice_id = response['invoice_id']
            print(f"   Created invoice ID: {self.created_invoice_id}")
            
            # Verify optional fields are saved
            if response.get('reference_name') == "Mr. John Doe":
                print("   ✅ Reference name saved correctly")
            if response.get('gst_percent') == 18.0:
                print("   ✅ GST percentage saved correctly")
            if response.get('consignee_name') == "ABC Construction Ltd":
                print("   ✅ Consignee details saved correctly")
            if response.get('overall_remarks'):
                print("   ✅ Overall remarks saved correctly")
                
            # Check GST calculation
            expected_gst = response.get('subtotal', 0) * 0.18
            actual_gst = response.get('gst_amount', 0)
            if abs(expected_gst - actual_gst) < 0.01:
                print(f"   ✅ GST calculation correct: ₹{actual_gst:.2f}")
            else:
                print(f"   ❌ GST calculation incorrect: expected ₹{expected_gst:.2f}, got ₹{actual_gst:.2f}")
            
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

    def test_pdf_generation(self):
        """Test PDF generation and download"""
        if not self.created_invoice_id:
            print("❌ Cannot test PDF generation - no invoice created")
            return False
            
        print(f"\n🔍 Testing PDF Generation...")
        url = f"{self.api_url}/invoices/{self.created_invoice_id}/pdf"
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                # Check if response is PDF
                content_type = response.headers.get('content-type', '')
                if 'application/pdf' in content_type:
                    print("✅ PDF generated successfully")
                    print(f"   Content-Type: {content_type}")
                    print(f"   Content-Length: {len(response.content)} bytes")
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
        ("Create Invoice with Optional Fields", tester.test_create_invoice_with_optional_fields),
        ("Get Invoice", tester.test_get_invoice),
        ("PDF Generation", tester.test_pdf_generation),
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