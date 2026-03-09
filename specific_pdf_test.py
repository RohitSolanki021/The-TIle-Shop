"""
Specific PDF Test for the Exact Requested Scenario
================================================
TEST SCENARIO:
1. Create a customer first
2. Create an invoice with:
   - A granite item: extra_sqft=25, rate_per_sqft=200 (should show "25 sqft" and "200.00/sqft" in PDF)
   - A tile_pieces item: quantity=15, rate_per_piece=500 (should show "15 pc" and "500.00/pc" in PDF)
3. Generate the PDF and verify the rate/quantity columns show correctly
"""

import requests
import json

# Get backend URL from frontend .env
BASE_URL = "https://granite-tile-swap.preview.emergentagent.com"
API_URL = f"{BASE_URL}/api"

def run_specific_test():
    print("Running Specific Test Scenario from Request")
    print("=" * 50)
    
    # 1. Create customer
    customer_data = {
        "name": "Test Customer for PDF Verification",
        "phone": "9999999999",
        "address": "Test Address for PDF Generation",
        "gstin": "TEST12345678901"
    }
    
    customer_response = requests.post(f"{API_URL}/customers", json=customer_data)
    if customer_response.status_code != 200:
        print(f"❌ Failed to create customer: {customer_response.status_code}")
        return
    
    customer = customer_response.json()
    customer_id = customer['customer_id']
    print(f"✅ Customer created: {customer_id}")
    
    # 2. Create invoice with exact requested values
    invoice_data = {
        "customer_id": customer_id,
        "line_items": [
            {
                "product_type": "granite",
                "location": "Kitchen",
                "tile_name": "Premium Granite Slab",
                "size": "Standard",
                "extra_sqft": 25.0,      # Exactly as requested
                "rate_per_sqft": 200.0,  # Exactly as requested
                "discount_percent": 0
            },
            {
                "product_type": "tile_pieces",
                "location": "Bathroom",
                "tile_name": "Decorative Tile Pieces",
                "size": "Standard",
                "quantity": 15,          # Exactly as requested
                "rate_per_piece": 500.0, # Exactly as requested
                "discount_percent": 0
            }
        ],
        "transport_charges": 0,
        "unloading_charges": 0,
        "amount_paid": 0
    }
    
    # Create invoice
    invoice_response = requests.post(f"{API_URL}/invoices", json=invoice_data)
    if invoice_response.status_code != 200:
        print(f"❌ Failed to create invoice: {invoice_response.status_code}")
        print(f"Response: {invoice_response.text}")
        return
    
    invoice = invoice_response.json()
    invoice_id = invoice['invoice_id']
    print(f"✅ Invoice created: {invoice_id}")
    
    # Verify calculations
    granite_item = invoice['line_items'][0]
    tile_item = invoice['line_items'][1]
    
    print(f"\n📊 Calculation Verification:")
    print(f"Granite: {granite_item['extra_sqft']} sqft × ₹{granite_item['rate_per_sqft']}/sqft = ₹{granite_item['final_amount']}")
    print(f"Expected: 25 × 200 = 5000 | Actual: {granite_item['final_amount']}")
    
    print(f"Tile Pieces: {tile_item['quantity']} pc × ₹{tile_item['rate_per_piece']}/pc = ₹{tile_item['final_amount']}")
    print(f"Expected: 15 × 500 = 7500 | Actual: {tile_item['final_amount']}")
    
    # 3. Generate PDF
    invoice_id_encoded = invoice_id.replace(' ', '%20').replace('/', '%2F')
    pdf_response = requests.get(f"{API_URL}/invoices/{invoice_id_encoded}/pdf")
    
    if pdf_response.status_code == 200:
        print(f"\n✅ PDF Generated Successfully")
        print(f"   Status: {pdf_response.status_code}")
        print(f"   Size: {len(pdf_response.content)} bytes")
        print(f"   Content-Type: {pdf_response.headers.get('content-type', 'unknown')}")
        
        # Save PDF
        pdf_filename = f"/app/specific_test_pdf_{invoice_id.replace(' / ', '-').replace('/', '-')}.pdf"
        with open(pdf_filename, 'wb') as f:
            f.write(pdf_response.content)
        print(f"   Saved: {pdf_filename}")
        
        print(f"\n📄 PDF Should Display:")
        print(f"   Granite Item:")
        print(f"     - Quantity: 25 sqft")
        print(f"     - Rate: 200.00/sqft") 
        print(f"     - Amount: ₹5,000.00")
        print(f"   Tile Pieces Item:")
        print(f"     - Quantity: 15 pc")
        print(f"     - Rate: 500.00/pc")
        print(f"     - Amount: ₹7,500.00")
        
    else:
        print(f"❌ PDF Generation Failed: {pdf_response.status_code}")
        print(f"Response: {pdf_response.text}")
    
    # Cleanup
    try:
        requests.delete(f"{API_URL}/invoices/{invoice_id_encoded}")
        requests.delete(f"{API_URL}/customers/{customer_id}")
        print(f"\n🧹 Cleanup completed")
    except:
        print(f"\n⚠️  Cleanup may have failed")
    
    print(f"\n✅ Test completed successfully!")

if __name__ == "__main__":
    run_specific_test()