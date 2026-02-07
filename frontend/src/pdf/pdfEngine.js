/**
 * PRO Invoice PDF Engine using pdf-lib
 * =====================================
 * 
 * Template-overlay approach with pixel-perfect alignment.
 * 
 * Features:
 * - Template PDF pages as background (page1 + continuation)
 * - All text/images drawn with drawTextInBox/drawImageInBox helpers
 * - Multiple sections support (SA, KITCHEN, etc.)
 * - Template label replacement with background rect overlay
 * - Item rows using y = startY - rowIndex * rowH
 * - Auto-pagination at safeBottomY
 * - Header only on page 1 (continuation pages have no header)
 */

import { PDFDocument, StandardFonts, rgb } from 'pdf-lib';
import templateMapPage1 from './template_map.page1.json';
import templateMapCont from './template_map.cont.json';

// ==================== TYPES ====================

/**
 * @typedef {Object} Box
 * @property {number} x - X coordinate (from left)
 * @property {number} y - Y coordinate (from bottom - pdf-lib convention)
 * @property {number} w - Width
 * @property {number} h - Height
 */

/**
 * @typedef {'left' | 'center' | 'right'} Align
 */

/**
 * @typedef {Object} InvoiceItem
 * @property {string} name
 * @property {string} size
 * @property {string} [rateBox]
 * @property {string} [rateSqft]
 * @property {string} [qty]
 * @property {string} [disc]
 * @property {string} [amount]
 * @property {number} [amountNumeric]
 * @property {string} [imageBase64]
 */

/**
 * @typedef {Object} InvoiceSection
 * @property {string} name - Section name (SA, KITCHEN, etc.)
 * @property {InvoiceItem[]} items
 */

/**
 * @typedef {Object} InvoiceData
 * @property {string} quotationNo
 * @property {string} date
 * @property {string} [referenceName]
 * @property {Object} [buyer]
 * @property {Object} [consignee]
 * @property {InvoiceSection[]} sections
 * @property {Object} [charges]
 * @property {number} [subtotal]
 * @property {number} [gstAmount]
 * @property {number} [grandTotal]
 * @property {string} [remarks]
 */

// ==================== CONSTANTS ====================

const BG_COLOR = rgb(0.98, 0.96, 0.95);  // Template background cream color
const BLACK = rgb(0, 0, 0);
const BROWN = rgb(0.35, 0.22, 0.15);

// ==================== HELPER FUNCTIONS ====================

/**
 * Calculate text width at given font size
 */
function textWidth(font, text, size) {
  return font.widthOfTextAtSize(text || '', size);
}

/**
 * Cover a box area with background color (to hide template text)
 * @param {any} page - PDF page
 * @param {Box} box - Box coordinates
 * @param {any} color - RGB color
 */
export function coverBox(page, box, color = BG_COLOR) {
  page.drawRectangle({
    x: box.x,
    y: box.y,
    width: box.w,
    height: box.h,
    color: color,
    borderColor: color,
  });
}

/**
 * Draw text inside a bounding box with alignment and shrink-to-fit
 * @param {any} page - PDF page
 * @param {any} font - PDF font
 * @param {string} textRaw - Text to draw
 * @param {Box} box - Box coordinates
 * @param {Object} opts - Options {size, align, pad, minSize, color}
 */
