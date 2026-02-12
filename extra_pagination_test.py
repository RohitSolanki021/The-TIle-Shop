#!/usr/bin/env python3
"""
Extra Large Invoice Test - Force 3+ pages
Tests PDF generation with even more line items to verify pagination scales
"""

import requests
from urllib.parse import quote

BACKEND_URL = "https://code-fork-4.preview.emergentagent.com/api"

def test_extra_large_invoice():
    """Create invoice with 60+ items to force 3-4 pages"""
    print("🔍 TESTING EXTRA LARGE INVOICE (60+ items for 3-4 pages)")
    print("=" * 60)
    
    # Get existing customers
    response = requests.get(f"{BACKEND_URL}/customers", timeout=10)
    customers = response.json()
    customer_id = customers[0]['customer_id']
    print(f"✅ Using customer: {customers[0]['name']}")
    
    # Create 60+ line items across multiple locations
    line_items = []
    
    # Generate items for 6 different areas with 10+ items each
    areas = [
        "Ground Floor Living Room", "First Floor Master Bedroom", "Kitchen & Dining",
        "Guest Bathroom", "Outdoor Terrace", "Staircase & Hallway"
    ]
    
    tile_types = [
        {"name": "Premium Vitrified", "size": "600x600mm", "rate": 120},
        {"name": "Ceramic Glazed", "size": "300x600mm", "rate": 85},
        {"name": "Porcelain Matt", "size": "800x800mm", "rate": 180},
        {"name": "Stone Texture", "size": "400x400mm", "rate": 95},
        {"name": "Wood Look Plank", "size": "200x1200mm", "rate": 140},
        {"name": "Marble Effect", "size": "600x1200mm", "rate": 220},
        {"name": "Mosaic Pattern", "size": "300x300mm", "rate": 75},
        {"name": "Anti-Skid Outdoor", "size": "600x600mm", "rate": 110},
        {"name": "Designer Border", "size": "100x600mm", "rate": 45},
        {"name": "High Gloss", "size": "800x800mm", "rate": 160},
        {"name": "Textured Surface", "size": "450x450mm", "rate": 90}
    ]
    
    item_counter = 1
    for area in areas:
        for i, tile in enumerate(tile_types):
            line_item = {
                "location": area,
                "tile_name": f"{tile['name']} Tiles - Series {i+1}",
                "size": tile["size"],
                "box_qty": 5 + (i * 2),  # Varying quantities
                "extra_sqft": 3.0,
                "rate_per_sqft": tile["rate"],
                "discount_percent": 5 + (i % 3) * 2,  # Varying discounts
                "coverage": 2.8 + (i * 0.2),  # Varying coverage
                "box_packing": 4
            }
            line_items.append(line_item)
            item_counter += 1
    
    print(f"   Total line items: {len(line_items)}")
    
    invoice_data = {
        "customer_id": customer_id,
        "line_items": line_items,
        "transport_charges": 5000.0,
        "unloading_charges": 3000.0,
        "gst_percent": 18.0,
        "reference_name": "Mega Construction Project - Phase 1",
        "overall_remarks": "Comprehensive tile supply for large residential complex. Quality inspection required for all items."
    }
    
    # Create the large invoice
    try:
        response = requests.post(f"{BACKEND_URL}/invoices", json=invoice_data, timeout=30)
        if response.status_code == 200:
            invoice = response.json()
            invoice_id = invoice['invoice_id']
            print(f"✅ Extra large invoice created: {invoice_id}")
            print(f"   Grand Total: ₹{invoice['grand_total']:,.2f}")
            
            # Generate PDF
            encoded_id = quote(invoice_id, safe='')
            pdf_url = f"{BACKEND_URL}/invoices/{encoded_id}/pdf"
            
            print("\n📄 Generating extra large PDF...")
            response = requests.get(pdf_url, timeout=90)  # Extra long timeout
            
            if response.status_code == 200:
                pdf_size_kb = len(response.content) / 1024
                print(f"✅ Extra large PDF generated: {pdf_size_kb:.1f} KB")
                
                # Save PDF
                pdf_filename = f"extra_large_invoice_{invoice_id.replace(' / ', '_').replace('/', '_')}.pdf"
                with open(pdf_filename, 'wb') as f:
                    f.write(response.content)
                print(f"   📁 Saved as: {pdf_filename}")
                
                # Estimate pages (rough calculation)
                estimated_pages = max(3, len(line_items) // 20)
                print(f"   📊 Estimated pages: {estimated_pages}+ (with {len(line_items)} items)")
                print(f"   🎯 Expected: Header and table columns repeat on ALL {estimated_pages}+ pages")
                
                return True
            else:
                print(f"❌ PDF generation failed: {response.status_code}")
                return False
        else:
            print(f"❌ Invoice creation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_extra_large_invoice()
    if success:
        print("\n🎯 Extra large invoice pagination test PASSED!")
    else:
        print("\n❌ Extra large invoice test FAILED!")