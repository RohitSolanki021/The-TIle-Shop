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
    
    invoice_id: str = ""  # Will be set by generate_invoice_id()
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
    """Calculate all invoice totals including GST"""
    invoice.subtotal = sum(item.final_amount for item in invoice.line_items)
    # Calculate GST if percentage is provided
    if invoice.gst_percent > 0:
        invoice.gst_amount = invoice.subtotal * (invoice.gst_percent / 100)
    else:
        invoice.gst_amount = 0
    invoice.grand_total = invoice.subtotal + invoice.transport_charges + invoice.unloading_charges + invoice.gst_amount
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

async def generate_invoice_id():
    """Generate invoice ID in format: TTS / XXX / YYYY-YY
    Financial year: April to March
    - April 2025 to March 2026 = 2025-26
    - April 2026 to March 2027 = 2026-27
    """
    now = datetime.now()
    current_month = now.month
    current_year = now.year
    
    # Determine financial year
    # If month is April (4) or later, FY starts in current year
    # If month is Jan-March, FY started in previous year
    if current_month >= 4:
        fy_start = current_year
        fy_end = current_year + 1
    else:
        fy_start = current_year - 1
        fy_end = current_year
    
    fy_string = f"{fy_start}-{str(fy_end)[-2:]}"  # e.g., "2025-26"
    
    # Get the last invoice number for this financial year
    # Pattern: TTS / XXX / 2025-26
    pattern = f"TTS / .* / {fy_string}"
    
    # Find the highest invoice number for this FY
    last_invoice = await db.invoices.find_one(
        {"invoice_id": {"$regex": f"^TTS / .* / {fy_string}$"}},
        sort=[("invoice_id", -1)]
    )
    
    if last_invoice:
        # Extract the sequence number from the last invoice
        try:
            parts = last_invoice['invoice_id'].split(' / ')
            last_seq = int(parts[1])
            new_seq = last_seq + 1
        except (ValueError, IndexError):
            new_seq = 1
    else:
        new_seq = 1
    
    # Format: TTS / 001 / 2025-26
    invoice_id = f"TTS / {new_seq:03d} / {fy_string}"
    return invoice_id

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
        
        # Generate financial year-based invoice ID
        invoice.invoice_id = await generate_invoice_id()
        
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


# ==================== PDF GENERATION - COORDINATE-BASED GRID ====================

