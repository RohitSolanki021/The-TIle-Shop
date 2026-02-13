"""
Comprehensive CRUD and Delete Tests for Tile Shop Invoice App
Tests: Tiles, Customers, Invoices - Create, Read, Update, Delete operations
Focus: Delete functionality (soft delete) and WhatsApp share preparation
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tile-invoice-app.preview.emergentagent.com').rstrip('/')

class TestHealthCheck:
    """Health check tests"""
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ Health check passed: {data}")


class TestTilesCRUD:
    """Tiles CRUD operations tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.test_tile_id = None
        yield
        # Cleanup - delete test tile if created
        if self.test_tile_id:
            try:
                requests.delete(f"{BASE_URL}/api/tiles/{self.test_tile_id}")
            except:
                pass
    
    def test_create_tile(self):
        """Test creating a new tile"""
        tile_data = {
            "size": "TEST_600x600mm",
            "coverage": 23.68,
            "box_packing": 4
        }
        response = requests.post(f"{BASE_URL}/api/tiles", json=tile_data)
        assert response.status_code == 200, f"Failed to create tile: {response.text}"
        
        data = response.json()
        assert data["size"] == tile_data["size"]
        assert data["coverage"] == tile_data["coverage"]
        assert data["box_packing"] == tile_data["box_packing"]
        assert "tile_id" in data
        
        self.test_tile_id = data["tile_id"]
        print(f"✓ Created tile: {data['tile_id']} - {data['size']}")
        return data
    
    def test_get_tiles(self):
        """Test getting all tiles"""
        response = requests.get(f"{BASE_URL}/api/tiles")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Retrieved {len(data)} tiles")
        return data
    
    def test_update_tile(self):
        """Test updating a tile"""
        # First create a tile
        tile_data = {
            "size": "TEST_UPDATE_800x800mm",
            "coverage": 30.0,
            "box_packing": 3
        }
        create_response = requests.post(f"{BASE_URL}/api/tiles", json=tile_data)
        assert create_response.status_code == 200
        tile_id = create_response.json()["tile_id"]
        self.test_tile_id = tile_id
        
        # Update the tile
        update_data = {
            "coverage": 35.5,
            "box_packing": 5
        }
        update_response = requests.put(f"{BASE_URL}/api/tiles/{tile_id}", json=update_data)
        assert update_response.status_code == 200
        
        updated_tile = update_response.json()
        assert updated_tile["coverage"] == 35.5
        assert updated_tile["box_packing"] == 5
        print(f"✓ Updated tile: {tile_id}")
    
    def test_delete_tile(self):
        """Test soft deleting a tile - CRITICAL TEST"""
        # First create a tile
        tile_data = {
            "size": "TEST_DELETE_900x900mm",
            "coverage": 25.0,
            "box_packing": 4
        }
        create_response = requests.post(f"{BASE_URL}/api/tiles", json=tile_data)
        assert create_response.status_code == 200
        tile_id = create_response.json()["tile_id"]
        
        # Delete the tile
        delete_response = requests.delete(f"{BASE_URL}/api/tiles/{tile_id}")
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        
        delete_data = delete_response.json()
        assert "message" in delete_data
        assert "deleted" in delete_data["message"].lower() or "success" in delete_data["message"].lower()
        print(f"✓ Deleted tile: {tile_id} - {delete_data}")
        
        # Verify tile is no longer in the list (soft deleted)
        get_response = requests.get(f"{BASE_URL}/api/tiles")
        tiles = get_response.json()
        tile_ids = [t["tile_id"] for t in tiles]
        assert tile_id not in tile_ids, "Deleted tile should not appear in list"
        print(f"✓ Verified tile {tile_id} is not in active tiles list")
    
    def test_delete_nonexistent_tile(self):
        """Test deleting a tile that doesn't exist"""
        fake_id = "nonexistent-tile-id-12345"
        response = requests.delete(f"{BASE_URL}/api/tiles/{fake_id}")
        assert response.status_code == 404
        print(f"✓ Correctly returned 404 for nonexistent tile")


