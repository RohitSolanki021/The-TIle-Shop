from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Table, TableStyle
from PIL import Image
import io
import base64

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Register DejaVuSans font for Rupee symbol
try:
    font_path = ROOT_DIR / "fonts" / "DejaVuSans.ttf"
    if font_path.exists():
        pdfmetrics.registerFont(TTFont('DejaVuSans', str(font_path)))
        logger.info("DejaVuSans font registered successfully")
    else:
        logger.warning(f"DejaVuSans font not found at {font_path}")
except Exception as e:
    logger.error(f"Error registering font: {e}")

# ==================== MODELS ====================

class Tile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    tile_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    size: str  # e.g., "600x600mm", "800x800mm"
    coverage: float = Field(default=0)  # sqft per box (new field)
    box_coverage_sqft: float = Field(default=0)  # sqft per box (backward compat)
    box_packing: int = Field(default=0)  # number of tiles per box
    # Old fields kept for backward compatibility
    product_name: Optional[str] = None
    rate_per_sqft: Optional[float] = None
    rate_per_box: Optional[float] = None
    active: bool = True
    deleted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TileCreate(BaseModel):
    size: str
    coverage: float = Field(default=0)
    box_packing: int = Field(default=0)

class TileUpdate(BaseModel):
    size: Optional[str] = None
    coverage: Optional[float] = None
    box_packing: Optional[int] = None