def generate_invoice_pdf(invoice: dict, output_path: str):
    """
    Generate PDF treating invoice as coordinate-based grid.
    
    Rules:
    1. Every field drawn inside predefined bounding boxes
    2. Section header replaces "MAIN FLOOR" by: background rect + new text in same box
    3. Items rendered using loop: y = startY + (rowIndex * rowHeight)
    4. Section total label replaced (cover old + draw new)
    5. Never place section text inside column cell
    6. Tables not moved - only fill boxes
    """
    try:
        import io
        import json
        import tempfile
        import os as os_module
        from pypdf import PdfReader, PdfWriter
        from reportlab.pdfgen import canvas as rl_canvas
        
        # Load template map with grid coordinates
        template_map_path = ROOT_DIR / "assets" / "template_map.json"
        with open(template_map_path, 'r') as f:
            tmap = json.load(f)
        
        PAGE_HEIGHT = tmap['page_height']
        PAGE_WIDTH = tmap['page_width']
        BG_COLOR = tuple(tmap.get('background_color', [0.98, 0.96, 0.95]))
        
        # Grid configuration
        grid = tmap['grid']
        cols = grid['column_boundaries']
        
        # Row parameters from grid
        ITEM_START_Y = grid['item_rows']['start_y']          # 255
        ROW_HEIGHT = grid['item_rows']['row_height']          # 18
        ROW_HEIGHT_IMG = grid['item_rows']['row_height_with_image']  # 40
        ITEM_END_Y_PAGE1 = grid['item_rows']['end_y_page1']   # 333
        ITEM_END_Y_CONT = grid['item_rows']['end_y_continuation']  # 780
        
        # Section row boxes from grid
        section_header = grid['section_header_row']
        section_total = grid['section_total_row']
        
        template_path = ROOT_DIR / "assets" / "invoice-template.pdf"
        
        # Rupee font check
        use_dejavusans = False
        try:
            from reportlab.pdfbase import pdfmetrics
            pdfmetrics.getFont("DejaVuSans")
            use_dejavusans = True
        except:
            pass
        
        # ==================== COORDINATE HELPERS ====================
        
        def y_coord(y_from_top):
            """Convert y_from_top to ReportLab y_from_bottom"""
            return PAGE_HEIGHT - y_from_top
        
        def cover_box(canvas, box):
            """Draw background-colored rectangle to cover template text"""
            canvas.setFillColorRGB(*BG_COLOR)
            canvas.rect(
                box['x'],
                y_coord(box['y_top'] + box['height']),
                box['width'],
                box['height'],
                fill=True, stroke=False
            )
        
        def draw_in_box(canvas, text, box, align="center", size=9, font="Helvetica-Bold", color=(0, 0, 0)):
            """Draw text inside a bounding box with alignment"""
            canvas.setFont(font, size)
            canvas.setFillColorRGB(*color)
            
            x = box['x']
            w = box['width']
            y_top = box['y_top']
            h = box['height']
            
            # Baseline centered vertically in box
            text_y = y_coord(y_top + h/2 + size/3)
            
            if align == "center":
                canvas.drawCentredString(x + w/2, text_y, str(text))
            elif align == "right":
                canvas.drawRightString(x + w - 2, text_y, str(text))
            else:
                canvas.drawString(x + 2, text_y, str(text))
        
        def draw_currency_in_box(canvas, value, box, align="right", size=7, bold=False):
            """Draw currency with Rupee symbol inside box"""
            if use_dejavusans:
                try:
                    canvas.setFont("DejaVuSans", size)
                except:
                    canvas.setFont("Helvetica-Bold" if bold else "Helvetica", size)
            else:
                canvas.setFont("Helvetica-Bold" if bold else "Helvetica", size)
            
            canvas.setFillColorRGB(0, 0, 0)
            
            text_y = y_coord(box['y_top'] + box['height']/2 + size/3)
            formatted = f"₹{round(value):,}"
            
            if align == "right":
                canvas.drawRightString(box['x'] + box['width'] - 2, text_y, formatted)
            elif align == "center":
                canvas.drawCentredString(box['x'] + box['width']/2, text_y, formatted)
            else:
                canvas.drawString(box['x'] + 2, text_y, formatted)
        
        def draw_image_in_box(canvas, image_data, box):
            """Draw image inside bounding box"""
            try:
                if image_data.startswith('data:image'):
                    image_data = image_data.split(',')[1]
                
                image_bytes = base64.b64decode(image_data)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                    tmp.write(image_bytes)
                    tmp_path = tmp.name
                
                canvas.drawImage(
                    tmp_path,
                    box['x'] + 2,
                    y_coord(box['y_top'] + box['height'] - 2),
                    width=box['width'] - 4,
                    height=box['height'] - 4,
                    preserveAspectRatio=True,
                    mask='auto'
                )
                
                os_module.unlink(tmp_path)
            except Exception as e:
                logger.warning(f"Image error: {e}")
        
        # ==================== GROUP ITEMS BY SECTION ====================
        
        sections_dict = {}
        for item in invoice.get('line_items', []):
            section = item.get('location', 'Items')
            if section not in sections_dict:
                sections_dict[section] = []
            sections_dict[section].append(item)
        
        sections = [{'name': name, 'items': items} for name, items in sections_dict.items()]
        
        # ==================== PAGINATION ====================
        
        def get_row_height(item):
            return ROW_HEIGHT_IMG if item.get('tile_image') else ROW_HEIGHT
        
        # Build render list
        render_list = []
        for section in sections:
            # Section header
            render_list.append({'type': 'section_header', 'name': section['name'], 'height': section_header['height']})
            
            # Items
            section_total_value = 0
            for i, item in enumerate(section['items']):
                h = get_row_height(item)
                render_list.append({'type': 'item', 'item': item, 'sr': i+1, 'height': h})
                section_total_value += item.get('final_amount', 0)
            
            # Section total
            render_list.append({'type': 'section_total', 'name': section['name'], 'total': section_total_value, 'height': section_total['height']})
        
        # Split into pages
        pages = []
        current_page = []
        current_y = ITEM_START_Y
        page_num = 1
        
        for elem in render_list:
            limit = ITEM_END_Y_PAGE1 if page_num == 1 else ITEM_END_Y_CONT
            
            if current_y + elem['height'] > limit:
                if current_page:
                    pages.append(current_page)
                    page_num += 1
                current_page = [elem]
                current_y = ITEM_START_Y + elem['height']
            else:
                current_page.append(elem)
                current_y += elem['height']
        
        if current_page:
            pages.append(current_page)
        if not pages:
            pages = [[]]
        
        total_pages = len(pages)
        
        # ==================== DRAWING FUNCTIONS ====================
        
        def draw_header(canvas, page_num):
            """Draw invoice header content"""
            qbox = tmap['quotation_box']
            
            canvas.setFont("Helvetica-Bold", 7.5)
            canvas.setFillColorRGB(0, 0, 0)
            
            # Invoice ID
            inv_id = invoice['invoice_id']
            if total_pages > 1:
                inv_id = f"{inv_id} (Page {page_num}/{total_pages})"
            canvas.drawString(qbox['quotation_no_value']['x'], y_coord(qbox['quotation_no_value']['y_from_top']), inv_id)
            
            # Date
            d = invoice.get('invoice_date')
            if d:
                if isinstance(d, str):
                    d = datetime.fromisoformat(d)
                canvas.drawString(qbox['date_value']['x'], y_coord(qbox['date_value']['y_from_top']), d.strftime("%d/%m/%Y"))
            
            # Reference
            ref = invoice.get('reference_name', '') or ''
            if ref:
                canvas.setFont("Helvetica", 7.5)
                canvas.drawString(qbox['reference_name_value']['x'], y_coord(qbox['reference_name_value']['y_from_top']), ref[:18])
            
            # Buyer
            buyer = tmap['buyer_section']
            canvas.setFont("Helvetica-Bold", 7.5)
            canvas.drawString(buyer['name']['x'], y_coord(buyer['name']['y_from_top']), invoice.get('customer_name', '')[:35])
            canvas.setFont("Helvetica", 7)
            canvas.drawString(buyer['phone']['x'], y_coord(buyer['phone']['y_from_top']), f"Ph: {invoice.get('customer_phone', '')}")
            addr = invoice.get('customer_address', '')
            canvas.drawString(buyer['address_line1']['x'], y_coord(buyer['address_line1']['y_from_top']), addr[:40])
            if len(addr) > 40:
                canvas.drawString(buyer['address_line2']['x'], y_coord(buyer['address_line2']['y_from_top']), addr[40:80])
            if invoice.get('customer_gstin'):
                canvas.drawString(buyer['gstin']['x'], y_coord(buyer['gstin']['y_from_top']), f"GSTIN: {invoice['customer_gstin']}")
            
            # Consignee
            cons = tmap['consignee_section']
            c_name = invoice.get('consignee_name') or invoice.get('customer_name', '')
            c_phone = invoice.get('consignee_phone') or invoice.get('customer_phone', '')
            c_addr = invoice.get('consignee_address') or invoice.get('customer_address', '')
            canvas.setFont("Helvetica-Bold", 7.5)
            canvas.drawString(cons['name']['x'], y_coord(cons['name']['y_from_top']), c_name[:35])
            canvas.setFont("Helvetica", 7)
            canvas.drawString(cons['phone']['x'], y_coord(cons['phone']['y_from_top']), f"Ph: {c_phone}")
            canvas.drawString(cons['address_line1']['x'], y_coord(cons['address_line1']['y_from_top']), c_addr[:40])
            if len(c_addr) > 40:
                canvas.drawString(cons['address_line2']['x'], y_coord(cons['address_line2']['y_from_top']), c_addr[40:80])
        
        def draw_section_header_row(canvas, section_name, y):
            """
            Replace 'MAIN FLOOR' with section name.
            1. Cover template text with background rect
            2. Draw section name centered in same box
            """
            text_box = section_header['text_box']
            box = {'x': text_box['x'], 'y_top': y, 'width': text_box['width'], 'height': text_box['height']}
            
            # Cover old text
            cover_box(canvas, box)
            
            # Draw new text
            draw_in_box(canvas, section_name.upper(), box, align="center", size=9, 
                       font="Helvetica-Bold", color=(0.35, 0.22, 0.15))
        
        def draw_item_row(canvas, item, sr, y):
            """
            Draw item row at y position.
            Each field drawn inside its column bounding box.
            """
            has_img = bool(item.get('tile_image'))
            h = ROW_HEIGHT_IMG if has_img else ROW_HEIGHT
            
            # SR NO
            draw_in_box(canvas, str(sr), {
                'x': cols['sr_no']['x0'], 'width': cols['sr_no']['width'], 'y_top': y, 'height': h
            }, align="center", size=7, font="Helvetica", color=(0,0,0))
            
            # NAME
            name = item.get('tile_name') or item.get('product_name') or ''
            draw_in_box(canvas, name[:15], {
                'x': cols['name']['x0'], 'width': cols['name']['width'], 'y_top': y, 'height': h
            }, align="left", size=7, font="Helvetica", color=(0,0,0))
            
            # IMAGE
            if has_img and item.get('tile_image'):
                draw_image_in_box(canvas, item['tile_image'], {
                    'x': cols['image']['x0'], 'width': 35, 'y_top': y + 3, 'height': 34
                })
            
            # SIZE
            draw_in_box(canvas, item.get('size', '')[:15], {
                'x': cols['size']['x0'], 'width': cols['size']['width'], 'y_top': y, 'height': h
            }, align="center", size=7, font="Helvetica", color=(0,0,0))
            
            # RATE/BOX
            draw_currency_in_box(canvas, item.get('rate_per_box', 0), {
                'x': cols['rate_box']['x0'], 'width': cols['rate_box']['width'], 'y_top': y, 'height': h
            }, align="right", size=6)
            
            # RATE/SQFT
            draw_currency_in_box(canvas, item.get('rate_per_sqft', 0), {
                'x': cols['rate_sqft']['x0'], 'width': cols['rate_sqft']['width'], 'y_top': y, 'height': h
            }, align="right", size=6)
            
            # QUANTITY
            draw_in_box(canvas, f"{item.get('box_qty', 0)} box", {
                'x': cols['quantity']['x0'], 'width': cols['quantity']['width'], 'y_top': y, 'height': h
            }, align="center", size=6, font="Helvetica", color=(0,0,0))
            
            # DISC
            draw_in_box(canvas, f"{round(item.get('discount_percent', 0))}%", {
                'x': cols['disc']['x0'], 'width': cols['disc']['width'], 'y_top': y, 'height': h
            }, align="center", size=6, font="Helvetica", color=(0,0,0))
            
            # AMOUNT
            draw_currency_in_box(canvas, item.get('final_amount', 0), {
                'x': cols['amount']['x0'], 'width': cols['amount']['width'], 'y_top': y, 'height': h
            }, align="right", size=7, bold=True)
            
            return h
        
        def draw_section_total_row(canvas, section_name, total, y):
            """
            Replace 'MAIN FLOOR's Total Amount' with section name.
            1. Cover label area with background rect
            2. Draw new label text
            3. Draw total value in value box
            """
            label_box = section_total['label_box']
            value_box = section_total['value_box']
            
            lb = {'x': label_box['x'], 'y_top': y, 'width': label_box['width'], 'height': label_box['height']}
            vb = {'x': value_box['x'], 'y_top': y, 'width': value_box['width'], 'height': value_box['height']}
            
            # Cover old label
            cover_box(canvas, lb)
            
            # Draw new label
            draw_in_box(canvas, f"{section_name}'s Total Amount", lb, align="right", size=8,
                       font="Helvetica-Bold", color=(0.35, 0.22, 0.15))
            
            # Draw value
            draw_currency_in_box(canvas, total, vb, align="right", size=8, bold=True)
        
        def draw_footer(canvas):
            """Draw financial summary"""
            fin = tmap['financial_summary']
            
            def draw_amt(y_from_top, value):
                if use_dejavusans:
                    try:
                        canvas.setFont("DejaVuSans", 7.5)
                    except:
                        canvas.setFont("Helvetica", 7.5)
                else:
                    canvas.setFont("Helvetica", 7.5)
                canvas.setFillColorRGB(0, 0, 0)
                canvas.drawRightString(fin['value_x'], y_coord(y_from_top), f"₹{round(value):,}")
            
            draw_amt(fin['total_amount']['y_from_top'], invoice.get('subtotal', 0))
            draw_amt(fin['transport']['y_from_top'], invoice.get('transport_charges', 0))
            draw_amt(fin['unloading']['y_from_top'], invoice.get('unloading_charges', 0))
            
            gst = invoice.get('gst_amount', 0)
            if gst > 0:
                draw_amt(fin['gst']['y_from_top'], gst)
            else:
                canvas.setFont("Helvetica-Oblique", 7)
                canvas.setFillColorRGB(0.4, 0.4, 0.4)
                canvas.drawRightString(fin['value_x'], y_coord(fin['gst']['y_from_top']), "As applicable")
            
            canvas.setFillColorRGB(1, 1, 1)
            if use_dejavusans:
                try:
                    canvas.setFont("DejaVuSans", 8)
                except:
                    canvas.setFont("Helvetica-Bold", 8)
            else:
                canvas.setFont("Helvetica-Bold", 8)
            canvas.drawRightString(fin['value_x'], y_coord(fin['final_amount']['y_from_top']), f"₹{round(invoice.get('grand_total', 0)):,}")
            
            # Remarks
            remarks = invoice.get('overall_remarks', '')
            if remarks:
                r = tmap['overall_remarks']
                canvas.setFont("Helvetica", 7)
                canvas.setFillColorRGB(0, 0, 0)
                canvas.drawString(r['x'], y_coord(r['y_from_top']), remarks[:80])
        
        def create_page_overlay(page_num, page_elems, is_last):
            """Create overlay for one page"""
            buf = io.BytesIO()
            c = rl_canvas.Canvas(buf, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
            
            draw_header(c, page_num)
            
            # Render elements with y = startY + (rowIndex * rowHeight)
            current_y = ITEM_START_Y
            
            for elem in page_elems:
                if elem['type'] == 'section_header':
                    draw_section_header_row(c, elem['name'], current_y)
                    current_y += elem['height']
                    
                elif elem['type'] == 'item':
                    h = draw_item_row(c, elem['item'], elem['sr'], current_y)
                    current_y += h
                    
                elif elem['type'] == 'section_total':
                    draw_section_total_row(c, elem['name'], elem['total'], current_y)
                    current_y += elem['height']
            
            if is_last:
                draw_footer(c)
            
            if not is_last:
                c.setFont("Helvetica-Oblique", 8)
                c.setFillColorRGB(0.4, 0.4, 0.4)
                c.drawCentredString(PAGE_WIDTH/2, y_coord(ITEM_END_Y_PAGE1 + 10), "Continued on next page...")
            
            c.save()
            buf.seek(0)
            return buf
        
        # ==================== GENERATE PDF ====================
        
        writer = PdfWriter()
        
        for i, page_elems in enumerate(pages):
            page_num = i + 1
            is_last = page_num == total_pages
            
            # Fresh template
            tr = PdfReader(str(template_path))
            tp = tr.pages[0]
            
            # Merge overlay
            overlay = create_page_overlay(page_num, page_elems, is_last)
            or_ = PdfReader(overlay)
            if len(or_.pages) > 0:
                tp.merge_page(or_.pages[0])
            
            writer.add_page(tp)
            logger.info(f"Generated page {page_num}/{total_pages}")
        
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        logger.info(f"PDF: {output_path} ({total_pages} pages)")
        
    except Exception as e:
        logger.error(f"PDF error: {e}")
        import traceback
        traceback.print_exc()
        raise

@api_router.get("/invoices/{invoice_id:path}/pdf")
async def get_invoice_pdf(invoice_id: str):
    """Generate and return PDF for invoice"""
    try:
        invoice = await db.invoices.find_one({"invoice_id": invoice_id, "deleted": False}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        pdf_dir = ROOT_DIR / "pdfs"
        pdf_dir.mkdir(exist_ok=True)
        safe_filename = invoice_id.replace(" / ", "-").replace("/", "-")
        pdf_path = pdf_dir / f"{safe_filename}.pdf"
        
        generate_invoice_pdf(invoice, str(pdf_path))
        
        return FileResponse(
            path=str(pdf_path),
            media_type='application/pdf',
            filename=f"Invoice_{safe_filename}.pdf",
            headers={
                "Content-Disposition": f"attachment; filename=Invoice_{safe_filename}.pdf",
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-cache"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/public/invoices/{invoice_id:path}/pdf")
async def get_public_invoice_pdf(invoice_id: str):
    """Public endpoint for PDF download (for WhatsApp sharing)"""
    try:
        invoice = await db.invoices.find_one({"invoice_id": invoice_id, "deleted": False}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        pdf_dir = ROOT_DIR / "pdfs"
        pdf_dir.mkdir(exist_ok=True)
        safe_filename = invoice_id.replace(" / ", "-").replace("/", "-")
        pdf_path = pdf_dir / f"{safe_filename}.pdf"
        
        generate_invoice_pdf(invoice, str(pdf_path))
        
        return FileResponse(
            path=str(pdf_path),
            media_type='application/pdf',
            filename=f"Invoice_{safe_filename}.pdf",
            headers={
                "Content-Disposition": f"inline; filename=Invoice_{safe_filename}.pdf",
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
