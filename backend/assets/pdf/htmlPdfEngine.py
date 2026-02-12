"""
HTML-based Invoice PDF Generator
=================================

Generates invoices using HTML templates and WeasyPrint for clean, professional PDFs.
"""

import os
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import logging

logger = logging.getLogger(__name__)

# Template directory
TEMPLATE_DIR = Path(__file__).parent


def generate_invoice_pdf_html(invoice: dict, output_path: str) -> str:
    """
    Generate invoice PDF from HTML template using WeasyPrint.
    
    Args:
        invoice: Invoice data dictionary
        output_path: Output PDF file path
        
    Returns:
        Output path
    """
    try:
        # Normalize invoice data
        logger.info("Normalizing invoice data...")
        data = _normalize_invoice_data(invoice)
        
        # Setup Jinja2 environment
        logger.info(f"Loading template from: {TEMPLATE_DIR}")
        env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
        template = env.get_template('invoice_template.html')
        
        # Render HTML
        logger.info("Rendering HTML template...")
        html_content = template.render(**data)
        
        # Generate PDF
        logger.info(f"Generating PDF: {output_path}")
        HTML(string=html_content).write_pdf(output_path)
        
        logger.info(f"HTML Invoice PDF generated: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error generating HTML PDF: {e}", exc_info=True)
        raise


def _normalize_invoice_data(invoice: dict) -> dict:
    """
    Normalize invoice data for template rendering.
    """
    # Group line items by location/section
    sections_dict = {}
    
    for item in invoice.get('line_items', []):
        location = item.get('location', 'Items')
        if location not in sections_dict:
            sections_dict[location] = {
                'line_items': [],
                'total': 0
            }
        
        # Format item data
        formatted_item = {
            'name': item.get('tile_name') or item.get('product_name', ''),
            'size': item.get('size', ''),
            'rate_box': f"{item.get('rate_per_box', 0):.2f}",
            'rate_sqft': f"{item.get('rate_per_sqft', 0):.2f}",
            'qty': f"{item.get('box_qty', 0)} box",
            'disc': f"{round(item.get('discount_percent', 0))}",
            'amount': f"{item.get('final_amount', 0):,.2f}",
            'image': item.get('tile_image', '')
        }
        
        sections_dict[location]['line_items'].append(formatted_item)
        sections_dict[location]['total'] += item.get('final_amount', 0)
    
    # Convert to list format
    sections = []
    for name, section_data in sections_dict.items():
        sections.append({
            'name': name,
            'line_items': section_data['line_items'],
            'total': f"{section_data['total']:,.2f}"
        })
    
    # Format date
    date = invoice.get('invoice_date')
    if date:
        if isinstance(date, str):
            try:
                date = datetime.fromisoformat(date)
            except:
                pass
        if isinstance(date, datetime):
            date = date.strftime("%d/%m/%Y")
    
    # Return normalized data
    return {
        'quotation_no': invoice.get('invoice_id', ''),
        'date': date or '',
        'reference_name': invoice.get('reference_name', ''),
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
            'transport': f"{invoice.get('transport_charges', 0):,.2f}",
            'unloading': f"{invoice.get('unloading_charges', 0):,.2f}"
        },
        'subtotal': f"{invoice.get('subtotal', 0):,.2f}",
        'gst_amount': invoice.get('gst_amount', 0),
        'grand_total': f"{invoice.get('grand_total', 0):,.2f}",
        'remarks': invoice.get('overall_remarks', '')
    }