export function drawTextInBox(page, font, textRaw, box, opts = {}) {
  const text = (textRaw ?? '').toString().trim();
  if (!text) return;
  
  const {
    size: initialSize = 9,
    align = 'left',
    pad = 2,
    minSize = 6,
    color = BLACK
  } = opts;
  
  let size = initialSize;
  const maxW = box.w - pad * 2;
  
  // Shrink to fit
  while (size > minSize && textWidth(font, text, size) > maxW) {
    size -= 0.25;
  }
  
  // Truncate if still too long
  let displayText = text;
  if (textWidth(font, displayText, size) > maxW) {
    while (displayText.length > 3 && textWidth(font, displayText + '..', size) > maxW) {
      displayText = displayText.slice(0, -1);
    }
    displayText += '..';
  }
  
  const w = textWidth(font, displayText, size);
  
  // Calculate X position based on alignment
  let x = box.x + pad;
  if (align === 'right') {
    x = box.x + box.w - pad - w;
  } else if (align === 'center') {
    x = box.x + (box.w - w) / 2;
  }
  
  // Calculate Y position (centered vertically in box)
  const y = box.y + (box.h - size) / 2;
  
  page.drawText(displayText, { x, y, size, font, color });
}

/**
 * Draw image inside a bounding box
 * @param {PDFDocument} pdfDoc - PDF document
 * @param {any} page - PDF page
 * @param {string} imageBase64 - Base64 image data
 * @param {Box} box - Box coordinates
 * @param {number} pad - Padding
 */
export async function drawImageInBox(pdfDoc, page, imageBase64, box, pad = 2) {
  if (!imageBase64) return;
  
  try {
    // Extract base64 data if it has prefix
    let base64Data = imageBase64;
    if (base64Data.startsWith('data:image')) {
      base64Data = base64Data.split(',')[1];
    }
    
    // Convert base64 to Uint8Array
    const binaryString = atob(base64Data);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    
    // Try to embed as PNG first, then JPEG
    let img;
    try {
      img = await pdfDoc.embedPng(bytes);
    } catch {
      img = await pdfDoc.embedJpg(bytes);
    }
    
    const maxW = box.w - pad * 2;
    const maxH = box.h - pad * 2;
    
    const dim = img.scale(1);
    const scale = Math.min(maxW / dim.width, maxH / dim.height);
    
    const w = dim.width * scale;
    const h = dim.height * scale;
    
    // Center image in box
    const x = box.x + (box.w - w) / 2;
    const y = box.y + (box.h - h) / 2;
    
    page.drawImage(img, { x, y, width: w, height: h });
  } catch (error) {
    console.warn('Error drawing image:', error);
  }
}

/**
 * Create a box for a table row cell
 * @param {Object} col - Column definition {x, w, align}
 * @param {number} y - Y position
 * @param {number} rowH - Row height
 * @returns {Box}
 */
function rowBox(col, y, rowH) {
  return { x: col.x, y, w: col.w, h: rowH };
}

// ==================== PDF ENGINE ====================

/**
 * Add a template page to the PDF document
 * @param {PDFDocument} pdfDoc - PDF document
 * @param {Uint8Array} templateBytes - Template PDF bytes
 * @returns {Promise<any>} - The added page
 */
async function addTemplatePage(pdfDoc, templateBytes) {
  const templateDoc = await PDFDocument.load(templateBytes);
  const [tplPage] = await pdfDoc.copyPages(templateDoc, [0]);
  pdfDoc.addPage(tplPage);
  return tplPage;
}

/**
 * Generate invoice PDF using template overlay
 * @param {InvoiceData} data - Invoice data with sections
 * @param {Uint8Array} templatePage1Bytes - Page 1 template PDF bytes
 * @param {Uint8Array} [templateContBytes] - Continuation template PDF bytes (optional)
 * @returns {Promise<Uint8Array>} - Generated PDF bytes
 */
