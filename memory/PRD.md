# The Tile Shop - Invoice Generation Application

## Original Problem Statement
Build and enhance an invoice generation application for The Tile Shop, a tile retail business. The primary goal is to create pixel-perfect PDF invoices that match a reference design provided by the user.

## Core Requirements
1. Implement a login page with credentials: `Thetileshop` / `Vicky123`
2. Replace JavaScript-based PDF engine with HTML-to-PDF generation using WeasyPrint
3. Create an exact replica of the user's reference invoice design
4. Include main company logo and 14 partner brand logos
5. All logos and images must be high quality
6. Proper table structure for all sections
7. Support sectioning of items (e.g., 'KITCHEN', 'BATHROOM')
8. Updated Terms & Conditions with user-provided text

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
- `GET /api/public/invoices/{invoice_id}/pdf` - Public PDF endpoint

## Database Schema
- **customers**: `{ customer_id, name, address, gstin }`
- **tiles**: `{ tile_id, name, size, image_url }`
- **invoices**: `{ invoice_id, customer_id, date, reference_name, line_items: [{tile_id, quantity, rate, section}] }`

## What's Been Implemented (Feb 13, 2026)

### Authentication System
- ✅ Login/Logout flow for frontend application
- ✅ Credentials: `Thetileshop` / `Vicky123`

### PDF Generation System
- ✅ Migrated from reportlab to WeasyPrint + Jinja2
- ✅ HTML template (`invoice_template_new.html`) with:
  - White background
  - High-quality main logo (crisp, not blurry)
  - Full-width tables with proper structure
  - Section headers with brown background
  - Section totals with beige background
  - Highlighted Final Amount row
  - Bank details table
  - Terms & Conditions section
  - 14 partner brand logos at bottom

### Invoice Features
- ✅ Buyer (Bill To) / Consignee (Ship To) sections
- ✅ Item sections (KITCHEN, BATHROOM, etc.)
- ✅ Rate per box / Rate per sqft columns
- ✅ Discount percentage column
- ✅ Transport and unloading charges
- ✅ GST amount calculation
- ✅ Overall remarks section

## Login Credentials
- **Username**: `Thetileshop`
- **Password**: `Vicky123`

## Known Issues & Solutions
- **WeasyPrint dependency crash**: If backend fails to start, reinstall with:
  ```bash
  sudo apt-get install --reinstall libpangoft2-1.0-0 libpango-1.0-0 libpangocairo-1.0-0
  ```

## Future Tasks / Backlog
- [ ] Delete obsolete PDF engine files (pdfEngine.js, pdfEngine.py)
- [ ] Add product images to invoice items
- [ ] Email invoice functionality
- [ ] Invoice status tracking (Draft/Sent/Paid)