class TestCustomersCRUD:
    """Customers CRUD operations tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.test_customer_id = None
        yield
        # Cleanup
        if self.test_customer_id:
            try:
                requests.delete(f"{BASE_URL}/api/customers/{self.test_customer_id}")
            except:
                pass
    
    def test_create_customer(self):
        """Test creating a new customer"""
        customer_data = {
            "name": "TEST_Customer_John",
            "phone": "9876543210",
            "address": "123 Test Street, Test City",
            "gstin": "TEST123456789"
        }
        response = requests.post(f"{BASE_URL}/api/customers", json=customer_data)
        assert response.status_code == 200, f"Failed to create customer: {response.text}"
        
        data = response.json()
        assert data["name"] == customer_data["name"]
        assert data["phone"] == customer_data["phone"]
        assert "customer_id" in data
        
        self.test_customer_id = data["customer_id"]
        print(f"✓ Created customer: {data['customer_id']} - {data['name']}")
        return data
    
    def test_get_customers(self):
        """Test getting all customers"""
        response = requests.get(f"{BASE_URL}/api/customers")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Retrieved {len(data)} customers")
        return data
    
    def test_update_customer(self):
        """Test updating a customer"""
        # First create a customer
        customer_data = {
            "name": "TEST_Update_Customer",
            "phone": "1234567890",
            "address": "Old Address"
        }
        create_response = requests.post(f"{BASE_URL}/api/customers", json=customer_data)
        assert create_response.status_code == 200
        customer_id = create_response.json()["customer_id"]
        self.test_customer_id = customer_id
        
        # Update the customer
        update_data = {
            "name": "TEST_Updated_Customer",
            "address": "New Updated Address"
        }
        update_response = requests.put(f"{BASE_URL}/api/customers/{customer_id}", json=update_data)
        assert update_response.status_code == 200
        
        updated_customer = update_response.json()
        assert updated_customer["name"] == "TEST_Updated_Customer"
        assert updated_customer["address"] == "New Updated Address"
        print(f"✓ Updated customer: {customer_id}")
    
    def test_delete_customer(self):
        """Test soft deleting a customer - CRITICAL TEST"""
        # First create a customer
        customer_data = {
            "name": "TEST_Delete_Customer",
            "phone": "5555555555",
            "address": "Delete Test Address"
        }
        create_response = requests.post(f"{BASE_URL}/api/customers", json=customer_data)
        assert create_response.status_code == 200
        customer_id = create_response.json()["customer_id"]
        
        # Delete the customer
        delete_response = requests.delete(f"{BASE_URL}/api/customers/{customer_id}")
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        
        delete_data = delete_response.json()
        assert "message" in delete_data
        print(f"✓ Deleted customer: {customer_id} - {delete_data}")
        
        # Verify customer is no longer in the list
        get_response = requests.get(f"{BASE_URL}/api/customers")
        customers = get_response.json()
        customer_ids = [c["customer_id"] for c in customers]
        assert customer_id not in customer_ids, "Deleted customer should not appear in list"
        print(f"✓ Verified customer {customer_id} is not in active customers list")
    
    def test_delete_nonexistent_customer(self):
        """Test deleting a customer that doesn't exist"""
        fake_id = "nonexistent-customer-id-12345"
        response = requests.delete(f"{BASE_URL}/api/customers/{fake_id}")
        assert response.status_code == 404
        print(f"✓ Correctly returned 404 for nonexistent customer")


class TestInvoicesCRUD:
    """Invoices CRUD operations tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data - create customer and tile first"""
        # Create a test customer
        customer_data = {
            "name": "TEST_Invoice_Customer",
            "phone": "1111111111",
            "address": "Invoice Test Address"
        }
        response = requests.post(f"{BASE_URL}/api/customers", json=customer_data)
        if response.status_code == 200:
            self.test_customer_id = response.json()["customer_id"]
        else:
            # Use existing customer
            customers = requests.get(f"{BASE_URL}/api/customers").json()
            if customers:
                self.test_customer_id = customers[0]["customer_id"]
            else:
                pytest.skip("No customers available for invoice testing")
        
        # Create a test tile
        tile_data = {
            "size": "TEST_INVOICE_600x600mm",
            "coverage": 23.68,
            "box_packing": 4
        }
        response = requests.post(f"{BASE_URL}/api/tiles", json=tile_data)
        if response.status_code == 200:
            self.test_tile_size = response.json()["size"]
        else:
            # Use existing tile
            tiles = requests.get(f"{BASE_URL}/api/tiles").json()
            if tiles:
                self.test_tile_size = tiles[0]["size"]
            else:
                self.test_tile_size = "600x600mm"
        
        self.test_invoice_id = None
        yield
        
        # Cleanup
        if self.test_invoice_id:
            try:
                requests.delete(f"{BASE_URL}/api/invoices/{self.test_invoice_id}")
            except:
                pass
    
    def test_create_invoice(self):
        """Test creating a new invoice"""
        invoice_data = {
            "customer_id": self.test_customer_id,
            "line_items": [
                {
                    "location": "Test Room",
                    "tile_name": "Test Tile",
                    "size": self.test_tile_size,
                    "box_qty": 5,
                    "extra_sqft": 0,
                    "rate_per_sqft": 50,
                    "rate_per_box": 0,
                    "discount_percent": 0,
                    "coverage": 23.68,
                    "box_packing": 4
                }
            ],
            "transport_charges": 500,
            "unloading_charges": 200,
            "amount_paid": 0,
            "status": "Draft"
        }
        response = requests.post(f"{BASE_URL}/api/invoices", json=invoice_data)
        assert response.status_code == 200, f"Failed to create invoice: {response.text}"
        
        data = response.json()
        assert "invoice_id" in data
        assert data["customer_id"] == self.test_customer_id
        assert len(data["line_items"]) == 1
        
        self.test_invoice_id = data["invoice_id"]
        print(f"✓ Created invoice: {data['invoice_id']}")
        return data
    
    def test_get_invoices(self):
        """Test getting all invoices"""
        response = requests.get(f"{BASE_URL}/api/invoices")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Retrieved {len(data)} invoices")
        return data
    
    def test_delete_invoice(self):
        """Test soft deleting an invoice - CRITICAL TEST"""
        # First create an invoice
        invoice_data = {
            "customer_id": self.test_customer_id,
            "line_items": [
                {
                    "location": "Delete Test Room",
                    "tile_name": "Delete Test Tile",
                    "size": self.test_tile_size,
                    "box_qty": 2,
                    "extra_sqft": 0,
                    "rate_per_sqft": 40,
                    "rate_per_box": 0,
                    "discount_percent": 0,
                    "coverage": 23.68,
                    "box_packing": 4
                }
            ],
            "transport_charges": 0,
            "unloading_charges": 0,
            "amount_paid": 0,
            "status": "Draft"
        }
        create_response = requests.post(f"{BASE_URL}/api/invoices", json=invoice_data)
        assert create_response.status_code == 200
        invoice_id = create_response.json()["invoice_id"]
        
        # Delete the invoice
        # URL encode the invoice_id since it contains slashes
        import urllib.parse
        encoded_invoice_id = urllib.parse.quote(invoice_id, safe='')
        delete_response = requests.delete(f"{BASE_URL}/api/invoices/{encoded_invoice_id}")
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        
        delete_data = delete_response.json()
        assert "message" in delete_data
        print(f"✓ Deleted invoice: {invoice_id} - {delete_data}")
        
        # Verify invoice is no longer in the list
        get_response = requests.get(f"{BASE_URL}/api/invoices")
        invoices = get_response.json()
        invoice_ids = [i["invoice_id"] for i in invoices]
        assert invoice_id not in invoice_ids, "Deleted invoice should not appear in list"
        print(f"✓ Verified invoice {invoice_id} is not in active invoices list")
    
    def test_delete_nonexistent_invoice(self):
        """Test deleting an invoice that doesn't exist"""
        fake_id = "TTS-999-9999-99"
        import urllib.parse
        encoded_id = urllib.parse.quote(fake_id, safe='')
        response = requests.delete(f"{BASE_URL}/api/invoices/{encoded_id}")
        assert response.status_code == 404
        print(f"✓ Correctly returned 404 for nonexistent invoice")


