"""
PRO Invoice Engine - PDF Generation
=====================================

Features:
- Template PDF pages as background (page1 + continuation)
- All text/images drawn with drawTextInBox/drawImageInBox helpers
- Multiple sections support (SA, KITCHEN, etc.)
- Template label replacement with background rect overlay
- Item rows using y = startY - rowIndex*rowH
- Auto-pagination when near safeBottomY
- Stable output for 1, 10, 50+ items
"""

import io
import json
import base64
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional, Literal
from datetime import datetime
import logging

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import A4

logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================

ROOT_DIR = Path(__file__).parent.parent

def load_template_map(page_type: Literal["page1", "cont"]) -> dict:
    """Load template map for page type"""
    filename = f"template_map.{page_type}.json"
    path = ROOT_DIR / "assets" / "pdf" / filename
    with open(path, 'r') as f:
        return json.load(f)

MAP_PAGE1 = None
MAP_CONT = None

def get_maps():
    """Lazy load template maps"""
    global MAP_PAGE1, MAP_CONT
    if MAP_PAGE1 is None:
        MAP_PAGE1 = load_template_map("page1")
    if MAP_CONT is None:
        MAP_CONT = load_template_map("cont")
    return MAP_PAGE1, MAP_CONT

# ==================== HELPER FUNCTIONS ====================

def cover_box(canvas, box: dict, bg_color: tuple):
    """
    Draw background-colored rectangle to cover template text.
    
    Args:
        canvas: ReportLab canvas
        box: dict with x, y, w, h (ReportLab coords: y from bottom)
        bg_color: RGB tuple (0-1 scale)
    """
    canvas.setFillColorRGB(*bg_color)
    canvas.rect(box['x'], box['y'], box['w'], box['h'], fill=True, stroke=False)


def draw_text_in_box(canvas, text: str, box: dict, options: dict = None):
    """
    Draw text inside a bounding box with alignment, shrink-to-fit, and optional wrap.
    
    Args:
        canvas: ReportLab canvas
        text: Text to draw
        box: dict with x, y, w, h, align
        options: {size, font, color, pad, shrink, wrap}
    """
    opts = options or {}
    size = opts.get('size', 7)
    font = opts.get('font', 'Helvetica')
    color = opts.get('color', (0, 0, 0))
    pad = opts.get('pad', 2)
    shrink = opts.get('shrink', True)
    wrap = opts.get('wrap', False)
    
    align = box.get('align', 'left')
    x = box['x']
    y = box['y']
    w = box['w']
    h = box['h']
    
    canvas.setFont(font, size)
    canvas.setFillColorRGB(*color)
    
    text = str(text) if text else ''
    
    # Shrink to fit if needed
    if shrink and text:
        text_width = canvas.stringWidth(text, font, size)
        max_width = w - pad * 2
        while text_width > max_width and len(text) > 3:
            text = text[:-1]
            text_width = canvas.stringWidth(text + "..", font, size)
        if canvas.stringWidth(text, font, size) > max_width:
            text = text[:-2] + ".."
    
    # Calculate text position (baseline)
    text_y = y + (h / 2) - (size / 3)
    
    if align == 'center':
        text_x = x + w / 2
        canvas.drawCentredString(text_x, text_y, text)
    elif align == 'right':
        text_x = x + w - pad
        canvas.drawRightString(text_x, text_y, text)
    else:  # left
        text_x = x + pad
        canvas.drawString(text_x, text_y, text)


def draw_currency_in_box(canvas, value: float, box: dict, options: dict = None):
    """
    Draw currency value with Rupee symbol inside box.
    """
    opts = options or {}
    size = opts.get('size', 7)
    bold = opts.get('bold', False)
    
    # Try DejaVuSans for Rupee, fallback to Helvetica
    try:
        from reportlab.pdfbase import pdfmetrics
        pdfmetrics.getFont("DejaVuSans")
        font = "DejaVuSans"
    except:
        font = "Helvetica-Bold" if bold else "Helvetica"
    
    formatted = f"₹{round(value):,}"
    
    draw_text_in_box(canvas, formatted, box, {
        'size': size,
        'font': font,
        'color': (0, 0, 0),
        **opts
    })