class Customer(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    customer_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    phone: str
    address: str
    gstin: Optional[str] = None
    total_pending: float = 0.0
    deleted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CustomerCreate(BaseModel):
    name: str
    phone: str
    address: str
    gstin: Optional[str] = None

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    gstin: Optional[str] = None

class InvoiceLineItem(BaseModel):
    location: str
    tile_name: Optional[str] = None  # Manual text entry for tile name (new field)
    product_name: Optional[str] = None  # Kept for backward compatibility
    tile_image: Optional[str] = None  # Base64 encoded image
    size: str  # Selected from existing tile sizes
    box_qty: int = Field(ge=0)
    extra_sqft: float = Field(ge=0, default=0)
    rate_per_sqft: float = 0  # User enters this OR rate_per_box
    rate_per_box: float = 0  # Auto-calculated from rate_per_sqft or vice versa
    discount_percent: float = Field(ge=0, le=100, default=0)
    coverage: float = Field(ge=0, default=0)  # Auto-fetched from tile based on size
    box_coverage_sqft: float = Field(ge=0, default=0)  # Kept for backward compatibility
    box_packing: int = Field(ge=0, default=0)  # Auto-fetched from tile based on size
    # Calculated fields
    total_sqft: float = 0
    amount_before_discount: float = 0
    discount_amount: float = 0
    final_amount: float = 0

class Invoice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    invoice_id: str = Field(default_factory=lambda: f"QT-{str(uuid.uuid4())[:8].upper()}")
    invoice_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    customer_id: str
    customer_name: str = ""
    customer_phone: str = ""
    customer_address: str = ""
    customer_gstin: Optional[str] = None
    # New fields from template
    reference_name: Optional[str] = None  # Reference Name field
    consignee_name: Optional[str] = None  # Ship To name
    consignee_phone: Optional[str] = None  # Ship To phone
    consignee_address: Optional[str] = None  # Ship To address
    overall_remarks: Optional[str] = None  # Overall Remarks field
    gst_percent: float = 0.0  # GST percentage (0 if not applicable)
    gst_amount: float = 0.0  # Calculated GST amount
    status: str = "Draft"  # Draft, Sent, Paid, Cancelled
    line_items: List[InvoiceLineItem]
    transport_charges: float = 0.0
    unloading_charges: float = 0.0
    subtotal: float = 0.0
    grand_total: float = 0.0
    amount_paid: float = 0.0
    pending_balance: float = 0.0
    deleted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InvoiceCreate(BaseModel):
    customer_id: str
    line_items: List[InvoiceLineItem]
    transport_charges: float = 0.0
    unloading_charges: float = 0.0
    amount_paid: float = 0.0
    status: str = "Draft"
    # New optional fields
    reference_name: Optional[str] = None
    consignee_name: Optional[str] = None
    consignee_phone: Optional[str] = None
    consignee_address: Optional[str] = None
    overall_remarks: Optional[str] = None
    gst_percent: float = 0.0

class InvoiceUpdate(BaseModel):
    line_items: Optional[List[InvoiceLineItem]] = None
    transport_charges: Optional[float] = None
    unloading_charges: Optional[float] = None
    amount_paid: Optional[float] = None
    status: Optional[str] = None
    # New optional fields
    reference_name: Optional[str] = None
    consignee_name: Optional[str] = None
    consignee_phone: Optional[str] = None
    consignee_address: Optional[str] = None
    overall_remarks: Optional[str] = None
    gst_percent: Optional[float] = None

# ==================== HELPER FUNCTIONS ====================

def calculate_bidirectional_rate(coverage: float, rate_sqft: Optional[float], rate_box: Optional[float]):
    """Calculate missing rate based on the other - for invoice line items"""
    if coverage <= 0:
        return rate_sqft or 0, rate_box or 0
    
    if rate_sqft and rate_sqft > 0 and (not rate_box or rate_box == 0):
        rate_box = rate_sqft * coverage
    elif rate_box and rate_box > 0 and (not rate_sqft or rate_sqft == 0):
        rate_sqft = rate_box / coverage
    
    return rate_sqft or 0, rate_box or 0

def calculate_line_item(item: InvoiceLineItem) -> InvoiceLineItem:
    """Calculate all fields for a line item"""
    # Get coverage (support both old and new field names)
    coverage = item.coverage if item.coverage > 0 else item.box_coverage_sqft
    
    # Calculate bidirectional rates
    item.rate_per_sqft, item.rate_per_box = calculate_bidirectional_rate(
        coverage, item.rate_per_sqft, item.rate_per_box
    )
    
    # Calculate total sqft using coverage
    item.total_sqft = (item.box_qty * coverage) + item.extra_sqft
    
    # Calculate amount before discount
    item.amount_before_discount = item.total_sqft * item.rate_per_sqft
    
    # Calculate discount
    item.discount_amount = item.amount_before_discount * (item.discount_percent / 100)
    
    # Calculate final amount
    item.final_amount = item.amount_before_discount - item.discount_amount
    
    return item

def calculate_invoice_totals(invoice: Invoice) -> Invoice:
    """Calculate all invoice totals"""
    invoice.subtotal = sum(item.final_amount for item in invoice.line_items)
    invoice.grand_total = invoice.subtotal + invoice.transport_charges + invoice.unloading_charges
    invoice.pending_balance = invoice.grand_total - invoice.amount_paid
    invoice.updated_at = datetime.now(timezone.utc)
    return invoice

async def recalculate_customer_pending(customer_id: str):
    """Recalculate total pending for a customer from all their invoices"""
    try:
        # Get all non-deleted invoices for this customer
        invoices = await db.invoices.find({
            "customer_id": customer_id,
            "deleted": False
        }, {"_id": 0}).to_list(1000)
        
        # Sum up all pending balances
        total_pending = sum(invoice.get('pending_balance', 0) for invoice in invoices)
        
        # Update customer's total_pending
        await db.customers.update_one(
            {"customer_id": customer_id},
            {"$set": {"total_pending": total_pending}}
        )
        
        return total_pending
    except Exception as e:
        logger.error(f"Error recalculating customer pending: {e}")
        return 0

# ==================== TILES ENDPOINTS ====================

@api_router.post("/tiles", response_model=Tile)
async def create_tile(tile_input: TileCreate):
    """Create a new tile with Size, Coverage, and Box Packing"""
    try:
        tile = Tile(**tile_input.model_dump())
        doc = tile.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        
        await db.tiles.insert_one(doc)
        return tile
    except Exception as e:
        logger.error(f"Error creating tile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tiles", response_model=List[Tile])
async def get_tiles():
    """Get all tiles (excluding soft-deleted)"""
    try:
        query = {"deleted": False}
        
        tiles = await db.tiles.find(query, {"_id": 0}).to_list(1000)
        
        for tile in tiles:
            if isinstance(tile.get('created_at'), str):
                tile['created_at'] = datetime.fromisoformat(tile['created_at'])
        
        return tiles
    except Exception as e:
        logger.error(f"Error fetching tiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tiles/by-size/{size}")
async def get_tile_by_size(size: str):
    """Get tile details by size for auto-population in invoice"""
    try:
        tile = await db.tiles.find_one({"size": size, "deleted": False}, {"_id": 0})
        if not tile:
            raise HTTPException(status_code=404, detail="Tile with this size not found")
        
        return {
            "size": tile['size'],
            "coverage": tile.get('coverage', tile.get('box_coverage_sqft', 0)),
            "box_packing": tile.get('box_packing', 0)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching tile by size: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tiles/{tile_id}", response_model=Tile)
async def get_tile(tile_id: str):
    """Get a specific tile"""
    try:
        tile = await db.tiles.find_one({"tile_id": tile_id, "deleted": False}, {"_id": 0})
        if not tile:
            raise HTTPException(status_code=404, detail="Tile not found")
        
        if isinstance(tile.get('created_at'), str):
            tile['created_at'] = datetime.fromisoformat(tile['created_at'])
        
        return tile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching tile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/tiles/{tile_id}", response_model=Tile)
async def update_tile(tile_id: str, tile_update: TileUpdate):
    """Update a tile"""
    try:
        existing_tile = await db.tiles.find_one({"tile_id": tile_id, "deleted": False}, {"_id": 0})
        if not existing_tile:
            raise HTTPException(status_code=404, detail="Tile not found")
        
        update_data = tile_update.model_dump(exclude_unset=True)
        
        await db.tiles.update_one(
            {"tile_id": tile_id, "deleted": False},
            {"$set": update_data}
        )
        
        updated_tile = await db.tiles.find_one({"tile_id": tile_id}, {"_id": 0})
        if isinstance(updated_tile.get('created_at'), str):
            updated_tile['created_at'] = datetime.fromisoformat(updated_tile['created_at'])
        
        return updated_tile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/tiles/{tile_id}")
async def delete_tile(tile_id: str):
    """Soft delete a tile"""
    try:
        result = await db.tiles.update_one(
            {"tile_id": tile_id, "deleted": False},
            {"$set": {"deleted": True}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Tile not found")
        
        return {"message": "Tile deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CUSTOMERS ENDPOINTS ====================

@api_router.post("/customers", response_model=Customer)
async def create_customer(customer_input: CustomerCreate):
    """Create a new customer"""
    try:
        customer_dict = customer_input.model_dump()
        customer = Customer(**customer_dict)
        doc = customer.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        
        await db.customers.insert_one(doc)
        return customer
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/customers", response_model=List[Customer])
async def get_customers():
    """Get all customers (excluding soft-deleted)"""
    try:
        customers = await db.customers.find({"deleted": False}, {"_id": 0}).to_list(1000)
        
        for customer in customers:
            if isinstance(customer['created_at'], str):
                customer['created_at'] = datetime.fromisoformat(customer['created_at'])
        
        return customers
    except Exception as e:
        logger.error(f"Error fetching customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(customer_id: str):
    """Get a specific customer"""
    try:
        customer = await db.customers.find_one({"customer_id": customer_id, "deleted": False}, {"_id": 0})
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        if isinstance(customer['created_at'], str):
            customer['created_at'] = datetime.fromisoformat(customer['created_at'])
        
        return customer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/customers/{customer_id}", response_model=Customer)
async def update_customer(customer_id: str, customer_update: CustomerUpdate):
    """Update a customer"""
    try:
        existing_customer = await db.customers.find_one({"customer_id": customer_id, "deleted": False}, {"_id": 0})
        if not existing_customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        update_data = customer_update.model_dump(exclude_unset=True)
        
        await db.customers.update_one(
            {"customer_id": customer_id, "deleted": False},
            {"$set": update_data}
        )
        
        updated_customer = await db.customers.find_one({"customer_id": customer_id}, {"_id": 0})
        if isinstance(updated_customer['created_at'], str):
            updated_customer['created_at'] = datetime.fromisoformat(updated_customer['created_at'])
        
        return updated_customer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str):
    """Soft delete a customer"""
    try:
        result = await db.customers.update_one(
            {"customer_id": customer_id, "deleted": False},
            {"$set": {"deleted": True}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return {"message": "Customer deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== INVOICES ENDPOINTS ====================

@api_router.post("/invoices", response_model=Invoice)
async def create_invoice(invoice_input: InvoiceCreate):
    """Create a new invoice with calculations"""
    try:
        # Fetch customer details
        customer = await db.customers.find_one({"customer_id": invoice_input.customer_id, "deleted": False}, {"_id": 0})
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Calculate line items
        calculated_items = []
        for item in invoice_input.line_items:
            # Get coverage (support both old and new field names)
            coverage = item.coverage if item.coverage > 0 else item.box_coverage_sqft
            if coverage <= 0:
                # If coverage not provided, try to fetch from tile by size
                tile = await db.tiles.find_one(
                    {"size": item.size, "deleted": False},
                    {"_id": 0}
                )
                if tile:
                    coverage = tile.get('coverage', tile.get('box_coverage_sqft', 0))
                    item.coverage = coverage
                    item.box_packing = tile.get('box_packing', 0)
            
            calculated_item = calculate_line_item(item)
            calculated_items.append(calculated_item)
        
        # Create invoice
        invoice_dict = invoice_input.model_dump()
        invoice_dict['line_items'] = [item.model_dump() for item in calculated_items]
        invoice_dict['customer_name'] = customer['name']
        invoice_dict['customer_phone'] = customer['phone']
        invoice_dict['customer_address'] = customer['address']
        invoice_dict['customer_gstin'] = customer.get('gstin')
        
        invoice = Invoice(**invoice_dict)
        invoice = calculate_invoice_totals(invoice)
        
        doc = invoice.model_dump()
        doc['invoice_date'] = doc['invoice_date'].isoformat()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        
        await db.invoices.insert_one(doc)
        
        # Recalculate customer total_pending from all invoices
        await recalculate_customer_pending(invoice_input.customer_id)
        
        return invoice
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/invoices", response_model=List[Invoice])
async def get_invoices():
    """Get all invoices (excluding soft-deleted)"""
    try:
        invoices = await db.invoices.find({"deleted": False}, {"_id": 0}).to_list(1000)
        
        for invoice in invoices:
            if isinstance(invoice['invoice_date'], str):
                invoice['invoice_date'] = datetime.fromisoformat(invoice['invoice_date'])
            if isinstance(invoice['created_at'], str):
                invoice['created_at'] = datetime.fromisoformat(invoice['created_at'])
            if isinstance(invoice['updated_at'], str):
                invoice['updated_at'] = datetime.fromisoformat(invoice['updated_at'])
        
        return invoices
    except Exception as e:
        logger.error(f"Error fetching invoices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/invoices/{invoice_id}", response_model=Invoice)
async def get_invoice(invoice_id: str):
    """Get a specific invoice"""
    try:
        invoice = await db.invoices.find_one({"invoice_id": invoice_id, "deleted": False}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        if isinstance(invoice['invoice_date'], str):
            invoice['invoice_date'] = datetime.fromisoformat(invoice['invoice_date'])
        if isinstance(invoice['created_at'], str):
            invoice['created_at'] = datetime.fromisoformat(invoice['created_at'])
        if isinstance(invoice['updated_at'], str):
            invoice['updated_at'] = datetime.fromisoformat(invoice['updated_at'])
        
        return invoice
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/invoices/{invoice_id}", response_model=Invoice)
async def update_invoice(invoice_id: str, invoice_update: InvoiceUpdate):
    """Update an invoice (block if status is Paid)"""
    try:
        existing_invoice = await db.invoices.find_one({"invoice_id": invoice_id, "deleted": False}, {"_id": 0})
        if not existing_invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Block editing if invoice is Paid
        if existing_invoice['status'] == 'Paid':
            raise HTTPException(status_code=403, detail="Cannot edit a Paid invoice")
        
        update_data = invoice_update.model_dump(exclude_unset=True)
        
        # Recalculate if line_items are updated
        if 'line_items' in update_data:
            calculated_items = []
            for item_dict in update_data['line_items']:
                item = InvoiceLineItem(**item_dict)
                # Get coverage (support both old and new field names)
                coverage = item.coverage if item.coverage > 0 else item.box_coverage_sqft
                if coverage <= 0:
                    # If coverage not provided, try to fetch from tile by size
                    tile = await db.tiles.find_one(
                        {"size": item.size, "deleted": False},
                        {"_id": 0}
                    )
                    if tile:
                        coverage = tile.get('coverage', tile.get('box_coverage_sqft', 0))
                        item.coverage = coverage
                        item.box_packing = tile.get('box_packing', 0)
                
                calculated_item = calculate_line_item(item)
                calculated_items.append(calculated_item.model_dump())
            
            update_data['line_items'] = calculated_items
        
        # Recalculate totals
        temp_invoice = Invoice(**{**existing_invoice, **update_data})
        temp_invoice = calculate_invoice_totals(temp_invoice)
        
        update_data['subtotal'] = temp_invoice.subtotal
        update_data['grand_total'] = temp_invoice.grand_total
        update_data['pending_balance'] = temp_invoice.pending_balance
        update_data['updated_at'] = temp_invoice.updated_at.isoformat()
        
        await db.invoices.update_one(
            {"invoice_id": invoice_id, "deleted": False},
            {"$set": update_data}
        )
        
        # Recalculate customer total_pending from all invoices
        await recalculate_customer_pending(existing_invoice['customer_id'])
        
        updated_invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
        if isinstance(updated_invoice['invoice_date'], str):
            updated_invoice['invoice_date'] = datetime.fromisoformat(updated_invoice['invoice_date'])
        if isinstance(updated_invoice['created_at'], str):
            updated_invoice['created_at'] = datetime.fromisoformat(updated_invoice['created_at'])
        if isinstance(updated_invoice['updated_at'], str):
            updated_invoice['updated_at'] = datetime.fromisoformat(updated_invoice['updated_at'])
        
        return updated_invoice
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/invoices/{invoice_id}")
async def delete_invoice(invoice_id: str):
    """Soft delete an invoice"""
    try:
        # Get invoice first to get customer_id
        invoice = await db.invoices.find_one({"invoice_id": invoice_id, "deleted": False}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        result = await db.invoices.update_one(
            {"invoice_id": invoice_id, "deleted": False},
            {"$set": {"deleted": True}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Recalculate customer total_pending from all invoices
        await recalculate_customer_pending(invoice['customer_id'])
        
        return {"message": "Invoice deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== PDF GENERATION ====================

def generate_invoice_pdf(invoice: dict, output_path: str):
    """Generate elegant PDF with perfect alignment"""
    try:
        # Create PDF with A4 size
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4
        
        # Use DejaVuSans font for Rupee symbol
        try:
            c.setFont("DejaVuSans", 10)
        except:
            c.setFont("Helvetica", 10)
        
        # ==================== HEADER SECTION ====================
        y_position = height - 40
        
        # Company Name (Bold, Large)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y_position, "RANGOLI CONCEPTS (INDIA) PVT. LTD.")
        y_position -= 18
        
        # Simple line separator
        c.setLineWidth(0.5)
        c.line(50, y_position, width - 50, y_position)
        y_position -= 12
        
        # Company Address (smaller, clean)
        c.setFont("Helvetica", 8)
        c.drawString(50, y_position, "Sr. No. 40/1, Marble Market, Near Shell Petrol Pump, Opp. Rajyog Toyota Showroom, Ambegaon,")
        y_position -= 9
        c.drawString(50, y_position, "Mumbai Pune Bypass Rd, Katraj, Pune, Maharashtra - 411046")
        y_position -= 11
        
        # Contact Info
        c.drawString(50, y_position, "Phone: 8550969769  |  Email: rangolicera2009@gmail.com  |  Website: www.rangoliconcepts.com")
        y_position -= 9
        
        # Registration Details
        c.drawString(50, y_position, "GSTIN: 27AANCR5561R1ZD  |  PAN: AANCR5561R  |  CIN: U46639PN2024PTC230073  |  MSME: UDYAM-MH-26-0693896")
        y_position -= 18
        
        # ==================== QUOTATION DETAILS (Right side) ====================
        details_x = width - 150
        details_y = height - 40
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(details_x, details_y, "Quotation No:")
        c.setFont("Helvetica", 9)
        c.drawString(details_x + 70, details_y, invoice['invoice_id'])
        
        details_y -= 11
        c.setFont("Helvetica-Bold", 9)
        c.drawString(details_x, details_y, "Enquiry Date:")
        c.setFont("Helvetica", 9)
        invoice_date = invoice['invoice_date']
        if isinstance(invoice_date, str):
            invoice_date = datetime.fromisoformat(invoice_date)
        c.drawString(details_x + 70, details_y, invoice_date.strftime("%d %b %Y"))
        
        details_y -= 11
        c.setFont("Helvetica-Bold", 9)
        c.drawString(details_x, details_y, "Status:")
        c.setFont("Helvetica", 9)
        c.drawString(details_x + 70, details_y, invoice['status'])
        
        # ==================== BUYER DETAILS ====================
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, y_position, "Buyer (Bill To)")
        y_position -= 3
        
        # Draw simple box for customer details
        c.setLineWidth(0.5)
        box_height = 45
        c.rect(50, y_position - box_height, 250, box_height)
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(55, y_position - 12, invoice['customer_name'])
        
        c.setFont("Helvetica", 8)
        c.drawString(55, y_position - 23, f"Phone: {invoice['customer_phone']}")
        
        # Handle long addresses
        address = invoice['customer_address']
        if len(address) > 45:
            c.drawString(55, y_position - 33, address[:45])
            if len(address) > 45:
                c.drawString(55, y_position - 42, address[45:90])
        else:
            c.drawString(55, y_position - 33, address)
        
        # GSTIN on right side if exists
        if invoice.get('customer_gstin'):
            c.drawString(310, y_position - 12, f"GSTIN: {invoice['customer_gstin']}")
        
        y_position -= (box_height + 15)
        
        # ==================== ITEMS TABLE ====================
        
        # Define precise column positions with better spacing to prevent overlap
        col_sr = 52
        col_image = 70
        col_sku = 118
        col_size = 185
        col_box = 235
        col_sqft = 268
        col_rate = 310
        col_box_rate = 355
        col_disc = 405
        col_amount = 450
        
        # Table header - black background
        c.setFillColorRGB(0, 0, 0)
        c.rect(50, y_position - 14, width - 100, 14, fill=1)
        
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 6)
        header_y = y_position - 6
        
        c.drawString(col_sr, header_y, "SR.")
        c.drawString(col_image + 8, header_y, "IMAGE")
        c.drawString(col_sku, header_y, "SKU")
        c.drawString(col_size, header_y, "SIZE")
        c.drawString(col_box, header_y, "BOX")
        c.drawString(col_sqft, header_y, "SQFT")
        c.drawString(col_rate, header_y, "RATE")
        c.drawString(col_box_rate, header_y, "BOX RATE")
        c.drawString(col_disc, header_y, "DISC")
        c.drawString(col_amount, header_y, "AMOUNT")
        
        table_y = y_position - 18
        c.setFillColorRGB(0, 0, 0)
        
        # Draw thin line under header
        c.setLineWidth(0.3)
        c.line(50, table_y, width - 50, table_y)
        table_y -= 8
        
        # GROUP BY LOCATION
        grouped_items = {}
        for item in invoice['line_items']:
            location = item['location']
            if location not in grouped_items:
                grouped_items[location] = []
            grouped_items[location].append(item)
        
        # ITEMS TABLE
        sr_no = 1
        
        for location, items in grouped_items.items():
            # Location Header
            c.setFont("Helvetica-Bold", 8)
            c.drawString(col_sr, table_y, location.upper())
            table_y -= 10
            
            location_subtotal = 0
            
            for item in items:
                # Check if we need a new page
                if table_y < 150:
                    c.showPage()
                    table_y = height - 50
                
                # Draw tile image if available
                has_image = False
                if item.get('tile_image'):
                    try:
                        # Decode base64 image
                        if item['tile_image'].startswith('data:image'):
                            image_data = item['tile_image'].split(',')[1]
                        else:
                            image_data = item['tile_image']
                        
                        import base64
                        image_bytes = base64.b64decode(image_data)
                        
                        # Create temporary image file
                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                            tmp_file.write(image_bytes)
                            tmp_path = tmp_file.name
                        
                        # Draw image - clean
                        from PIL import Image as PILImage
                        
                        img = PILImage.open(tmp_path)
                        img_width, img_height = img.size
                        
                        # Calculate dimensions maintaining aspect ratio
                        max_width = 45
                        max_height = 45
                        aspect = img_width / img_height
                        
                        if aspect > 1:
                            draw_width = max_width
                            draw_height = max_width / aspect
                        else:
                            draw_height = max_height
                            draw_width = max_height * aspect
                        
                        # Center the image in column
                        x_offset = col_image + (max_width - draw_width) / 2
                        y_offset = table_y + 2
                        
                        # Simple thin border
                        c.setStrokeColorRGB(0.7, 0.7, 0.7)
                        c.setLineWidth(0.3)
                        c.rect(x_offset - 1, y_offset - draw_height - 1, draw_width + 2, draw_height + 2, stroke=1, fill=0)
                        
                        c.drawImage(tmp_path, x_offset, y_offset - draw_height, 
                                  width=draw_width, height=draw_height, 
                                  preserveAspectRatio=True, mask='auto')
                        
                        has_image = True
                        
                        # Clean up
                        import os as os_module
                        os_module.unlink(tmp_path)
                    except Exception as e:
                        logger.warning(f"Error embedding image in PDF: {e}")
                
                # Draw text content with precise alignment
                c.setFont("Helvetica", 6)
                text_y = table_y if not has_image else table_y - 20
                
                c.drawString(col_sr, text_y, str(sr_no))
                # Image column handled above
                # Use tile_name (fallback to product_name for backward compatibility)
                tile_name = item.get('tile_name', item.get('product_name', ''))
                c.drawString(col_sku, text_y, tile_name[:15])
                c.drawString(col_size, text_y, item['size'][:10])
                c.drawString(col_box, text_y, str(item['box_qty']))
                c.drawString(col_sqft, text_y, f"{item['total_sqft']:.1f}")
                
                # Format RATE (per sqft) with Rupee symbol
                try:
                    c.setFont("DejaVuSans", 6)
                    c.drawString(col_rate, text_y, f"₹{item['rate_per_sqft']:.0f}")
                except:
                    c.setFont("Helvetica", 6)
                    c.drawString(col_rate, text_y, f"Rs.{item['rate_per_sqft']:.0f}")
                
                # Format BOX RATE with Rupee symbol
                try:
                    c.setFont("DejaVuSans", 6)
                    c.drawString(col_box_rate, text_y, f"₹{item['rate_per_box']:.0f}")
                except:
                    c.setFont("Helvetica", 6)
                    c.drawString(col_box_rate, text_y, f"Rs.{item['rate_per_box']:.0f}")
                
                c.setFont("Helvetica", 6)
                c.drawString(col_disc, text_y, f"{item['discount_percent']:.0f}%")
                
                try:
                    c.setFont("DejaVuSans", 6)
                    c.drawString(col_amount, text_y, f"₹{item['final_amount']:.2f}")
                except:
                    c.setFont("Helvetica", 6)
                    c.drawString(col_amount, text_y, f"Rs.{item['final_amount']:.2f}")
                
                location_subtotal += item['final_amount']
                
                # Row spacing
                if has_image:
                    table_y -= 48
                else:
                    table_y -= 11
                
                sr_no += 1
            
            # Location Subtotal
            c.setLineWidth(0.3)
            c.line(50, table_y + 2, width - 50, table_y + 2)
            table_y -= 8
            
            c.setFont("Helvetica-Bold", 8)
            c.drawString(col_disc - 20, table_y, f"{location} Total:")
            try:
                c.setFont("DejaVuSans-Bold", 8)
                c.drawString(col_amount, table_y, f"₹{location_subtotal:.2f}")
            except:
                c.setFont("Helvetica-Bold", 8)
                c.drawString(col_amount, table_y, f"Rs.{location_subtotal:.2f}")
            
            table_y -= 12
        
        # ==================== TOTALS SECTION ====================
        
        # Simple separator line
        c.setLineWidth(0.5)
        c.line(50, table_y, width - 50, table_y)
        table_y -= 12
        
        # Totals - right aligned
        label_x = col_disc - 15
        amount_x = col_amount
        
        c.setFont("Helvetica", 9)
        c.drawString(label_x, table_y, "Subtotal:")
        try:
            c.setFont("DejaVuSans", 9)
            c.drawString(amount_x, table_y, f"₹{invoice['subtotal']:.2f}")
        except:
            c.setFont("Helvetica", 9)
            c.drawString(amount_x, table_y, f"Rs.{invoice['subtotal']:.2f}")
        
        table_y -= 11
        c.setFont("Helvetica", 9)
        c.drawString(label_x, table_y, "Transport:")
        try:
            c.setFont("DejaVuSans", 9)
            c.drawString(amount_x, table_y, f"₹{invoice['transport_charges']:.2f}")
        except:
            c.setFont("Helvetica", 9)
            c.drawString(amount_x, table_y, f"Rs.{invoice['transport_charges']:.2f}")
        
        table_y -= 11
        c.setFont("Helvetica", 9)
        c.drawString(label_x, table_y, "Unloading:")
        try:
            c.setFont("DejaVuSans", 9)
            c.drawString(amount_x, table_y, f"₹{invoice['unloading_charges']:.2f}")
        except:
            c.setFont("Helvetica", 9)
            c.drawString(amount_x, table_y, f"Rs.{invoice['unloading_charges']:.2f}")
        
        table_y -= 13
        
        # Grand Total line
        c.setLineWidth(0.5)
        c.line(label_x - 5, table_y + 2, width - 50, table_y + 2)
        table_y -= 9
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(label_x, table_y, "GRAND TOTAL:")
        try:
            c.setFont("DejaVuSans-Bold", 10)
            c.drawString(amount_x, table_y, f"₹{invoice['grand_total']:.2f}")
        except:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(amount_x, table_y, f"Rs.{invoice['grand_total']:.2f}")
        
        table_y -= 13
        
        c.setFont("Helvetica", 9)
        c.drawString(label_x, table_y, "Paid:")
        try:
            c.setFont("DejaVuSans", 9)
            c.drawString(amount_x, table_y, f"₹{invoice['amount_paid']:.2f}")
        except:
            c.setFont("Helvetica", 9)
            c.drawString(amount_x, table_y, f"Rs.{invoice['amount_paid']:.2f}")
        
        table_y -= 11
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(label_x, table_y, "Balance:")
        try:
            c.setFont("DejaVuSans-Bold", 9)
            c.drawString(amount_x, table_y, f"₹{invoice['pending_balance']:.2f}")
        except:
            c.setFont("Helvetica-Bold", 9)
            c.drawString(amount_x, table_y, f"Rs.{invoice['pending_balance']:.2f}")
        
        table_y -= 20
        
        # ==================== BANK DETAILS ====================
        
        if table_y < 130:
            c.showPage()
            table_y = height - 50
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, table_y, "Bank Details:")
        table_y -= 10
        
        c.setFont("Helvetica", 8)
        c.drawString(50, table_y, "Bank: HDFC Bank  |  Account: XXXXXXXX1234  |  IFSC: HDFC0001234  |  Branch: Katraj, Pune")
        table_y -= 18
        
        # ==================== TERMS & CONDITIONS ====================
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, table_y, "Terms & Conditions:")
        table_y -= 10
        
        c.setFont("Helvetica", 7)
        terms = [
            "1. Payment: 100% advance payment required before delivery.",
            "2. Delivery: Subject to availability and transportation arrangements.",
            "3. Validity: This quotation is valid for 7 days from the date of issue.",
            "4. Returns: No returns accepted after delivery.",
            "5. Complaints: Must be reported within 24 hours of delivery with photographic evidence."
        ]
        
        for term in terms:
            c.drawString(50, table_y, term)
            table_y -= 9
        
        # ==================== FOOTER ====================
        
        # Simple separator line
        c.setLineWidth(0.5)
        c.line(50, 55, width - 50, 55)
        
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(50, 42, "For RANGOLI CONCEPTS (INDIA) PVT. LTD.")
        
        c.setFont("Helvetica", 8)
        c.drawString(width - 150, 42, "Authorized Signatory")
        
        # Thank you message
        c.setFont("Helvetica-Oblique", 8)
        thank_text = "Thank you for your business!"
        text_width = c.stringWidth(thank_text, "Helvetica-Oblique", 8)
        c.drawString((width - text_width) / 2, 28, thank_text)
        
        # Save PDF
        c.save()
        logger.info(f"Perfectly aligned PDF generated: {output_path}")
        
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        raise

@api_router.get("/invoices/{invoice_id}/pdf")
async def get_invoice_pdf(invoice_id: str):
    """Generate and return PDF for invoice"""
    try:
        invoice = await db.invoices.find_one({"invoice_id": invoice_id, "deleted": False}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Generate PDF
        pdf_dir = ROOT_DIR / "pdfs"
        pdf_dir.mkdir(exist_ok=True)
        pdf_path = pdf_dir / f"{invoice_id}.pdf"
        
        generate_invoice_pdf(invoice, str(pdf_path))
        
        return FileResponse(
            path=str(pdf_path),
            media_type='application/pdf',
            filename=f"Invoice_{invoice_id}.pdf",
            headers={
                "Content-Disposition": f"attachment; filename=Invoice_{invoice_id}.pdf",
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-cache"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/public/invoices/{invoice_id}/pdf")
async def get_public_invoice_pdf(invoice_id: str):
    """Public endpoint for PDF download (for WhatsApp sharing)"""
    try:
        invoice = await db.invoices.find_one({"invoice_id": invoice_id, "deleted": False}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Generate PDF
        pdf_dir = ROOT_DIR / "pdfs"
        pdf_dir.mkdir(exist_ok=True)
        pdf_path = pdf_dir / f"{invoice_id}.pdf"
        
        generate_invoice_pdf(invoice, str(pdf_path))
        
        return FileResponse(
            path=str(pdf_path),
            media_type='application/pdf',
            filename=f"Invoice_{invoice_id}.pdf",
            headers={
                "Content-Disposition": f"inline; filename=Invoice_{invoice_id}.pdf",
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "public, max-age=3600"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ROOT ENDPOINTS ====================

@api_router.get("/")
async def root():
    return {"message": "Tile Shop Invoicing API", "version": "1.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "tile-shop-api"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