class TestPDFGeneration:
    """PDF generation tests"""
    
    def test_pdf_download(self):
        """Test PDF download for an existing invoice"""
        import urllib.parse
        
        # Get existing invoices
        response = requests.get(f"{BASE_URL}/api/invoices")
        assert response.status_code == 200
        invoices = response.json()
        
        if not invoices:
            pytest.skip("No invoices available for PDF testing")
        
        # Try each invoice until we find one that works
        for invoice in invoices:
            invoice_id = invoice["invoice_id"]
            encoded_id = urllib.parse.quote(invoice_id, safe='')
            
            # Download PDF
            pdf_response = requests.get(f"{BASE_URL}/api/invoices/{encoded_id}/pdf")
            if pdf_response.status_code == 200:
                assert pdf_response.headers.get('content-type') == 'application/pdf'
                assert len(pdf_response.content) > 0
                print(f"✓ PDF downloaded successfully for invoice {invoice_id} - Size: {len(pdf_response.content)} bytes")
                return
        
        pytest.fail("No valid invoice found for PDF download")
    
    def test_public_pdf_endpoint(self):
        """Test public PDF endpoint for WhatsApp sharing"""
        # Get existing invoices
        response = requests.get(f"{BASE_URL}/api/invoices")
        assert response.status_code == 200
        invoices = response.json()
        
        if not invoices:
            pytest.skip("No invoices available for PDF testing")
        
        invoice_id = invoices[0]["invoice_id"]
        import urllib.parse
        encoded_id = urllib.parse.quote(invoice_id, safe='')
        
        # Test public PDF endpoint
        pdf_response = requests.get(f"{BASE_URL}/api/public/invoices/{encoded_id}/pdf")
        assert pdf_response.status_code == 200, f"Public PDF download failed: {pdf_response.text}"
        assert pdf_response.headers.get('content-type') == 'application/pdf'
        print(f"✓ Public PDF endpoint working for invoice {invoice_id}")


class TestWhatsAppSharePreparation:
    """Tests to verify WhatsApp share functionality prerequisites"""
    
    def test_invoice_has_required_fields_for_whatsapp(self):
        """Verify invoice has all fields needed for WhatsApp message"""
        response = requests.get(f"{BASE_URL}/api/invoices")
        assert response.status_code == 200
        invoices = response.json()
        
        if not invoices:
            pytest.skip("No invoices available for WhatsApp testing")
        
        invoice = invoices[0]
        
        # Check required fields for WhatsApp message
        required_fields = [
            "invoice_id",
            "customer_name",
            "customer_phone",
            "grand_total",
            "amount_paid",
            "pending_balance",
            "status"
        ]
        
        for field in required_fields:
            assert field in invoice, f"Missing required field: {field}"
            print(f"✓ Field '{field}' present: {invoice[field]}")
        
        print(f"✓ Invoice has all required fields for WhatsApp sharing")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
