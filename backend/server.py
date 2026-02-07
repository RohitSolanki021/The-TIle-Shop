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



# ==================== PDF GENERATION (TEMPLATE OVERLAY WITH PROPER MULTI-ITEM SUPPORT) ====================

def generate_invoice_pdf(invoice: dict, output_path: str):
    """
    Generate PDF using TEMPLATE OVERLAY method with proper multi-item support.
    
    Features:
    - Multiple items per section rendered as proper rows
    - Dynamic section names (e.g., "SA" replaces "MAIN FLOOR")
    - Dynamic section totals computed from items
    - Pixel-perfect alignment using box-based positioning
    - White rectangle masking for template text replacement
    - Pagination support with headers on every page
    """
    try:
        import io
        import json
        import tempfile
        import os as os_module
        from pypdf import PdfReader, PdfWriter
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib import colors
        
        # Load template map
        template_map_path = ROOT_DIR / "assets" / "template_map.json"
        with open(template_map_path, 'r') as f:
            tmap = json.load(f)
        
        PAGE_HEIGHT = tmap['page_height']
        PAGE_WIDTH = tmap['page_width']
        
        # Pagination settings
        pagination = tmap.get('pagination', {})
        TABLE_START_Y = pagination.get('content_area_start_y', tmap['table']['first_row_y_from_top'])
        MAX_CONTENT_Y_PAGE1 = pagination.get('content_area_end_y', 700)
        MAX_CONTENT_Y_CONTINUATION = pagination.get('continuation_page_end_y', 780)
        SAFE_BOTTOM_Y = pagination.get('safe_bottom_y', 720)
        
        # Table config
        table_cfg = tmap['table']
        cols = table_cfg['columns']
        ROW_HEIGHT = table_cfg['row_height']
        ROW_HEIGHT_WITH_IMAGE = table_cfg['row_height_with_image']
        
        # Load template PDF path
        template_path = ROOT_DIR / "assets" / "invoice-template.pdf"
        
        # Check if DejaVuSans font is available for Rupee symbol
        use_dejavusans = False
        try:
            from reportlab.pdfbase import pdfmetrics
            pdfmetrics.getFont("DejaVuSans")
            use_dejavusans = True
        except:
            pass
        
        # ==================== HELPER FUNCTIONS ====================
        
        def y_coord(y_from_top):
            """Convert y_from_top to ReportLab's y_from_bottom coordinates"""
            return PAGE_HEIGHT - y_from_top
        
        def set_rupee_font(canvas, size=7, bold=False):
            """Set font that supports Rupee symbol"""
            if use_dejavusans:
                try:
                    canvas.setFont("DejaVuSans", size)
                    return
                except:
                    pass
            canvas.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        
        def draw_text_in_box(canvas, text, box, align="left", font="Helvetica", size=7, color=(0, 0, 0)):
            """
            Draw text within a bounding box with alignment support.
            
            Args:
                canvas: ReportLab canvas
                text: Text to draw
                box: dict with x, y_from_top, width, height
                align: "left", "center", or "right"
                font: Font name
                size: Font size
                color: RGB tuple (0-1 scale)
            """
            canvas.setFont(font, size)
            canvas.setFillColorRGB(*color)
            
            x = box['x']
            width = box['width']
            y_from_top = box['y_from_top']
            height = box.get('height', ROW_HEIGHT)
            
            # Calculate text baseline (vertically centered in box)
            text_y = y_coord(y_from_top + height / 2 + size / 3)
            
            # Truncate text if too long
            max_chars = int(width / (size * 0.5))
            if len(str(text)) > max_chars:
                text = str(text)[:max_chars-2] + ".."
            
            if align == "center":
                text_x = x + width / 2
                canvas.drawCentredString(text_x, text_y, str(text))
            elif align == "right":
                text_x = x + width - 2
                canvas.drawRightString(text_x, text_y, str(text))
            else:  # left
                text_x = x + 2
                canvas.drawString(text_x, text_y, str(text))
        
        def draw_currency_in_box(canvas, value, box, align="right", size=7, bold=False):
            """Draw currency value with Rupee symbol in a box"""
            set_rupee_font(canvas, size, bold)
            canvas.setFillColorRGB(0, 0, 0)
            
            x = box['x']
            width = box['width']
            y_from_top = box['y_from_top']
            height = box.get('height', ROW_HEIGHT)
            
            text_y = y_coord(y_from_top + height / 2 + size / 3)
            formatted_value = f"₹{round(value):,}"
            
            if align == "right":
                text_x = x + width - 2
                canvas.drawRightString(text_x, text_y, formatted_value)
            elif align == "center":
                text_x = x + width / 2
                canvas.drawCentredString(text_x, text_y, formatted_value)
            else:
                text_x = x + 2
                canvas.drawString(text_x, text_y, formatted_value)
        
        def draw_white_mask(canvas, box):
            """Draw a white rectangle to mask template text"""
            canvas.setFillColorRGB(1, 1, 1)  # White
            canvas.rect(
                box['x'],
                y_coord(box['y_from_top'] + box['height']),
                box['width'],
                box['height'],
                fill=True,
                stroke=False
            )
        
        def draw_image_in_box(canvas, image_data, box, padding=2):
            """Draw an image within a bounding box"""
            try:
                if image_data.startswith('data:image'):
                    image_data = image_data.split(',')[1]
                
                image_bytes = base64.b64decode(image_data)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                    tmp_file.write(image_bytes)
                    tmp_path = tmp_file.name
                
                img_w = box['width'] - padding * 2
                img_h = box['height'] - padding * 2
                img_x = box['x'] + padding
                img_y = y_coord(box['y_from_top'] + box['height'] - padding)
                
                canvas.drawImage(tmp_path, img_x, img_y, 
                           width=img_w, height=img_h,
                           preserveAspectRatio=True, mask='auto')
                
                os_module.unlink(tmp_path)
            except Exception as e:
                logger.warning(f"Error drawing image: {e}")
        
        # ==================== GROUP ITEMS BY LOCATION/SECTION ====================
        
        grouped_items = {}
        for item in invoice.get('line_items', []):
            location = item.get('location', 'Items')
            if location not in grouped_items:
                grouped_items[location] = []
            grouped_items[location].append(item)
        
        # ==================== CALCULATE PAGINATION ====================
        
        def get_item_height(item):
            """Calculate height needed for an item row"""
            has_image = bool(item.get('tile_image'))
            return ROW_HEIGHT_WITH_IMAGE if has_image else ROW_HEIGHT
        
        # Build render list with all elements
        render_items = []
        for section_name, items in grouped_items.items():
            # Section header
            render_items.append({
                'type': 'section_header',
                'section_name': section_name,
                'height': table_cfg.get('section_header', {}).get('height', 18)
            })
            
            # Calculate section total while adding items
            section_total = 0
            for idx, item in enumerate(items):
                item_height = get_item_height(item)
                render_items.append({
                    'type': 'item',
                    'item': item,
                    'sr_no': idx + 1,
                    'section_name': section_name,
                    'height': item_height
                })
                section_total += item.get('final_amount', 0)
            
            # Section total row
            render_items.append({
                'type': 'section_total',
                'section_name': section_name,
                'total': section_total,
                'height': table_cfg.get('section_total', {}).get('height', 18)
            })
        
        # Split into pages
        pages_content = []
        current_page_items = []
        current_y = TABLE_START_Y
        page_num = 1
        
        for render_item in render_items:
            item_height = render_item['height']
            max_y = MAX_CONTENT_Y_PAGE1 if page_num == 1 else MAX_CONTENT_Y_CONTINUATION
            
            if current_y + item_height > max_y:
                # Start new page
                if current_page_items:
                    pages_content.append(current_page_items)
                    page_num += 1
                current_page_items = [render_item]
                current_y = TABLE_START_Y + item_height
            else:
                current_page_items.append(render_item)
                current_y += item_height
        
        if current_page_items:
            pages_content.append(current_page_items)
        
        if not pages_content:
            pages_content = [[]]
        
        total_pages = len(pages_content)
        
        # ==================== DRAWING FUNCTIONS ====================
        
        def draw_header_content(canvas, page_num, total_pages):
            """Draw header content (quotation box, buyer, consignee) on each page"""
            qbox = tmap['quotation_box']
            
            canvas.setFont("Helvetica-Bold", 7.5)
            canvas.setFillColorRGB(0, 0, 0)
            
            # Invoice ID (with page number on continuation pages)
            invoice_id_text = invoice['invoice_id']
            if total_pages > 1:
                invoice_id_text = f"{invoice['invoice_id']} (Page {page_num}/{total_pages})"
            
            canvas.drawString(qbox['quotation_no_value']['x'], y_coord(qbox['quotation_no_value']['y_from_top']), 
                        invoice_id_text)
            
            # Date
            invoice_date = invoice.get('invoice_date')
            if invoice_date:
                if isinstance(invoice_date, str):
                    invoice_date = datetime.fromisoformat(invoice_date)
                canvas.drawString(qbox['date_value']['x'], y_coord(qbox['date_value']['y_from_top']), 
                            invoice_date.strftime("%d/%m/%Y"))
            
            # Reference name
            ref_name = invoice.get('reference_name', '') or ''
            if ref_name:
                canvas.setFont("Helvetica", 7.5)
                canvas.drawString(qbox['reference_name_value']['x'], y_coord(qbox['reference_name_value']['y_from_top']), 
                            ref_name[:18])
            
            # Buyer section
            buyer = tmap['buyer_section']
            canvas.setFont("Helvetica-Bold", 7.5)
            canvas.drawString(buyer['name']['x'], y_coord(buyer['name']['y_from_top']), 
                        invoice.get('customer_name', '')[:35])
            
            canvas.setFont("Helvetica", 7)
            canvas.drawString(buyer['phone']['x'], y_coord(buyer['phone']['y_from_top']), 
                        f"Ph: {invoice.get('customer_phone', '')}")
            
            address = invoice.get('customer_address', '')
            if len(address) > 40:
                canvas.drawString(buyer['address_line1']['x'], y_coord(buyer['address_line1']['y_from_top']), 
                            address[:40])
                canvas.drawString(buyer['address_line2']['x'], y_coord(buyer['address_line2']['y_from_top']), 
                            address[40:80])
            else:
                canvas.drawString(buyer['address_line1']['x'], y_coord(buyer['address_line1']['y_from_top']), 
                            address)
            
            if invoice.get('customer_gstin'):
                canvas.drawString(buyer['gstin']['x'], y_coord(buyer['gstin']['y_from_top']), 
                            f"GSTIN: {invoice['customer_gstin']}")
            
            # Consignee section
            consignee = tmap['consignee_section']
            consignee_name = invoice.get('consignee_name') or invoice.get('customer_name', '')
            consignee_phone = invoice.get('consignee_phone') or invoice.get('customer_phone', '')
            consignee_address = invoice.get('consignee_address') or invoice.get('customer_address', '')
            
            canvas.setFont("Helvetica-Bold", 7.5)
            canvas.drawString(consignee['name']['x'], y_coord(consignee['name']['y_from_top']), 
                        consignee_name[:35])
            
            canvas.setFont("Helvetica", 7)
            canvas.drawString(consignee['phone']['x'], y_coord(consignee['phone']['y_from_top']), 
                        f"Ph: {consignee_phone}")
            
            if len(consignee_address) > 40:
                canvas.drawString(consignee['address_line1']['x'], y_coord(consignee['address_line1']['y_from_top']), 
                            consignee_address[:40])
                canvas.drawString(consignee['address_line2']['x'], y_coord(consignee['address_line2']['y_from_top']), 
                            consignee_address[40:80])
            else:
                canvas.drawString(consignee['address_line1']['x'], y_coord(consignee['address_line1']['y_from_top']), 
                            consignee_address)
        
        def draw_section_header(canvas, section_name, current_y):
            """
            Draw section header (e.g., "SA" replacing "MAIN FLOOR").
            Masks the template text with white and draws the section name.
            """
            section_cfg = table_cfg.get('section_header', {})
            height = section_cfg.get('height', 18)
            
            # Mask the template "MAIN FLOOR" text with white rectangle
            mask_cfg = section_cfg.get('mask_box', {})
            if mask_cfg:
                draw_white_mask(canvas, {
                    'x': mask_cfg.get('x', 38),
                    'y_from_top': current_y - 2,
                    'width': mask_cfg.get('width', 537),
                    'height': mask_cfg.get('height', 16)
                })
            
            # Draw the section name centered
            canvas.setFont("Helvetica-Bold", 9)
            canvas.setFillColorRGB(0.35, 0.22, 0.15)  # Brown color
            text_y = y_coord(current_y + height / 2 - 3)
            canvas.drawCentredString(PAGE_WIDTH / 2, text_y, section_name.upper())
            canvas.setFillColorRGB(0, 0, 0)
            
            return height
        
        def draw_item_row(canvas, item, current_y, sr_no):
            """
            Draw a single item row with proper alignment in each column box.
            """
            has_image = bool(item.get('tile_image'))
            row_height = ROW_HEIGHT_WITH_IMAGE if has_image else ROW_HEIGHT
            
            # SR NO - centered
            draw_text_in_box(canvas, str(sr_no), {
                'x': cols['sr_no']['x'],
                'width': cols['sr_no']['width'],
                'y_from_top': current_y,
                'height': row_height
            }, align="center", size=7)
            
            # NAME - left aligned
            tile_name = item.get('tile_name') or item.get('product_name') or ''
            draw_text_in_box(canvas, tile_name, {
                'x': cols['name']['x'],
                'width': cols['name']['width'],
                'y_from_top': current_y,
                'height': row_height
            }, align="left", size=7)
            
            # IMAGE
            if has_image and item.get('tile_image'):
                draw_image_in_box(canvas, item['tile_image'], {
                    'x': cols['image']['x'],
                    'width': cols['image'].get('img_width', 30),
                    'y_from_top': current_y,
                    'height': cols['image'].get('img_height', 30)
                })
            
            # SIZE - centered
            draw_text_in_box(canvas, item.get('size', ''), {
                'x': cols['size']['x'],
                'width': cols['size']['width'],
                'y_from_top': current_y,
                'height': row_height
            }, align="center", size=7)
            
            # RATE/BOX - right aligned with Rupee
            draw_currency_in_box(canvas, item.get('rate_per_box', 0), {
                'x': cols['rate_box']['x'],
                'width': cols['rate_box']['width'],
                'y_from_top': current_y,
                'height': row_height
            }, align="right", size=7)
            
            # RATE/SQFT - right aligned with Rupee
            draw_currency_in_box(canvas, item.get('rate_per_sqft', 0), {
                'x': cols['rate_sqft']['x'],
                'width': cols['rate_sqft']['width'],
                'y_from_top': current_y,
                'height': row_height
            }, align="right", size=7)
            
            # QUANTITY - centered
            qty_text = f"{item.get('box_qty', 0)} box"
            draw_text_in_box(canvas, qty_text, {
                'x': cols['quantity']['x'],
                'width': cols['quantity']['width'],
                'y_from_top': current_y,
                'height': row_height
            }, align="center", size=7)
            
            # DISC - centered
            disc_text = f"{round(item.get('discount_percent', 0))}%"
            draw_text_in_box(canvas, disc_text, {
                'x': cols['disc']['x'],
                'width': cols['disc']['width'],
                'y_from_top': current_y,
                'height': row_height
            }, align="center", size=7)
            
            # AMOUNT - right aligned with Rupee
            draw_currency_in_box(canvas, item.get('final_amount', 0), {
                'x': cols['amount']['x'],
                'width': cols['amount']['width'],
                'y_from_top': current_y,
                'height': row_height
            }, align="right", size=7)
            
            return row_height
        
        def draw_section_total(canvas, section_name, total, current_y):
            """
            Draw section total row (e.g., "SA's Total Amount: ₹X,XXX").
            Masks the template "MAIN FLOOR's Total Amount" text.
            """
            section_cfg = table_cfg.get('section_total', {})
            height = section_cfg.get('height', 18)
            
            # Mask the template text with white rectangle
            mask_cfg = section_cfg.get('mask_box', {})
            if mask_cfg:
                draw_white_mask(canvas, {
                    'x': mask_cfg.get('x', 38),
                    'y_from_top': current_y,
                    'width': mask_cfg.get('width', 537),
                    'height': mask_cfg.get('height', 16)
                })
            
            # Draw section total label - right aligned before amount column
            canvas.setFont("Helvetica-Bold", 7)
            canvas.setFillColorRGB(0.35, 0.22, 0.15)  # Brown color
            label_text = f"{section_name}'s Total Amount:"
            label_x = cols['amount']['x'] - 5
            text_y = y_coord(current_y + height / 2 - 2)
            canvas.drawRightString(label_x, text_y, label_text)
            
            # Draw total value - right aligned in amount column
            draw_currency_in_box(canvas, total, {
                'x': cols['amount']['x'],
                'width': cols['amount']['width'],
                'y_from_top': current_y,
                'height': height
            }, align="right", size=7, bold=True)
            
            canvas.setFillColorRGB(0, 0, 0)
            return height
        
        def draw_footer_content(canvas):
            """Draw footer content (financial summary, remarks) on the last page"""
            fin = tmap['financial_summary']
            
            def draw_fin_amount(y_from_top, value):
                set_rupee_font(canvas, 7.5)
                canvas.drawRightString(fin['value_x'], y_coord(y_from_top), f"₹{round(value):,}")
            
            canvas.setFillColorRGB(0, 0, 0)
            
            # Total Amount
            draw_fin_amount(fin['total_amount']['y_from_top'], invoice.get('subtotal', 0))
            
            # Transport Charges
            draw_fin_amount(fin['transport']['y_from_top'], invoice.get('transport_charges', 0))
            
            # Unloading Charges
            draw_fin_amount(fin['unloading']['y_from_top'], invoice.get('unloading_charges', 0))
            
            # GST
            gst_amount = invoice.get('gst_amount', 0)
            gst_percent = invoice.get('gst_percent', 0)
            if gst_amount > 0 or gst_percent > 0:
                draw_fin_amount(fin['gst']['y_from_top'], gst_amount)
            else:
                canvas.setFont("Helvetica-Oblique", 7)
                canvas.setFillColorRGB(0.4, 0.4, 0.4)
                canvas.drawRightString(fin['value_x'], y_coord(fin['gst']['y_from_top']), "As applicable")
                canvas.setFillColorRGB(0, 0, 0)
            
            # Final Amount
            canvas.setFillColorRGB(1, 1, 1)  # White on brown background
            set_rupee_font(canvas, 8, bold=True)
            canvas.drawRightString(fin['value_x'], y_coord(fin['final_amount']['y_from_top']), 
                             f"₹{round(invoice.get('grand_total', 0)):,}")
            canvas.setFillColorRGB(0, 0, 0)
            
            # Overall Remarks
            remarks = invoice.get('overall_remarks', '')
            if remarks:
                remarks_cfg = tmap['overall_remarks']
                canvas.setFont("Helvetica", 7)
                canvas.setFillColorRGB(0, 0, 0)
                
                words = remarks.split()
                line = ""
                y_offset = 0
                for word in words:
                    test_line = line + " " + word if line else word
                    if canvas.stringWidth(test_line, "Helvetica", 7) < remarks_cfg['max_width']:
                        line = test_line
                    else:
                        canvas.drawString(remarks_cfg['x'], y_coord(remarks_cfg['y_from_top'] + y_offset), line)
                        y_offset += 10
                        line = word
                if line:
                    canvas.drawString(remarks_cfg['x'], y_coord(remarks_cfg['y_from_top'] + y_offset), line)
        
        def create_page_overlay(page_num, page_items, is_last_page):
            """Create overlay for a single page with all dynamic content"""
            page_buffer = io.BytesIO()
            canvas = rl_canvas.Canvas(page_buffer, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
            
            # Draw header content
            draw_header_content(canvas, page_num, total_pages)
            
            # Draw items for this page
            current_y = TABLE_START_Y
            
            for render_item in page_items:
                if render_item['type'] == 'section_header':
                    height = draw_section_header(canvas, render_item['section_name'], current_y)
                    current_y += height
                    
                elif render_item['type'] == 'item':
                    height = draw_item_row(canvas, render_item['item'], current_y, render_item['sr_no'])
                    current_y += height
                    
                elif render_item['type'] == 'section_total':
                    height = draw_section_total(canvas, render_item['section_name'], render_item['total'], current_y)
                    current_y += height
            
            # Draw footer only on last page
            if is_last_page:
                draw_footer_content(canvas)
            
            # Add continuation note on non-last pages
            if not is_last_page:
                max_y_for_note = MAX_CONTENT_Y_PAGE1 if page_num == 1 else MAX_CONTENT_Y_CONTINUATION
                canvas.setFont("Helvetica-Oblique", 8)
                canvas.setFillColorRGB(0.4, 0.4, 0.4)
                canvas.drawCentredString(PAGE_WIDTH / 2, y_coord(max_y_for_note + 20), 
                                       "Continued on next page...")
                canvas.setFillColorRGB(0, 0, 0)
            
            canvas.save()
            page_buffer.seek(0)
            return page_buffer
        
        # ==================== GENERATE PDF ====================
        
        writer = PdfWriter()
        
        for page_idx, page_items in enumerate(pages_content):
            page_num = page_idx + 1
            is_last_page = page_num == total_pages
            
            # Load fresh template for each page
            template_reader = PdfReader(str(template_path))
            template_page = template_reader.pages[0]
            
            # Create overlay for this page
            overlay_buffer = create_page_overlay(page_num, page_items, is_last_page)
            overlay_reader = PdfReader(overlay_buffer)
            
            if len(overlay_reader.pages) > 0:
                overlay_page = overlay_reader.pages[0]
                template_page.merge_page(overlay_page)
            
            writer.add_page(template_page)
            logger.info(f"Generated page {page_num}/{total_pages} with {len(page_items)} items")
        
        # Write output
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        logger.info(f"PDF generated: {output_path} ({total_pages} pages)")
        
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
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
