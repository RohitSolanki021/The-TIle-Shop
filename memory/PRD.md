# The Tile Shop - Invoicing System PRD

## Original Problem Statement
1. Clone GitHub repository: https://github.com/RohitSolanki021/The-Tile-Shop
2. Integrate logo and color scheme (#fef7f7 background, brown tones)
3. Implement PDF invoice generation that EXACTLY matches reference template

## Tech Stack
- **Frontend:** React 19, TailwindCSS, Lucide Icons
- **Backend:** FastAPI, MongoDB, ReportLab (PDF generation)
- **Styling:** Custom CSS with brand variables

## What's Been Implemented (Feb 7, 2026)

### Phase 1: Repository Clone & Branding
- ✅ Cloned full Tile Shop Invoicing application from GitHub
- ✅ Logo integrated from customer assets
- ✅ Brand color scheme applied throughout (#fef7f7, #5a3825, #6b4a35)

### Phase 2: PDF Template Implementation
- ✅ PDF generation rewritten to match THE TILE SHOP reference template
- ✅ Company header with logo, address, contact, GSTIN
- ✅ Quotation box with number, date, reference name
- ✅ Buyer (Bill To) and Consignee (Ship To) sections
- ✅ Items table with columns: SR NO., NAME, IMAGE, SIZE, RATE/BOX, RATE/SQFT, QUANTITY, DISC.(%), AMOUNT
- ✅ Location grouping with subtotals
- ✅ GST calculation
- ✅ Overall Remarks section
- ✅ Bank Details (HDFC Bank - SHREE SONANA SHETRPAL CERAMIC)
- ✅ Terms & Conditions (9 points from template)
- ✅ Footer with thank you message

### New Optional Fields Added
| Field | Type | Description |
|-------|------|-------------|
| reference_name | string | Reference person name |
| consignee_name | string | Ship To name |
| consignee_phone | string | Ship To phone |
| consignee_address | string | Ship To address |
| overall_remarks | string | Additional notes |
| gst_percent | float | GST percentage (calculates gst_amount) |

### Frontend Updates
- ✅ Advanced Fields toggle in invoice form
- ✅ Reference Name, GST %, Consignee section, Overall Remarks inputs
- ✅ Real-time GST calculation in invoice summary
- ✅ All fields optional and gracefully hidden if empty in PDF

## API Endpoints
- POST /api/invoices - Create invoice with optional fields
- GET /api/invoices/{id}/pdf - Download PDF matching template
- PUT /api/invoices/{id} - Update invoice
- GET /api/invoices - List all invoices

## Testing Status
- ✅ All API endpoints tested (100% pass)
- ✅ PDF generation verified with text extraction
- ✅ Frontend UI tested (advanced fields toggle, form inputs)
- ✅ GST calculation verified

## Next Action Items
- None specified

## Future/Backlog
- Add tile images to PDF when uploaded
- Multiple page PDF support for large invoices
- Email invoice directly to customer
- Inventory management integration
