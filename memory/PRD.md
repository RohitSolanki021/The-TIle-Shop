# Tile Shop Invoicing System - PRD

## Original Problem Statement
Build a production-ready Tile Shop Invoicing system with:
- Tile Master management (Size, Coverage, Box Packing - simplified)
- Customer Master (Name, Phone, Address, GSTIN, auto-computed TotalPending)
- Invoice creation with sequential InvoiceID, Date, Status
- Invoice Line Items: Location, Tile Name (manual), Size (select), BoxQty, ExtraSqft, RatePerSqft, RatePerBox (bidirectional), DiscountPercent
- Compulsory photo upload/capture for each tile item
- Transport and Unloading Charges
- PDF generation matching RANGOLI template
- WhatsApp sharing with downloadable PDF link

## User's Preferred Language
English

## Tech Stack
- **Frontend**: React, Tailwind CSS
- **Backend**: FastAPI (Python)
- **Database**: MongoDB (via motor async driver)
- **PDF Generation**: ReportLab

## What's Implemented (Feb 1, 2026)

### Core Features - COMPLETE ✅
1. **Tiles Management** (Simplified)
   - Only 3 fields: Size, Coverage (sqft/box), Box Packing (tiles/box)
   - Removed: Product Name, Rate per Sqft, Rate per Box

2. **Customers Management**
   - CRUD operations
   - Auto-computed total_pending balance
   - Soft delete implementation

3. **Invoices Management**
   - Create/Edit/Delete invoices
   - New line item structure:
     - Tile Name (manual text entry)
     - Size (select from existing tiles)
     - Auto-fetch Coverage & Box Packing when size selected
     - Rate per Sqft OR Rate per Box (bidirectional calculation)
   - Real-time cost calculations

4. **PDF Generation**
   - Professional layout matching RANGOLI template
   - Column headers: SR., IMAGE, SKU, SIZE, BOX, SQFT, RATE, BOX RATE, DISC, AMOUNT
   - Rupee symbol (₹) rendering via DejaVuSans font
   - Embedded tile images
   - No text overlapping

5. **WhatsApp Sharing**
   - Public PDF download endpoint
   - Pre-filled WhatsApp message

### Recent Changes (Feb 1, 2026)
1. **Tiles Management Simplified**
   - Only Size, Coverage, Box Packing fields
   - Removed Product Name, rates from tile master

2. **Invoice Line Item Restructured**
   - Tile Name: Manual text entry
   - Size: Dropdown from existing tiles (auto-fetches coverage & box_packing)
   - Rate per Sqft ↔ Rate per Box: Bidirectional calculation
   - Coverage auto-populated when size selected

## API Endpoints
- `POST/GET /api/tiles` - Tile CRUD (simplified)
- `GET /api/tiles/by-size/{size}` - Get tile by size for auto-population
- `POST/GET /api/customers` - Customer CRUD
- `POST/GET /api/invoices` - Invoice CRUD
- `GET /api/invoices/{id}/pdf` - Download PDF
- `GET /api/public/invoices/{id}/pdf` - Public PDF (for WhatsApp)

## Database Schema
- **tiles**: { tile_id, size, coverage, box_coverage_sqft, box_packing, deleted }
- **customers**: { customer_id, name, phone, address, gstin, total_pending, deleted }
- **invoices**: { invoice_id, customer_id, customer_name, line_items[], transport_charges, unloading_charges, grand_total, pending_balance, deleted }
- **InvoiceLineItem**: { location, tile_name, tile_image, size, box_qty, extra_sqft, rate_per_sqft, rate_per_box, discount_percent, coverage, box_packing, total_sqft, final_amount }

## Files Structure
```
/app/
├── backend/
│   ├── server.py (all APIs and PDF generation)
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.js (React app)
    │   └── App.css
    └── package.json
```

## Future Tasks / Backlog
1. **UI/UX Improvements** - Make web UI more "elegant" and professional
2. **Codebase Refactoring** - Split monolithic App.js into components