export async function generateInvoicePDF(data, templatePage1Bytes, templateContBytes = null) {
  const pdfDoc = await PDFDocument.create();
  const font = await pdfDoc.embedFont(StandardFonts.Helvetica);
  const fontBold = await pdfDoc.embedFont(StandardFonts.HelveticaBold);
  
  // Use page1 template for continuation if no separate template provided
  const contTemplateBytes = templateContBytes || templatePage1Bytes;
  
  // ---- Page 1 ----
  let page = await addTemplatePage(pdfDoc, templatePage1Bytes);
  let map = templateMapPage1;
  let isFirstPage = true;
  
  // ---- Fill Header (Page 1 only) ----
  if (map.header) {
    drawTextInBox(page, fontBold, data.quotationNo, map.header.quotationNo, { align: 'left', size: 7.5 });
    drawTextInBox(page, fontBold, data.date, map.header.date, { align: 'left', size: 7.5 });
    if (data.referenceName) {
      drawTextInBox(page, font, data.referenceName, map.header.referenceName, { align: 'left', size: 7.5 });
    }
  }
  
  // ---- Fill Buyer (Page 1 only) ----
  if (map.buyer && data.buyer) {
    drawTextInBox(page, fontBold, data.buyer.name, map.buyer.name, { size: 7.5 });
    drawTextInBox(page, font, `Ph: ${data.buyer.phone || ''}`, map.buyer.phone, { size: 7 });
    
    const addr = data.buyer.address || '';
    drawTextInBox(page, font, addr.slice(0, 40), map.buyer.address1, { size: 7 });
    if (addr.length > 40) {
      drawTextInBox(page, font, addr.slice(40, 80), map.buyer.address2, { size: 7 });
    }
    if (data.buyer.gstin) {
      drawTextInBox(page, font, `GSTIN: ${data.buyer.gstin}`, map.buyer.gstin, { size: 7 });
    }
  }
  
  // ---- Fill Consignee (Page 1 only) ----
  if (map.consignee && data.consignee) {
    drawTextInBox(page, fontBold, data.consignee.name, map.consignee.name, { size: 7.5 });
    drawTextInBox(page, font, `Ph: ${data.consignee.phone || ''}`, map.consignee.phone, { size: 7 });
    
    const addr = data.consignee.address || '';
    drawTextInBox(page, font, addr.slice(0, 40), map.consignee.address1, { size: 7 });
    if (addr.length > 40) {
      drawTextInBox(page, font, addr.slice(40, 80), map.consignee.address2, { size: 7 });
    }
  }
  
  // ---- Render Sections ----
  let y = map.table.startY;
  
  for (const section of data.sections) {
    const rowH = map.table.rowH;
    
    // Check if section header fits, otherwise new page
    if (y - rowH < map.table.safeBottomY) {
      page = await addTemplatePage(pdfDoc, contTemplateBytes);
      map = templateMapCont;
      isFirstPage = false;
      y = map.table.startY;
    }
    
    // ---- Section Header Row ----
    // Cover "MAIN FLOOR" text and write section name
    const titleBox = { ...map.section.titleBox, y: y - rowH };
    coverBox(page, titleBox, BG_COLOR);
    drawTextInBox(page, fontBold, section.name.toUpperCase(), titleBox, { 
      align: 'center', 
      size: 9, 
      color: BROWN 
    });
    
    y -= rowH;
    
    // ---- Item Rows ----
    let sr = 1;
    let sectionTotal = 0;
    
    for (const item of section.items) {
      const hasImage = !!item.imageBase64;
      const itemRowH = hasImage ? map.table.rowHWithImage : rowH;
      
      // Check if item row fits
      if (y - itemRowH < map.table.safeBottomY) {
        page = await addTemplatePage(pdfDoc, contTemplateBytes);
        map = templateMapCont;
        isFirstPage = false;
        y = map.table.startY;
      }
      
      const cols = map.table.cols;
      const rowY = y - itemRowH;
      
      // SR NO
      drawTextInBox(page, font, String(sr), rowBox(cols.sr, rowY, itemRowH), { align: 'center', size: 7 });
      
      // NAME
      drawTextInBox(page, font, item.name, rowBox(cols.name, rowY, itemRowH), { align: 'left', size: 7 });
      
      // IMAGE
      if (hasImage) {
        const imgBox = {
          x: cols.image.x,
          y: rowY + 3,
          w: cols.image.imgW || 30,
          h: cols.image.imgH || 30
        };
        await drawImageInBox(pdfDoc, page, item.imageBase64, imgBox);
      }
      
      // SIZE
      drawTextInBox(page, font, item.size, rowBox(cols.size, rowY, itemRowH), { align: 'center', size: 7 });
      
      // RATE/BOX
      drawTextInBox(page, font, item.rateBox || '', rowBox(cols.rateBox, rowY, itemRowH), { align: 'right', size: 6 });
      
      // RATE/SQFT
      drawTextInBox(page, font, item.rateSqft || '', rowBox(cols.rateSqft, rowY, itemRowH), { align: 'right', size: 6 });
      
      // QTY
      drawTextInBox(page, font, item.qty || '', rowBox(cols.qty, rowY, itemRowH), { align: 'center', size: 6 });
      
      // DISC
      drawTextInBox(page, font, item.disc || '', rowBox(cols.disc, rowY, itemRowH), { align: 'center', size: 6 });
      
      // AMOUNT
      drawTextInBox(page, fontBold, item.amount || '', rowBox(cols.amount, rowY, itemRowH), { align: 'right', size: 7 });
      
      sectionTotal += Number(item.amountNumeric ?? 0);
      sr++;
      y -= itemRowH;
    }
    
    // ---- Section Total Row ----
    if (y - rowH < map.table.safeBottomY) {
      page = await addTemplatePage(pdfDoc, contTemplateBytes);
      map = templateMapCont;
      isFirstPage = false;
      y = map.table.startY;
    }
    
    // Cover "MAIN FLOOR's Total Amount" and write section total
    const labelBox = { ...map.section.totalLabelBox, y: y - rowH };
    const valueBox = { ...map.section.totalValueBox, y: y - rowH };
    
    coverBox(page, labelBox, BG_COLOR);
    drawTextInBox(page, fontBold, `${section.name}'s Total Amount`, labelBox, { 
      align: 'right', 
      size: 8, 
      color: BROWN 
    });
    
    drawTextInBox(page, fontBold, `₹${sectionTotal.toLocaleString('en-IN')}`, valueBox, { 
      align: 'right', 
      size: 8 
    });
    
    y -= rowH + 5; // Extra spacing between sections
  }
  
  // ---- Footer (if on page 1 and has space) ----
  if (isFirstPage && map.footer && y > 150) {
    // Total Amount
    if (data.subtotal !== undefined) {
      drawTextInBox(page, font, `₹${Math.round(data.subtotal).toLocaleString('en-IN')}`, map.footer.totalAmount, { align: 'right', size: 7.5 });
    }
    
    // Transport
    if (data.charges?.transport !== undefined) {
      drawTextInBox(page, font, `₹${Math.round(data.charges.transport).toLocaleString('en-IN')}`, map.footer.transport, { align: 'right', size: 7.5 });
    }
    
    // Unloading
    if (data.charges?.unloading !== undefined) {
      drawTextInBox(page, font, `₹${Math.round(data.charges.unloading).toLocaleString('en-IN')}`, map.footer.unloading, { align: 'right', size: 7.5 });
    }
    
    // GST
    if (data.gstAmount !== undefined && data.gstAmount > 0) {
      drawTextInBox(page, font, `₹${Math.round(data.gstAmount).toLocaleString('en-IN')}`, map.footer.gst, { align: 'right', size: 7.5 });
    } else {
      drawTextInBox(page, font, 'As applicable', map.footer.gst, { align: 'right', size: 7, color: rgb(0.4, 0.4, 0.4) });
    }
    
    // Final Amount
    if (data.grandTotal !== undefined) {
      drawTextInBox(page, fontBold, `₹${Math.round(data.grandTotal).toLocaleString('en-IN')}`, map.footer.finalAmount, { align: 'right', size: 8, color: rgb(1, 1, 1) });
    }
    
    // Remarks
    if (data.remarks) {
      drawTextInBox(page, font, data.remarks, map.footer.remarks, { align: 'left', size: 7 });
    }
  }
  
  // ---- Add Page Numbers (if multiple pages) ----
  const pageCount = pdfDoc.getPageCount();
  if (pageCount > 1) {
    const pages = pdfDoc.getPages();
    for (let i = 0; i < pageCount; i++) {
      const p = pages[i];
      const pageNumText = `${data.quotationNo} (Page ${i + 1}/${pageCount})`;
      drawTextInBox(p, font, pageNumText, { x: 350, y: 815, w: 220, h: 12 }, { 
        align: 'right', 
        size: 7, 
        color: rgb(0.3, 0.3, 0.3) 
      });
    }
  }
  
  return await pdfDoc.save();
}

