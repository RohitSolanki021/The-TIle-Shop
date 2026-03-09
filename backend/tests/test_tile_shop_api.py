"""
Tile Shop API Tests
====================
Tests for Tiles, Granites, Customers, and Invoices endpoints
Includes product type variations: tiles_box, tile_pieces, granite
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://granite-tile-swap.preview.emergentagent.com').rstrip('/')

class TestHealthEndpoint:
    """Health check tests"""
    
    def test_health_endpoint(self):
        """Test API health status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Health endpoint working")


class TestTilesEndpoints:
    """Tiles CRUD operations"""
    
    def test_get_tiles(self):
        """Test fetching all tiles"""
        response = requests.get(f"{BASE_URL}/api/tiles")
        assert response.status_code == 200
        tiles = response.json()
        assert isinstance(tiles, list)
        print(f"✓ GET /api/tiles - Found {len(tiles)} tiles")
    
    def test_create_tile(self):
        """Test creating a tile"""
        tile_data = {
            "size": f"TEST_{uuid.uuid4().hex[:8]}",
            "coverage": 25.5,
            "box_packing": 4
        }
        response = requests.post(f"{BASE_URL}/api/tiles", json=tile_data)
        assert response.status_code == 200
        data = response.json()
        assert data["size"] == tile_data["size"]
        assert data["coverage"] == tile_data["coverage"]
        assert data["box_packing"] == tile_data["box_packing"]
        print(f"✓ POST /api/tiles - Created tile: {data['tile_id']}")
        return data["tile_id"]
    
    def test_create_and_delete_tile(self):
        """Test create and delete cycle"""
        # Create
        tile_data = {
            "size": f"TEST_DELETE_{uuid.uuid4().hex[:8]}",
            "coverage": 20.0,
            "box_packing": 3
        }
        create_response = requests.post(f"{BASE_URL}/api/tiles", json=tile_data)
        assert create_response.status_code == 200
        tile_id = create_response.json()["tile_id"]
        
        # Delete
        delete_response = requests.delete(f"{BASE_URL}/api/tiles/{tile_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "Tile deleted successfully"
        print(f"✓ DELETE /api/tiles/{tile_id} - Tile deleted")


class TestGranitesEndpoints:
    """Granites CRUD operations - NEW FEATURE"""
    
    def test_get_granites(self):
        """Test fetching all granites"""
        response = requests.get(f"{BASE_URL}/api/granites")
        assert response.status_code == 200
        granites = response.json()
        assert isinstance(granites, list)
        print(f"✓ GET /api/granites - Found {len(granites)} granites")
    
    def test_create_granite(self):
        """Test creating a granite"""
        granite_data = {
            "name": f"TEST_Granite_{uuid.uuid4().hex[:8]}",
            "size": "8ft x 4ft",
            "thickness": "18mm",
            "color": "Black",
            "rate_per_piece": 15000.00,
            "rate_per_sqft": 500.00
        }
        response = requests.post(f"{BASE_URL}/api/granites", json=granite_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == granite_data["name"]
        assert data["size"] == granite_data["size"]
        assert data["rate_per_piece"] == granite_data["rate_per_piece"]
        print(f"✓ POST /api/granites - Created granite: {data['granite_id']}")
        return data
    
    def test_update_granite(self):
        """Test updating a granite"""
        # Create first
        granite_data = {
            "name": f"TEST_Update_{uuid.uuid4().hex[:8]}",
            "size": "6ft x 3ft",
            "rate_per_piece": 10000.00
        }
        create_response = requests.post(f"{BASE_URL}/api/granites", json=granite_data)
        assert create_response.status_code == 200
        granite_id = create_response.json()["granite_id"]
        
        # Update
        update_data = {
            "rate_per_piece": 12000.00,
            "color": "Brown"
        }
        update_response = requests.put(f"{BASE_URL}/api/granites/{granite_id}", json=update_data)
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["rate_per_piece"] == 12000.00
        assert updated["color"] == "Brown"
        print(f"✓ PUT /api/granites/{granite_id} - Granite updated")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/granites/{granite_id}")
    
    def test_delete_granite(self):
        """Test deleting a granite"""
        # Create first
        granite_data = {
            "name": f"TEST_Delete_{uuid.uuid4().hex[:8]}",
            "rate_per_piece": 5000.00
        }
        create_response = requests.post(f"{BASE_URL}/api/granites", json=granite_data)
        granite_id = create_response.json()["granite_id"]
        
        # Delete
        delete_response = requests.delete(f"{BASE_URL}/api/granites/{granite_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "Granite deleted successfully"
        print(f"✓ DELETE /api/granites/{granite_id} - Granite deleted")


class TestCustomersEndpoints:
    """Customers CRUD operations"""
    
    def test_get_customers(self):
        """Test fetching all customers"""
        response = requests.get(f"{BASE_URL}/api/customers")
        assert response.status_code == 200
        customers = response.json()
        assert isinstance(customers, list)
        print(f"✓ GET /api/customers - Found {len(customers)} customers")
    
    def test_create_customer(self):
        """Test creating a customer"""
        customer_data = {
            "name": f"TEST_Customer_{uuid.uuid4().hex[:8]}",
            "phone": "9876543210",
            "address": "123 Test Street, Test City"
        }
        response = requests.post(f"{BASE_URL}/api/customers", json=customer_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == customer_data["name"]
        assert data["phone"] == customer_data["phone"]
        assert "customer_id" in data
        print(f"✓ POST /api/customers - Created customer: {data['customer_id']}")
        return data


class TestInvoicesEndpoints:
    """Invoices CRUD operations with different product types"""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Create test customer for invoice tests"""
        customer_data = {
            "name": f"TEST_Invoice_Customer_{uuid.uuid4().hex[:8]}",
            "phone": "9999888877",
            "address": "456 Invoice Test Road"
        }
        response = requests.post(f"{BASE_URL}/api/customers", json=customer_data)
        self.customer = response.json()
        yield
        # Cleanup
        if hasattr(self, 'customer'):
            requests.delete(f"{BASE_URL}/api/customers/{self.customer['customer_id']}")
    
    def test_get_invoices(self):
        """Test fetching all invoices"""
        response = requests.get(f"{BASE_URL}/api/invoices")
        assert response.status_code == 200
        invoices = response.json()
        assert isinstance(invoices, list)
        print(f"✓ GET /api/invoices - Found {len(invoices)} invoices")
    
    def test_create_invoice_tiles_box(self):
        """Test creating invoice with tiles_box product type"""
        invoice_data = {
            "customer_id": self.customer["customer_id"],
            "line_items": [{
                "product_type": "tiles_box",
                "location": "Living Room",
                "tile_name": "Test Vitrified Tile",
                "size": "600x600mm",
                "box_qty": 10,
                "extra_sqft": 5,
                "rate_per_sqft": 50.0,
                "coverage": 20.0,
                "discount_percent": 5
            }],
            "transport_charges": 500,
            "unloading_charges": 200
        }
        response = requests.post(f"{BASE_URL}/api/invoices", json=invoice_data)
        assert response.status_code == 200
        data = response.json()
        assert data["customer_name"] == self.customer["name"]
        assert len(data["line_items"]) == 1
        assert data["line_items"][0]["product_type"] == "tiles_box"
        assert data["subtotal"] > 0
        print(f"✓ POST /api/invoices (tiles_box) - Invoice: {data['invoice_id']}")
        
        # Cleanup
        encoded_id = data['invoice_id'].replace(' ', '%20').replace('/', '%2F')
        requests.delete(f"{BASE_URL}/api/invoices/{encoded_id}")
    
    def test_create_invoice_tile_pieces(self):
        """Test creating invoice with tile_pieces product type (NEW)"""
        invoice_data = {
            "customer_id": self.customer["customer_id"],
            "line_items": [{
                "product_type": "tile_pieces",
                "location": "Kitchen",
                "tile_name": "Individual Floor Tile",
                "size": "300x300mm",
                "extra_sqft": 15.5,  # Manual sqft entry
                "rate_per_sqft": 75.0,
                "discount_percent": 0
            }],
            "transport_charges": 0
        }
        response = requests.post(f"{BASE_URL}/api/invoices", json=invoice_data)
        assert response.status_code == 200
        data = response.json()
        assert len(data["line_items"]) == 1
        assert data["line_items"][0]["product_type"] == "tile_pieces"
        # Total should be 15.5 * 75 = 1162.50
        assert data["subtotal"] == 1162.5
        print(f"✓ POST /api/invoices (tile_pieces) - Invoice: {data['invoice_id']}, Subtotal: {data['subtotal']}")
        
        # Cleanup
        encoded_id = data['invoice_id'].replace(' ', '%20').replace('/', '%2F')
        requests.delete(f"{BASE_URL}/api/invoices/{encoded_id}")
    
    def test_create_invoice_granite(self):
        """Test creating invoice with granite product type (NEW)"""
        invoice_data = {
            "customer_id": self.customer["customer_id"],
            "line_items": [{
                "product_type": "granite",
                "location": "Kitchen Counter",
                "tile_name": "Black Galaxy Granite",
                "size": "8ft x 4ft",
                "quantity": 2,  # 2 pieces/slabs
                "rate_per_piece": 15000.0,
                "discount_percent": 10
            }],
            "transport_charges": 1000
        }
        response = requests.post(f"{BASE_URL}/api/invoices", json=invoice_data)
        assert response.status_code == 200
        data = response.json()
        assert len(data["line_items"]) == 1
        assert data["line_items"][0]["product_type"] == "granite"
        # Total: 2 * 15000 = 30000, 10% discount = 3000, final = 27000
        assert data["subtotal"] == 27000.0
        print(f"✓ POST /api/invoices (granite) - Invoice: {data['invoice_id']}, Subtotal: {data['subtotal']}")
        
        # Cleanup
        encoded_id = data['invoice_id'].replace(' ', '%20').replace('/', '%2F')
        requests.delete(f"{BASE_URL}/api/invoices/{encoded_id}")
    
    def test_create_invoice_mixed_products(self):
        """Test invoice with all three product types"""
        invoice_data = {
            "customer_id": self.customer["customer_id"],
            "line_items": [
                {
                    "product_type": "tiles_box",
                    "location": "Floor",
                    "tile_name": "Ceramic Tile",
                    "size": "600x600mm",
                    "box_qty": 5,
                    "coverage": 20.0,
                    "rate_per_sqft": 40.0,
                    "discount_percent": 0
                },
                {
                    "product_type": "tile_pieces",
                    "location": "Wall",
                    "tile_name": "Border Tile",
                    "extra_sqft": 10,
                    "rate_per_sqft": 100.0,
                    "discount_percent": 5
                },
                {
                    "product_type": "granite",
                    "location": "Counter",
                    "tile_name": "Tan Brown Granite",
                    "quantity": 1,
                    "rate_per_piece": 12000.0,
                    "discount_percent": 0
                }
            ],
            "transport_charges": 500
        }
        response = requests.post(f"{BASE_URL}/api/invoices", json=invoice_data)
        assert response.status_code == 200
        data = response.json()
        assert len(data["line_items"]) == 3
        
        # Verify all product types present
        product_types = [item["product_type"] for item in data["line_items"]]
        assert "tiles_box" in product_types
        assert "tile_pieces" in product_types
        assert "granite" in product_types
        
        # Calculate expected total:
        # tiles_box: 5 * 20 * 40 = 4000
        # tile_pieces: 10 * 100 * 0.95 = 950
        # granite: 12000
        # subtotal = 16950, transport = 500, grand = 17450
        assert data["subtotal"] > 0
        print(f"✓ POST /api/invoices (mixed) - Invoice: {data['invoice_id']}, Subtotal: {data['subtotal']}")
        
        # Cleanup
        encoded_id = data['invoice_id'].replace(' ', '%20').replace('/', '%2F')
        requests.delete(f"{BASE_URL}/api/invoices/{encoded_id}")


class TestPDFGeneration:
    """Test PDF generation for different product types"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create test customer and invoice"""
        customer_data = {
            "name": f"TEST_PDF_Customer_{uuid.uuid4().hex[:8]}",
            "phone": "8888777766",
            "address": "PDF Test Address"
        }
        response = requests.post(f"{BASE_URL}/api/customers", json=customer_data)
        self.customer = response.json()
        yield
        # Cleanup
        requests.delete(f"{BASE_URL}/api/customers/{self.customer['customer_id']}")
    
    def test_pdf_generation_mixed_products(self):
        """Test PDF generation with all product types"""
        invoice_data = {
            "customer_id": self.customer["customer_id"],
            "line_items": [
                {
                    "product_type": "tiles_box",
                    "location": "Room 1",
                    "tile_name": "PDF Test Tile",
                    "size": "600x600mm",
                    "box_qty": 3,
                    "coverage": 20.0,
                    "rate_per_sqft": 50.0
                },
                {
                    "product_type": "granite",
                    "location": "Room 2",
                    "tile_name": "PDF Test Granite",
                    "quantity": 1,
                    "rate_per_piece": 10000.0
                }
            ]
        }
        # Create invoice
        create_response = requests.post(f"{BASE_URL}/api/invoices", json=invoice_data)
        assert create_response.status_code == 200
        invoice_id = create_response.json()["invoice_id"]
        
        # Get PDF
        encoded_id = invoice_id.replace(' ', '%20').replace('/', '%2F')
        pdf_response = requests.get(f"{BASE_URL}/api/invoices/{encoded_id}/pdf")
        assert pdf_response.status_code == 200
        assert pdf_response.headers.get('content-type') == 'application/pdf'
        assert len(pdf_response.content) > 1000  # PDF should have content
        print(f"✓ GET /api/invoices/{invoice_id}/pdf - PDF generated, size: {len(pdf_response.content)} bytes")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/invoices/{encoded_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