def draw_image_in_box(canvas, image_data: str, box: dict, padding: int = 2):
    """
    Draw image inside bounding box with padding.
    """
    try:
        if not image_data:
            return
            
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        
        img_w = box.get('imgW', box['w'] - padding * 2)
        img_h = box.get('imgH', box['h'] - padding * 2)
        img_x = box['x'] + (box['w'] - img_w) / 2
        img_y = box['y'] + (box['h'] - img_h) / 2
        
        canvas.drawImage(
            tmp_path,
            img_x, img_y,
            width=img_w, height=img_h,
            preserveAspectRatio=True,
            mask='auto'
        )
        
        os.unlink(tmp_path)
    except Exception as e:
        logger.warning(f"Error drawing image: {e}")


# ==================== PRO INVOICE ENGINE ====================

class ProInvoiceEngine:
    """
    PRO Invoice Engine with template overlay and multi-section support.
    """
    
    def __init__(self, template_path: Path = None):
        self.template_path = template_path or (ROOT_DIR / "assets" / "invoice-template.pdf")
        self.map_p1, self.map_cont = get_maps()
        self.bg_color = tuple(self.map_p1['background']['color'])
        
    def generate(self, invoice_data: dict, output_path: str) -> str:
        """
        Generate invoice PDF with template overlay.
        
        Args:
            invoice_data: Invoice data with sections
            output_path: Output file path
            
        Returns:
            Output path
        """
        # Normalize invoice data to grouped model
        data = self._normalize_data(invoice_data)
        
        # Create pages
        pages = []
        current_page = self._new_page_overlay("page1")
        pages.append(current_page)
        
        # Render header on first page
        self._render_header(current_page['canvas'], data)
        
        # Track Y position (ReportLab: y decreases going down)
        y = self.map_p1['table']['startY']
        page_type = "page1"
        current_map = self.map_p1
        
        # Render all sections
        for section in data['sections']:
            section_name = section['name']
            items = section['items']
            
            # Calculate section total
            section_total = sum(item.get('amountNumeric', 0) for item in items)
            
            # Section header row
            row_h = current_map['table']['rowH']
            
            # Check if need new page for section header
            if y - row_h < current_map['page']['safeBottomY']:
                current_page = self._new_page_overlay("cont")
                pages.append(current_page)
                page_type = "cont"
                current_map = self.map_cont
                y = current_map['table']['startY']
            
            # Draw section header
            self._render_section_header(current_page['canvas'], section_name, y, current_map)
            y -= row_h
            
            # Render items
            sr = 1
            for item in items:
                has_image = bool(item.get('image'))
                item_row_h = current_map['table']['rowHWithImage'] if has_image else row_h
                
                # Check if need new page for item
                if y - item_row_h < current_map['page']['safeBottomY']:
                    current_page = self._new_page_overlay("cont")
                    pages.append(current_page)
                    page_type = "cont"
                    current_map = self.map_cont
                    y = current_map['table']['startY']
                
                # Draw item row
                self._render_item_row(current_page['canvas'], item, sr, y, item_row_h, current_map)
                y -= item_row_h
                sr += 1
            
            # Section total row
            total_row_h = row_h
            if y - total_row_h < current_map['page']['safeBottomY']:
                current_page = self._new_page_overlay("cont")
                pages.append(current_page)
                page_type = "cont"
                current_map = self.map_cont
                y = current_map['table']['startY']
            
            # Draw section total
            self._render_section_total(current_page['canvas'], section_name, section_total, y, current_map)
            y -= total_row_h + 5  # Extra spacing between sections
        
        # Footer on last page
        self._render_footer(current_page['canvas'], data, page_type)
        
        # Add page numbers
        total_pages = len(pages)
        for i, page in enumerate(pages):
            if total_pages > 1:
                self._render_page_number(page['canvas'], i + 1, total_pages, data['quotationNo'])
        
        # Finalize all canvases
        for page in pages:
            page['canvas'].save()
        
        # Merge overlays with template
        writer = PdfWriter()
        
        for i, page in enumerate(pages):
            # Load fresh template for each page
            template_reader = PdfReader(str(self.template_path))
            template_page = template_reader.pages[0]
            
            # Read overlay
            page['buffer'].seek(0)
            overlay_reader = PdfReader(page['buffer'])
            
            if len(overlay_reader.pages) > 0:
                template_page.merge_page(overlay_reader.pages[0])
            
            writer.add_page(template_page)
        
        # Write output
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        logger.info(f"PRO Invoice generated: {output_path} ({total_pages} pages)")
        return output_path
    
    def _normalize_data(self, invoice: dict) -> dict:
        """
        Normalize invoice data to grouped sections model.
        """
        # If already has sections, use as-is
        if 'sections' in invoice:
            # Ensure amountNumeric is computed
            for section in invoice['sections']:
                for item in section['items']:
                    if 'amountNumeric' not in item:
                        item['amountNumeric'] = item.get('final_amount', 0)
            return invoice
        
        # Convert from line_items to sections
        sections_dict = {}
        for item in invoice.get('line_items', []):
            location = item.get('location', 'Items')
            if location not in sections_dict:
                sections_dict[location] = []
            
            # Map old field names to new
            normalized_item = {
                'name': item.get('tile_name') or item.get('product_name', ''),
                'size': item.get('size', ''),
                'rateBox': item.get('rate_per_box', 0),
                'rateSqft': item.get('rate_per_sqft', 0),
                'qty': f"{item.get('box_qty', 0)} box",
                'disc': f"{round(item.get('discount_percent', 0))}%",
                'amount': item.get('final_amount', 0),
                'amountNumeric': item.get('final_amount', 0),
                'image': item.get('tile_image', '')
            }
            sections_dict[location].append(normalized_item)
        
        sections = [{'name': name, 'items': items} for name, items in sections_dict.items()]
        
        return {
            'quotationNo': invoice.get('invoice_id', ''),
            'date': invoice.get('invoice_date'),
            'referenceName': invoice.get('reference_name', ''),
            'buyer': {
                'name': invoice.get('customer_name', ''),
                'phone': invoice.get('customer_phone', ''),
                'address': invoice.get('customer_address', ''),
                'gstin': invoice.get('customer_gstin', '')
            },
            'consignee': {
                'name': invoice.get('consignee_name') or invoice.get('customer_name', ''),
                'phone': invoice.get('consignee_phone') or invoice.get('customer_phone', ''),
                'address': invoice.get('consignee_address') or invoice.get('customer_address', '')
            },
            'sections': sections,
            'charges': {
                'transport': invoice.get('transport_charges', 0),
                'unloading': invoice.get('unloading_charges', 0)
            },
            'subtotal': invoice.get('subtotal', 0),
            'gstAmount': invoice.get('gst_amount', 0),
            'grandTotal': invoice.get('grand_total', 0),
            'remarks': invoice.get('overall_remarks', '')
        }
    
    def _new_page_overlay(self, page_type: str) -> dict:
        """Create new overlay buffer and canvas"""
        buffer = io.BytesIO()
        canvas = rl_canvas.Canvas(buffer, pagesize=A4)
        return {
            'buffer': buffer,
            'canvas': canvas,
            'type': page_type
        }
    
    def _render_header(self, canvas, data: dict):
        """Render header content on page 1"""
        header = self.map_p1['header']
        buyer = self.map_p1['buyer']
        consignee = self.map_p1['consignee']
        
        # Quotation number
        draw_text_in_box(canvas, data['quotationNo'], header['quotationNo'], 
                        {'size': 7.5, 'font': 'Helvetica-Bold'})
        
        # Date
        date = data.get('date')
        if date:
            if isinstance(date, str):
                try:
                    date = datetime.fromisoformat(date)
                except:
                    pass
            if isinstance(date, datetime):
                date = date.strftime("%d/%m/%Y")
            draw_text_in_box(canvas, str(date), header['date'], {'size': 7.5, 'font': 'Helvetica-Bold'})
        
        # Reference name
        if data.get('referenceName'):
            draw_text_in_box(canvas, data['referenceName'], header['reference'], {'size': 7.5})
        
        # Buyer details
        b = data.get('buyer', {})
        draw_text_in_box(canvas, b.get('name', ''), buyer['name'], 
                        {'size': 7.5, 'font': 'Helvetica-Bold'})
        draw_text_in_box(canvas, f"Ph: {b.get('phone', '')}", buyer['phone'], {'size': 7})
        
        addr = b.get('address', '')
        draw_text_in_box(canvas, addr[:40], buyer['address1'], {'size': 7})
        if len(addr) > 40:
            draw_text_in_box(canvas, addr[40:80], buyer['address2'], {'size': 7})
        
        if b.get('gstin'):
            draw_text_in_box(canvas, f"GSTIN: {b['gstin']}", buyer['gstin'], {'size': 7})
        
        # Consignee details
        c = data.get('consignee', {})
        draw_text_in_box(canvas, c.get('name', ''), consignee['name'], 
                        {'size': 7.5, 'font': 'Helvetica-Bold'})
        draw_text_in_box(canvas, f"Ph: {c.get('phone', '')}", consignee['phone'], {'size': 7})
        
        c_addr = c.get('address', '')
        draw_text_in_box(canvas, c_addr[:40], consignee['address1'], {'size': 7})
        if len(c_addr) > 40:
            draw_text_in_box(canvas, c_addr[40:80], consignee['address2'], {'size': 7})
    
    def _render_section_header(self, canvas, section_name: str, y: float, map_: dict):
        """Render section header row (replaces 'MAIN FLOOR')"""
        title_box = map_['section']['titleBox'].copy()
        title_box['y'] = y - title_box['h']
        
        # Cover template text
        cover_box(canvas, title_box, self.bg_color)
        
        # Draw section name
        draw_text_in_box(canvas, section_name.upper(), title_box, {
            'size': 9,
            'font': 'Helvetica-Bold',
            'color': (0.35, 0.22, 0.15)  # Brown
        })
    
    def _render_item_row(self, canvas, item: dict, sr: int, y: float, row_h: float, map_: dict):
        """Render single item row in table grid"""
        cols = map_['table']['cols']
        
        def col_box(col_name: str) -> dict:
            c = cols[col_name]
            return {
                'x': c['x'],
                'y': y - row_h,
                'w': c['w'],
                'h': row_h,
                'align': c.get('align', 'left'),
                'imgW': c.get('imgW'),
                'imgH': c.get('imgH')
            }
        
        # SR NO
        draw_text_in_box(canvas, str(sr), col_box('sr'), {'size': 7})
        
        # NAME
        draw_text_in_box(canvas, item.get('name', '')[:15], col_box('name'), {'size': 7})
        
        # IMAGE
        if item.get('image'):
            img_box = col_box('image')
            img_box['imgW'] = cols['image'].get('imgW', 30)
            img_box['imgH'] = cols['image'].get('imgH', 30)
            draw_image_in_box(canvas, item['image'], img_box)
        
        # SIZE
        draw_text_in_box(canvas, item.get('size', '')[:20], col_box('size'), {'size': 7})
        
        # RATE/BOX
        rate_box = item.get('rateBox', 0)
        if isinstance(rate_box, str):
            draw_text_in_box(canvas, rate_box, col_box('rateBox'), {'size': 6})
        else:
            draw_currency_in_box(canvas, rate_box, col_box('rateBox'), {'size': 6})
        
        # RATE/SQFT
        rate_sqft = item.get('rateSqft', 0)
        if isinstance(rate_sqft, str):
            draw_text_in_box(canvas, rate_sqft, col_box('rateSqft'), {'size': 6})
        else:
            draw_currency_in_box(canvas, rate_sqft, col_box('rateSqft'), {'size': 6})
        
        # QTY
        draw_text_in_box(canvas, item.get('qty', ''), col_box('qty'), {'size': 6})
        
        # DISC
        draw_text_in_box(canvas, item.get('disc', ''), col_box('disc'), {'size': 6})
        
        # AMOUNT
        amount = item.get('amount', 0) or item.get('amountNumeric', 0)
        if isinstance(amount, str):
            draw_text_in_box(canvas, amount, col_box('amount'), {'size': 7, 'font': 'Helvetica-Bold'})
        else:
            draw_currency_in_box(canvas, amount, col_box('amount'), {'size': 7, 'bold': True})
    
    def _render_section_total(self, canvas, section_name: str, total: float, y: float, map_: dict):
        """Render section total row (replaces 'MAIN FLOOR's Total Amount')"""
        section = map_['section']
        
        # Label box
        label_box = section['totalLabel'].copy()
        label_box['y'] = y - label_box['h']
        
        # Value box
        value_box = section['totalValue'].copy()
        value_box['y'] = y - value_box['h']
        
        # Cover template label
        cover_box(canvas, label_box, self.bg_color)
        
        # Draw new label
        draw_text_in_box(canvas, f"{section_name}'s Total Amount", label_box, {
            'size': 8,
            'font': 'Helvetica-Bold',
            'color': (0.35, 0.22, 0.15)
        })
        
        # Draw value
        draw_currency_in_box(canvas, total, value_box, {'size': 8, 'bold': True})
    
    def _render_footer(self, canvas, data: dict, page_type: str):
        """Render footer content (financial summary, remarks)"""
        if page_type == "cont":
            return  # Footer only on page with space
        
        footer = self.map_p1.get('footer', {})
        
        # Total Amount
        if 'totalAmount' in footer:
            draw_currency_in_box(canvas, data.get('subtotal', 0), footer['totalAmount'], {'size': 7.5})
        
        # Transport
        if 'transport' in footer:
            draw_currency_in_box(canvas, data.get('charges', {}).get('transport', 0), footer['transport'], {'size': 7.5})
        
        # Unloading
        if 'unloading' in footer:
            draw_currency_in_box(canvas, data.get('charges', {}).get('unloading', 0), footer['unloading'], {'size': 7.5})
        
        # GST
        if 'gst' in footer:
            gst = data.get('gstAmount', 0)
            if gst > 0:
                draw_currency_in_box(canvas, gst, footer['gst'], {'size': 7.5})
            else:
                draw_text_in_box(canvas, "As applicable", footer['gst'], {
                    'size': 7,
                    'font': 'Helvetica-Oblique',
                    'color': (0.4, 0.4, 0.4)
                })
        
        # Final Amount
        if 'finalAmount' in footer:
            canvas.setFillColorRGB(1, 1, 1)  # White on brown background
            draw_currency_in_box(canvas, data.get('grandTotal', 0), footer['finalAmount'], {
                'size': 8,
                'bold': True,
                'color': (1, 1, 1)
            })
        
        # Remarks
        remarks = data.get('remarks', '')
        if remarks and 'remarks' in footer:
            draw_text_in_box(canvas, remarks[:200], footer['remarks'], {'size': 7})
    
    def _render_page_number(self, canvas, page_num: int, total_pages: int, invoice_id: str):
        """Add page number to multi-page invoices"""
        if total_pages <= 1:
            return
        
        # Page info in top-right
        text = f"{invoice_id} (Page {page_num}/{total_pages})"
        canvas.setFont("Helvetica", 7)
        canvas.setFillColorRGB(0.3, 0.3, 0.3)
        canvas.drawRightString(570, 825, text)


# ==================== FACTORY FUNCTION ====================

def generate_invoice_pdf(invoice: dict, output_path: str):
    """
    Generate invoice PDF using PRO Invoice Engine.
    
    This is the main entry point, compatible with existing API.
    """
    engine = ProInvoiceEngine()
    return engine.generate(invoice, output_path)
