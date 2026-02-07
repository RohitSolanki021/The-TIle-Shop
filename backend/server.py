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
    """Generate PDF matching THE TILE SHOP reference template exactly"""
    try:
        import tempfile
        import os as os_module
        
        # Create PDF with A4 size
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4
        
        # Use DejaVuSans font for Rupee symbol
        use_dejavusans = False
        try:
            c.setFont("DejaVuSans", 10)
            use_dejavusans = True
        except:
            c.setFont("Helvetica", 10)
        
        # ==================== COMPANY HEADER (Left Side) ====================
        y_pos = height - 35
        
        # Draw Logo
        logo_path = ROOT_DIR / "assets" / "logo.png"
        if logo_path.exists():
            try:
                c.drawImage(str(logo_path), 40, y_pos - 50, width=60, height=60, preserveAspectRatio=True, mask='auto')
            except Exception as e:
                logger.warning(f"Could not draw logo: {e}")
        
        # Company Name and Details (next to logo)
        header_x = 110
        c.setFont("Helvetica-Bold", 14)
        c.setFillColorRGB(0.35, 0.22, 0.15)  # Dark brown color
        c.drawString(header_x, y_pos, "THE TILE SHOP")
        
        c.setFont("Helvetica", 7)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawString(header_x, y_pos - 12, "A Subsidiary of SHREE SONANA SHETRPAL CERAMIC")
        
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 7)
        c.drawString(header_x, y_pos - 24, "S No. 19, Shop No. 2, Near Pravin Electronics, Pune Saswad Road,")
        c.drawString(header_x, y_pos - 33, "Gondhale Nagar, Hadapsar, Pune - 411028")
        c.drawString(header_x, y_pos - 44, "Contact: +91 879 601 5150 / +91 702 099 8244")
        c.drawString(header_x, y_pos - 53, "Email: thetileshoppune@gmail.com")
        c.drawString(header_x, y_pos - 64, "GSTIN: 27ALBPJ3478P1ZJ")
        
        # ==================== QUOTATION BOX (Right Side) ====================
        box_x = width - 180
        box_y = y_pos - 5
        box_width = 140
        box_height = 65
        
        # Draw quotation box with brown header
        c.setFillColorRGB(0.35, 0.22, 0.15)  # Dark brown
        c.rect(box_x, box_y - 15, box_width, 18, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(box_x + box_width/2, box_y - 10, "Quotation")
        
        # Box border
        c.setStrokeColorRGB(0.35, 0.22, 0.15)
        c.setLineWidth(1)
        c.rect(box_x, box_y - box_height, box_width, box_height - 15, stroke=1, fill=0)
        
        # Quotation details inside box
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 8)
        detail_y = box_y - 28
        
        c.drawString(box_x + 5, detail_y, "Quotation No.:")
        c.setFont("Helvetica-Bold", 8)
        c.drawString(box_x + 70, detail_y, invoice['invoice_id'])
        
        detail_y -= 12
        c.setFont("Helvetica", 8)
        c.drawString(box_x + 5, detail_y, "Date:")
        invoice_date = invoice['invoice_date']
        if isinstance(invoice_date, str):
            invoice_date = datetime.fromisoformat(invoice_date)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(box_x + 70, detail_y, invoice_date.strftime("%d/%m/%Y"))
        
        detail_y -= 12
        c.setFont("Helvetica", 8)
        c.drawString(box_x + 5, detail_y, "Reference Name:")
        ref_name = invoice.get('reference_name', '') or ''
        c.setFont("Helvetica-Bold", 8)
        c.drawString(box_x + 70, detail_y, ref_name[:20] if ref_name else '')
        
        # ==================== BUYER & CONSIGNEE SECTION ====================
        y_pos = height - 115
        
        # Draw horizontal line
        c.setStrokeColorRGB(0.35, 0.22, 0.15)
        c.setLineWidth(0.5)
        c.line(40, y_pos, width - 40, y_pos)
        y_pos -= 5
        
        # Two-column layout for Buyer and Consignee
        left_col_x = 45
        right_col_x = width / 2 + 10
        col_width = (width - 100) / 2 - 10
        
        # Buyer (Bill To) Header
        c.setFillColorRGB(0.35, 0.22, 0.15)
        c.rect(left_col_x, y_pos - 15, col_width, 15, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(left_col_x + 5, y_pos - 11, "Buyer (Bill To)")
        
        # Consignee (Ship To) Header
        c.setFillColorRGB(0.35, 0.22, 0.15)
        c.rect(right_col_x, y_pos - 15, col_width, 15, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(right_col_x + 5, y_pos - 11, "Consignee (Ship To)")
        
        # Buyer details box
        buyer_box_height = 50
        c.setStrokeColorRGB(0.35, 0.22, 0.15)
        c.setLineWidth(0.5)
        c.rect(left_col_x, y_pos - 15 - buyer_box_height, col_width, buyer_box_height, stroke=1, fill=0)
        
        # Consignee details box
        c.rect(right_col_x, y_pos - 15 - buyer_box_height, col_width, buyer_box_height, stroke=1, fill=0)
        
        # Buyer content
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 8)
        buyer_y = y_pos - 28
        c.drawString(left_col_x + 5, buyer_y, invoice.get('customer_name', '')[:35])
        
        c.setFont("Helvetica", 7)
        buyer_y -= 10
        c.drawString(left_col_x + 5, buyer_y, f"Phone: {invoice.get('customer_phone', '')}")
        
        buyer_y -= 10
        address = invoice.get('customer_address', '')
        if len(address) > 45:
            c.drawString(left_col_x + 5, buyer_y, address[:45])
            buyer_y -= 9
            c.drawString(left_col_x + 5, buyer_y, address[45:90])
        else:
            c.drawString(left_col_x + 5, buyer_y, address)
        
        if invoice.get('customer_gstin'):
            buyer_y -= 10
            c.drawString(left_col_x + 5, buyer_y, f"GSTIN: {invoice['customer_gstin']}")
        
        # Consignee content (if different from buyer)
        consignee_name = invoice.get('consignee_name') or invoice.get('customer_name', '')
        consignee_phone = invoice.get('consignee_phone') or invoice.get('customer_phone', '')
        consignee_address = invoice.get('consignee_address') or invoice.get('customer_address', '')
        
        c.setFont("Helvetica-Bold", 8)
        consignee_y = y_pos - 28
        c.drawString(right_col_x + 5, consignee_y, consignee_name[:35])
        
        c.setFont("Helvetica", 7)
        consignee_y -= 10
        c.drawString(right_col_x + 5, consignee_y, f"Phone: {consignee_phone}")
        
        consignee_y -= 10
        if len(consignee_address) > 45:
            c.drawString(right_col_x + 5, consignee_y, consignee_address[:45])
            consignee_y -= 9
            c.drawString(right_col_x + 5, consignee_y, consignee_address[45:90])
        else:
            c.drawString(right_col_x + 5, consignee_y, consignee_address)
        
        y_pos = y_pos - 15 - buyer_box_height - 10
        
        # ==================== ITEMS TABLE ====================
        
        # Table column positions (matching template)
        table_left = 40
        table_right = width - 40
        table_width = table_right - table_left
        
        # Column widths as percentages (matching template analysis)
        col_widths = {
            'sr': 0.04 * table_width,
            'name': 0.18 * table_width,
            'image': 0.10 * table_width,
            'size': 0.10 * table_width,
            'rate_box': 0.10 * table_width,
            'rate_sqft': 0.10 * table_width,
            'quantity': 0.10 * table_width,
            'disc': 0.08 * table_width,
            'amount': 0.12 * table_width
        }
        
        # Calculate column positions
        col_sr = table_left
        col_name = col_sr + col_widths['sr']
        col_image = col_name + col_widths['name']
        col_size = col_image + col_widths['image']
        col_rate_box = col_size + col_widths['size']
        col_rate_sqft = col_rate_box + col_widths['rate_box']
        col_qty = col_rate_sqft + col_widths['rate_sqft']
        col_disc = col_qty + col_widths['quantity']
        col_amount = col_disc + col_widths['disc']
        
        # Table header with brown background
        header_height = 18
        c.setFillColorRGB(0.35, 0.22, 0.15)  # Dark brown
        c.rect(table_left, y_pos - header_height, table_width, header_height, fill=1, stroke=0)
        
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 7)
        header_y = y_pos - 12
        
        c.drawString(col_sr + 2, header_y, "SR NO.")
        c.drawString(col_name + 2, header_y, "NAME")
        c.drawString(col_image + 2, header_y, "IMAGE")
        c.drawString(col_size + 2, header_y, "SIZE")
        c.drawString(col_rate_box + 2, header_y, "RATE/BOX")
        c.drawString(col_rate_sqft + 2, header_y, "RATE/SQFT")
        c.drawString(col_qty + 2, header_y, "QUANTITY")
        c.drawString(col_disc + 2, header_y, "DISC.(%)")
        c.drawString(col_amount + 2, header_y, "AMOUNT")
        
        y_pos -= header_height
        
        # Draw vertical lines for table structure
        c.setStrokeColorRGB(0.35, 0.22, 0.15)
        c.setLineWidth(0.3)
        
        # Group items by location
        grouped_items = {}
        for item in invoice['line_items']:
            location = item.get('location', 'Items')
            if location not in grouped_items:
                grouped_items[location] = []
            grouped_items[location].append(item)
        
        table_start_y = y_pos
        
        for location, items in grouped_items.items():
            # RESET SR. NO. for each location group
            sr_no = 1
            
            # Location header row
            c.setFillColorRGB(0.9, 0.85, 0.8)  # Light brown/beige
            c.rect(table_left, y_pos - 16, table_width, 16, fill=1, stroke=0)
            
            c.setFillColorRGB(0.35, 0.22, 0.15)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(table_left + 5, y_pos - 11, location.upper())
            
            y_pos -= 16
            location_subtotal = 0
            
            for item in items:
                # Check for page break
                if y_pos < 180:
                    c.showPage()
                    y_pos = height - 50
                    # Redraw table header on new page
                    c.setFillColorRGB(0.35, 0.22, 0.15)
                    c.rect(table_left, y_pos - header_height, table_width, header_height, fill=1, stroke=0)
                    c.setFillColorRGB(1, 1, 1)
                    c.setFont("Helvetica-Bold", 7)
                    header_y = y_pos - 12
                    c.drawString(col_sr + 2, header_y, "SR NO.")
                    c.drawString(col_name + 2, header_y, "NAME")
                    c.drawString(col_image + 2, header_y, "IMAGE")
                    c.drawString(col_size + 2, header_y, "SIZE")
                    c.drawString(col_rate_box + 2, header_y, "RATE/BOX")
                    c.drawString(col_rate_sqft + 2, header_y, "RATE/SQFT")
                    c.drawString(col_qty + 2, header_y, "QUANTITY")
                    c.drawString(col_disc + 2, header_y, "DISC.(%)")
                    c.drawString(col_amount + 2, header_y, "AMOUNT")
                    y_pos -= header_height
                
                row_height = 45 if item.get('tile_image') else 18
                
                # Row background (alternating)
                if sr_no % 2 == 0:
                    c.setFillColorRGB(0.98, 0.97, 0.97)
                    c.rect(table_left, y_pos - row_height, table_width, row_height, fill=1, stroke=0)
                
                # Draw row border
                c.setStrokeColorRGB(0.8, 0.8, 0.8)
                c.setLineWidth(0.3)
                c.line(table_left, y_pos - row_height, table_right, y_pos - row_height)
                
                # Row content
                c.setFillColorRGB(0, 0, 0)
                text_y = y_pos - 12 if not item.get('tile_image') else y_pos - 30
                
                c.setFont("Helvetica", 7)
                c.drawString(col_sr + 2, text_y, str(sr_no))
                
                tile_name = item.get('tile_name') or item.get('product_name') or ''
                c.drawString(col_name + 2, text_y, tile_name[:20])
                
                # Draw image if exists
                if item.get('tile_image'):
                    try:
                        if item['tile_image'].startswith('data:image'):
                            image_data = item['tile_image'].split(',')[1]
                        else:
                            image_data = item['tile_image']
                        
                        image_bytes = base64.b64decode(image_data)
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                            tmp_file.write(image_bytes)
                            tmp_path = tmp_file.name
                        
                        img = Image.open(tmp_path)
                        img_w, img_h = img.size
                        
                        max_w, max_h = 35, 35
                        aspect = img_w / img_h
                        if aspect > 1:
                            draw_w = max_w
                            draw_h = max_w / aspect
                        else:
                            draw_h = max_h
                            draw_w = max_h * aspect
                        
                        img_x = col_image + (col_widths['image'] - draw_w) / 2
                        img_y = y_pos - row_height + 5
                        
                        c.drawImage(tmp_path, img_x, img_y, width=draw_w, height=draw_h,
                                  preserveAspectRatio=True, mask='auto')
                        
                        os_module.unlink(tmp_path)
                    except Exception as e:
                        logger.warning(f"Error drawing tile image: {e}")
                
                c.drawString(col_size + 2, text_y, item.get('size', '')[:12])
                
                # Format rates with Rupee symbol
                rate_box = item.get('rate_per_box', 0)
                rate_sqft = item.get('rate_per_sqft', 0)
                
                if use_dejavusans:
                    try:
                        c.setFont("DejaVuSans", 7)
                        c.drawString(col_rate_box + 2, text_y, f"₹{rate_box:.0f}")
                        c.drawString(col_rate_sqft + 2, text_y, f"₹{rate_sqft:.0f}")
                    except:
                        c.setFont("Helvetica", 7)
                        c.drawString(col_rate_box + 2, text_y, f"Rs.{rate_box:.0f}")
                        c.drawString(col_rate_sqft + 2, text_y, f"Rs.{rate_sqft:.0f}")
                else:
                    c.setFont("Helvetica", 7)
                    c.drawString(col_rate_box + 2, text_y, f"Rs.{rate_box:.0f}")
                    c.drawString(col_rate_sqft + 2, text_y, f"Rs.{rate_sqft:.0f}")
                
                c.setFont("Helvetica", 7)
                qty_text = f"{item.get('box_qty', 0)} box"
                if item.get('extra_sqft', 0) > 0:
                    qty_text += f" +{item['extra_sqft']:.1f}sqft"
                c.drawString(col_qty + 2, text_y, qty_text[:15])
                
                c.drawString(col_disc + 2, text_y, f"{item.get('discount_percent', 0):.0f}%")
                
                final_amount = item.get('final_amount', 0)
                if use_dejavusans:
                    try:
                        c.setFont("DejaVuSans", 7)
                        c.drawString(col_amount + 2, text_y, f"₹{final_amount:.2f}")
                    except:
                        c.setFont("Helvetica", 7)
                        c.drawString(col_amount + 2, text_y, f"Rs.{final_amount:.2f}")
                else:
                    c.setFont("Helvetica", 7)
                    c.drawString(col_amount + 2, text_y, f"Rs.{final_amount:.2f}")
                
                location_subtotal += final_amount
                y_pos -= row_height
                sr_no += 1
            
            # Location subtotal row
            c.setFillColorRGB(0.95, 0.93, 0.9)
            c.rect(table_left, y_pos - 16, table_width, 16, fill=1, stroke=0)
            
            c.setFillColorRGB(0.35, 0.22, 0.15)
            c.setFont("Helvetica-Bold", 8)
            c.drawRightString(col_amount - 5, y_pos - 11, f"{location}'s Total Amount:")
            
            if use_dejavusans:
                try:
                    c.setFont("DejaVuSans-Bold", 8)
                    c.drawString(col_amount + 2, y_pos - 11, f"₹{location_subtotal:.2f}")
                except:
                    c.setFont("Helvetica-Bold", 8)
                    c.drawString(col_amount + 2, y_pos - 11, f"Rs.{location_subtotal:.2f}")
            else:
                c.setFont("Helvetica-Bold", 8)
                c.drawString(col_amount + 2, y_pos - 11, f"Rs.{location_subtotal:.2f}")
            
            y_pos -= 18
        
        # ==================== TOTALS SECTION ====================
        y_pos -= 5
        
        totals_x = table_right - 200
        
        # Total Amount
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 9)
        c.drawRightString(totals_x + 100, y_pos, "Total Amount :")
        if use_dejavusans:
            try:
                c.setFont("DejaVuSans", 9)
                c.drawString(totals_x + 105, y_pos, f"₹{invoice.get('subtotal', 0):.2f}")
            except:
                c.setFont("Helvetica", 9)
                c.drawString(totals_x + 105, y_pos, f"Rs.{invoice.get('subtotal', 0):.2f}")
        else:
            c.setFont("Helvetica", 9)
            c.drawString(totals_x + 105, y_pos, f"Rs.{invoice.get('subtotal', 0):.2f}")
        
        y_pos -= 14
        
        # Transport Charges
        c.setFont("Helvetica", 9)
        c.drawRightString(totals_x + 100, y_pos, "Transport Charges :")
        transport = invoice.get('transport_charges', 0)
        if use_dejavusans:
            try:
                c.setFont("DejaVuSans", 9)
                c.drawString(totals_x + 105, y_pos, f"₹{transport:.2f}")
            except:
                c.setFont("Helvetica", 9)
                c.drawString(totals_x + 105, y_pos, f"Rs.{transport:.2f}")
        else:
            c.setFont("Helvetica", 9)
            c.drawString(totals_x + 105, y_pos, f"Rs.{transport:.2f}")
        
        y_pos -= 14
        
        # Unloading Charges
        c.setFont("Helvetica", 9)
        c.drawRightString(totals_x + 100, y_pos, "Unloading Charges :")
        unloading = invoice.get('unloading_charges', 0)
        if use_dejavusans:
            try:
                c.setFont("DejaVuSans", 9)
                c.drawString(totals_x + 105, y_pos, f"₹{unloading:.2f}")
            except:
                c.setFont("Helvetica", 9)
                c.drawString(totals_x + 105, y_pos, f"Rs.{unloading:.2f}")
        else:
            c.setFont("Helvetica", 9)
            c.drawString(totals_x + 105, y_pos, f"Rs.{unloading:.2f}")
        
        y_pos -= 14
        
        # GST Amount section
        gst_amount = invoice.get('gst_amount', 0)
        gst_percent = invoice.get('gst_percent', 0)
        
        c.setFont("Helvetica", 9)
        if gst_percent > 0 or gst_amount > 0:
            # GST is provided - show normal GST row
            c.drawRightString(totals_x + 100, y_pos, f"GST Amount ({gst_percent:.0f}%) :")
            if use_dejavusans:
                try:
                    c.setFont("DejaVuSans", 9)
                    c.drawString(totals_x + 105, y_pos, f"₹{gst_amount:.2f}")
                except:
                    c.setFont("Helvetica", 9)
                    c.drawString(totals_x + 105, y_pos, f"Rs.{gst_amount:.2f}")
            else:
                c.setFont("Helvetica", 9)
                c.drawString(totals_x + 105, y_pos, f"Rs.{gst_amount:.2f}")
        else:
            # GST is empty - show placeholder text
            c.drawRightString(totals_x + 100, y_pos, "GST :")
            c.setFont("Helvetica-Oblique", 8)
            c.setFillColorRGB(0.5, 0.5, 0.5)  # Gray color for placeholder
            c.drawString(totals_x + 105, y_pos, "Would be applied at the time of billing")
            c.setFillColorRGB(0, 0, 0)  # Reset to black
        y_pos -= 14
        
        # Final Amount (highlighted)
        c.setFillColorRGB(0.35, 0.22, 0.15)
        c.rect(totals_x - 10, y_pos - 5, 210, 20, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(totals_x + 100, y_pos + 3, "Final Amount:")
        grand_total = invoice.get('grand_total', 0)
        if use_dejavusans:
            try:
                c.setFont("DejaVuSans-Bold", 10)
                c.drawString(totals_x + 105, y_pos + 3, f"₹{grand_total:.2f}")
            except:
                c.setFont("Helvetica-Bold", 10)
                c.drawString(totals_x + 105, y_pos + 3, f"Rs.{grand_total:.2f}")
        else:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(totals_x + 105, y_pos + 3, f"Rs.{grand_total:.2f}")
        
        y_pos -= 25
        
        # ==================== OVERALL REMARKS (if present) ====================
        remarks = invoice.get('overall_remarks', '')
        if remarks:
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(40, y_pos, "Overall Remarks:")
            y_pos -= 12
            c.setFont("Helvetica", 8)
            # Handle multi-line remarks
            words = remarks.split()
            line = ""
            for word in words:
                if c.stringWidth(line + " " + word, "Helvetica", 8) < table_width - 20:
                    line = line + " " + word if line else word
                else:
                    c.drawString(45, y_pos, line)
                    y_pos -= 10
                    line = word
            if line:
                c.drawString(45, y_pos, line)
            y_pos -= 15
        
        # ==================== BANK DETAILS ====================
        if y_pos < 200:
            c.showPage()
            y_pos = height - 50
        
        c.setFillColorRGB(0.35, 0.22, 0.15)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(40, y_pos, "Bank Details")
        y_pos -= 3
        
        # Bank details box
        bank_box_height = 55
        c.setStrokeColorRGB(0.35, 0.22, 0.15)
        c.setLineWidth(0.5)
        c.rect(40, y_pos - bank_box_height, 250, bank_box_height, stroke=1, fill=0)
        
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 8)
        bank_y = y_pos - 12
        
        c.drawString(45, bank_y, "Account Name:")
        c.setFont("Helvetica-Bold", 8)
        c.drawString(120, bank_y, "SHREE SONANA SHETRPAL CERAMIC")
        
        bank_y -= 10
        c.setFont("Helvetica", 8)
        c.drawString(45, bank_y, "Bank Name:")
        c.setFont("Helvetica-Bold", 8)
        c.drawString(120, bank_y, "HDFC BANK")
        
        bank_y -= 10
        c.setFont("Helvetica", 8)
        c.drawString(45, bank_y, "Account No.:")
        c.setFont("Helvetica-Bold", 8)
        c.drawString(120, bank_y, "50200069370271")
        
        bank_y -= 10
        c.setFont("Helvetica", 8)
        c.drawString(45, bank_y, "IFSC:")
        c.setFont("Helvetica-Bold", 8)
        c.drawString(120, bank_y, "HDFC0005291")
        
        bank_y -= 10
        c.setFont("Helvetica", 8)
        c.drawString(45, bank_y, "Branch:")
        c.setFont("Helvetica-Bold", 8)
        c.drawString(120, bank_y, "HYDE PARK")
        
        y_pos -= (bank_box_height + 15)
        
        # ==================== TERMS & CONDITIONS ====================
        c.setFillColorRGB(0.35, 0.22, 0.15)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(40, y_pos, "TERMS & CONDITION")
        y_pos -= 12
        
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 7)
        
        terms = [
            "1. Payment: 100% Advance",
            "2. 2% Breakage mandatory",
            "3. Delivery: 8-10 days as per availability.",
            "4. Quotation Price valid for fifteen days.",
            "5. Goods once sold will not be taken back or exchanged.",
            "6. Quality complaints will not be entertained unless laid as instructed.",
            "7. We are not responsible for any damage during transit.",
            "8. Batch wise variation is inherent characteristic of ceramic, NO COMPLAINTS WILL BE ENTERTAINED AFTER INSTALLATION OF TILES.",
            "9. Our responsibility ceases after the dispatch of goods from our premises."
        ]
        
        for term in terms:
            if y_pos < 60:
                c.showPage()
                y_pos = height - 50
            c.drawString(45, y_pos, term)
            y_pos -= 10
        
        # ==================== BRAND LOGOS FOOTER ====================
        # Simple footer line
        c.setStrokeColorRGB(0.35, 0.22, 0.15)
        c.setLineWidth(0.5)
        c.line(40, 45, width - 40, 45)
        
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.setFont("Helvetica-Oblique", 7)
        c.drawCentredString(width / 2, 35, "Thank you for your business! - THE TILE SHOP")
        
        c.setFont("Helvetica", 6)
        c.drawString(40, 25, "Generated on: " + datetime.now().strftime("%d/%m/%Y %H:%M"))
        c.drawRightString(width - 40, 25, "Page 1")
        
        # Save PDF
        c.save()
        logger.info(f"PDF generated successfully matching template: {output_path}")
        
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        import traceback
        logger.error(traceback.format_exc())
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
