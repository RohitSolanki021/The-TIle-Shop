# The Tile Shop - Invoice Generation Application

## Original Problem Statement
Build and enhance an invoice generation application for The Tile Shop, a tile and granite retail business. The primary goal is to create pixel-perfect PDF invoices that match a reference design provided by the user.

## Core Requirements
1. Implement a login page with credentials: `Thetileshop` / `Vicky123`
2. Replace JavaScript-based PDF engine with HTML-to-PDF generation using WeasyPrint
3. Create an exact replica of the user's reference invoice design
4. Include main company logo and 14 partner brand logos
5. All logos and images must be high quality
6. Proper table structure for all sections
7. Support sectioning of items (e.g., 'KITCHEN', 'BATHROOM')
8. Updated Terms & Conditions with user-provided text
9. **Support multiple product types**: Tiles (Box), Tile Pieces, Granites

## Tech Stack
- **Frontend**: React
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **PDF Generation**: WeasyPrint + Jinja2 (HTML-to-PDF)
- **System Dependencies**: libpangoft2-1.0-0, libpango-1.0-0, poppler-utils

## Architecture
```
/app/
├── backend/
│   ├── assets/
│   │   ├── brand_logos/      # 14 partner logos + main_logo.png
│   │   └── pdf/
│   │       ├── htmlPdfEngine.py       # PDF generation logic
│   │       ├── invoice_template_new.html  # HTML template
│   │       └── load_logos.py          # Logo loader
│   ├── pdfs/                 # Generated PDFs output
│   └── main.py               # FastAPI application
├── frontend/
│   └── src/
│       ├── components/
│       │   └── Login.js
│       └── App.js
```

## Key API Endpoints
- `POST /api/invoices` - Create new invoice
- `GET /api/invoices/{invoice_id}/pdf` - Generate and download PDF
- `GET /api/granites` - Get all granites
- `POST /api/granites` - Create new granite
- `PUT /api/granites/{granite_id}` - Update granite
- `DELETE /api/granites/{granite_id}` - Delete granite

## Database Schema
- **customers**: `{ customer_id, name, phone, address, gstin, total_pending }`
- **tiles**: `{ tile_id, size, coverage, box_packing, active }`
- **granites**: `{ granite_id, name, size, thickness, color, rate_per_piece, rate_per_sqft, active }`
- **invoices**: `{ invoice_id, customer_id, line_items: [{product_type, ...}], transport_charges, ... }`

## Product Types in Invoices
- **tiles_box**: Tiles sold by box - uses size dropdown, box qty, coverage (sqft/box), rate per sqft/box
- **tile_pieces**: Individual tiles not in boxes - manual sqft entry, rate per sqft
- **granite**: Granite slabs - quantity (pieces), rate per piece

## What's Been Implemented

### Authentication System
- ✅ Login/Logout flow for frontend application
- ✅ Credentials: `Thetileshop` / `Vicky123`

### PDF Generation System
- ✅ Migrated from reportlab to WeasyPrint + Jinja2
- ✅ HTML template with proper table structure
- ✅ Support for different product types in PDF output

### Invoice Features
- ✅ Buyer (Bill To) / Consignee (Ship To) sections
- ✅ Item sections (KITCHEN, BATHROOM, etc.)
- ✅ Rate per box / Rate per sqft columns
- ✅ Discount percentage column
- ✅ Transport and unloading charges
- ✅ GST amount calculation
- ✅ Overall remarks section

### Granites Management (Mar 5, 2026)
- ✅ Dashboard shows Granites in sidebar navigation
- ✅ Dashboard shows Granites stat card with count
- ✅ Granites Management page with CRUD operations
- ✅ Granite fields: Name, Size (L x W), Thickness, Color, Rate/Piece, Rate/Sqft
- ✅ Search functionality for granites

### Multi-Product Type Invoice (Mar 5, 2026)
- ✅ Product Type selector in invoice creation: Tiles (Box), Tile Pieces, Granite
- ✅ Dynamic form fields based on product type
- ✅ Tiles (Box): Size dropdown, Box Qty, Extra Sqft, Rate/Sqft, Rate/Box
- ✅ Tile Pieces: Manual Size, Total Sqft, Rate/Sqft (no box calculations)
- ✅ Granite: Granite dropdown (select from saved), Size (L x W), Quantity (Pieces), Rate/Piece
- ✅ Line items table shows product type badge (Box/Tile Pcs/Granite)
- ✅ Real-time cost preview for all product types
- ✅ Backend calculation handles all product types
- ✅ PDF generation adapts to product type

## Login Credentials
- **Username**: `Thetileshop`
- **Password**: `Vicky123`

## Known Issues & Solutions
- **WeasyPrint dependency crash**: If backend fails to start, reinstall with:
  ```bash
  sudo apt-get install --reinstall libpangoft2-1.0-0 libpango-1.0-0 libpangocairo-1.0-0
  ```
- **PDF route 404**: Ensure PDF routes are defined BEFORE generic invoice routes in main.py

## Future Tasks / Backlog
- [ ] Delete obsolete PDF engine files (pdfEngine.js, pdfEngine.py)
- [ ] Add product images to invoice items
- [ ] Email invoice functionality
- [ ] Invoice status tracking improvements
- [ ] PHP backend for Hostinger deployment (partially completed in php_backend/)