/**
 * Convert invoice from backend format to PDF engine format
 * @param {Object} invoice - Invoice from backend API
 * @returns {InvoiceData}
 */
export function convertInvoiceToSections(invoice) {
  // Group line items by location (section)
  const sectionsDict = {};
  
  for (const item of (invoice.line_items || [])) {
    const sectionName = item.location || 'Items';
    if (!sectionsDict[sectionName]) {
      sectionsDict[sectionName] = [];
    }
    
    sectionsDict[sectionName].push({
      name: item.tile_name || item.product_name || '',
      size: item.size || '',
      rateBox: `₹${Math.round(item.rate_per_box || 0)}`,
      rateSqft: `₹${Math.round(item.rate_per_sqft || 0)}`,
      qty: `${item.box_qty || 0} box`,
      disc: `${Math.round(item.discount_percent || 0)}%`,
      amount: `₹${Math.round(item.final_amount || 0).toLocaleString('en-IN')}`,
      amountNumeric: item.final_amount || 0,
      imageBase64: item.tile_image || ''
    });
  }
  
  const sections = Object.entries(sectionsDict).map(([name, items]) => ({
    name,
    items
  }));
  
  // Format date
  let dateStr = invoice.invoice_date;
  if (dateStr) {
    try {
      const d = new Date(dateStr);
      dateStr = d.toLocaleDateString('en-GB'); // DD/MM/YYYY
    } catch {
      // Keep original
    }
  }
  
  return {
    quotationNo: invoice.invoice_id || '',
    date: dateStr || '',
    referenceName: invoice.reference_name || '',
    buyer: {
      name: invoice.customer_name || '',
      phone: invoice.customer_phone || '',
      address: invoice.customer_address || '',
      gstin: invoice.customer_gstin || ''
    },
    consignee: {
      name: invoice.consignee_name || invoice.customer_name || '',
      phone: invoice.consignee_phone || invoice.customer_phone || '',
      address: invoice.consignee_address || invoice.customer_address || ''
    },
    sections,
    charges: {
      transport: invoice.transport_charges || 0,
      unloading: invoice.unloading_charges || 0
    },
    subtotal: invoice.subtotal || 0,
    gstAmount: invoice.gst_amount || 0,
    grandTotal: invoice.grand_total || 0,
    remarks: invoice.overall_remarks || ''
  };
}

/**
 * Generate and download PDF from invoice
 * @param {Object} invoice - Invoice from backend
 * @param {Uint8Array} templateBytes - Template PDF bytes
 */
export async function downloadInvoicePDF(invoice, templateBytes) {
  const data = convertInvoiceToSections(invoice);
  const pdfBytes = await generateInvoicePDF(data, templateBytes);
  
  // Create blob and download
  const blob = new Blob([pdfBytes], { type: 'application/pdf' });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = `Invoice_${invoice.invoice_id.replace(/\//g, '-')}.pdf`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  URL.revokeObjectURL(url);
}

export default {
  generateInvoicePDF,
  convertInvoiceToSections,
  downloadInvoicePDF,
  coverBox,
  drawTextInBox,
  drawImageInBox
};
