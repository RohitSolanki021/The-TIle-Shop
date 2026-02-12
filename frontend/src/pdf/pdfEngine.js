/**
 * PRO Invoice PDF Engine using pdf-lib
 * =====================================
 * 
 * Template-overlay approach with pixel-perfect alignment.
 */

import { PDFDocument, StandardFonts, rgb } from 'pdf-lib';
import templateMapPage1 from './template_map.page1.json';
import templateMapCont from './template_map.cont.json';

// ==================== CONSTANTS ====================

const BLACK = rgb(0, 0, 0);
const BROWN = rgb(0.35, 0.22, 0.15);

// ==================== UTILITIES ====================

function textWidth(font, text, size) {
  try {
    return font.widthOfTextAtSize(text || '', size);
  } catch {
    return 0;
  }
}

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

function drawTextInBox(page, font, textRaw, box, opts = {}) {
  const text = (textRaw ?? '').toString().trim();
  if (!text || !box) return;

  const {
    size = 8,
    align = 'left',
    pad = 2,
    minSize = 6,
    color = BLACK
  } = opts;

  let fontSize = size;
  const maxWidth = box.w - pad * 2;

  while (fontSize > minSize && textWidth(font, text, fontSize) > maxWidth) {
    fontSize -= 0.2;
  }

  let display = text;
  if (textWidth(font, display, fontSize) > maxWidth) {
    while (
      display.length > 3 &&
      textWidth(font, display + '..', fontSize) > maxWidth
    ) {
      display = display.slice(0, -1);
    }
    display += '..';
  }

  const w = textWidth(font, display, fontSize);

  let x = box.x + pad;
  if (align === 'right') x = box.x + box.w - pad - w;
  if (align === 'center') x = box.x + (box.w - w) / 2;

  const y = box.y + (box.h - fontSize) / 2;

  page.drawText(display, { x, y, size: fontSize, font, color });
}

export async function drawImageInBox(pdfDoc, page, imageBase64, box, pad = 2) {
  if (!imageBase64) return;
  
  try {
    let base64Data = imageBase64;
    if (base64Data.startsWith('data:image')) {
      base64Data = base64Data.split(',')[1];
    }
    
    const binaryString = atob(base64Data);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    
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
    
    const x = box.x + (box.w - w) / 2;
    const y = box.y + (box.h - h) / 2;
    
    page.drawImage(img, { x, y, width: w, height: h });
  } catch (error) {
    console.warn('Error drawing image:', error);
  }
}

function rowBox(col, y, rowH) {
  return { x: col.x, y, w: col.w, h: rowH };
}

// ==================== PDF ENGINE ====================

async function addTemplatePage(pdfDoc, templateBytes) {
  const templateDoc = await PDFDocument.load(templateBytes);
  const [tplPage] = await pdfDoc.copyPages(templateDoc, [0]);
  pdfDoc.addPage(tplPage);
  return tplPage;
}

export async function generateInvoicePDF(data, templatePage1Bytes, templateContBytes = null) {
  const pdfDoc = await PDFDocument.create();
  const font = await pdfDoc.embedFont(StandardFonts.Helvetica);
  const fontBold = await pdfDoc.embedFont(StandardFonts.HelveticaBold);
  
  const contTemplateBytes = templateContBytes || templatePage1Bytes;
  
  let page = await addTemplatePage(pdfDoc, templatePage1Bytes);
  let map = templateMapPage1;
  let isFirstPage = true;
  
  // Fill Header (Page 1 only)
  if (map.header) {
    drawTextInBox(page, fontBold, data.quotationNo, map.header.quotationNo, { align: 'left', size: 7.5 });
    drawTextInBox(page, fontBold, data.date, map.header.date, { align: 'left', size: 7.5 });
    if (data.referenceName) {
      drawTextInBox(page, font, data.referenceName, map.header.referenceName, { align: 'left', size: 7.5 });
    }
  }
  
  // Fill Buyer (Page 1 only)
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
  
  // Fill Consignee (Page 1 only)
  if (map.consignee && data.consignee) {
    drawTextInBox(page, fontBold, data.consignee.name, map.consignee.name, { size: 7.5 });
    drawTextInBox(page, font, `Ph: ${data.consignee.phone || ''}`, map.consignee.phone, { size: 7 });
    
    const addr = data.consignee.address || '';
    drawTextInBox(page, font, addr.slice(0, 40), map.consignee.address1, { size: 7 });
    if (addr.length > 40) {
      drawTextInBox(page, font, addr.slice(40, 80), map.consignee.address2, { size: 7 });
    }
  }
  
  // Render Sections
  let y = map.table.startY;
  
  for (const section of data.sections) {
    const rowH = map.table.rowH;
    
    if (y - rowH < map.table.safeBottomY) {
      page = await addTemplatePage(pdfDoc, contTemplateBytes);
      map = templateMapCont;
      isFirstPage = false;
      y = map.table.startY;
    }
    
    // Section Header Row
    const titleBox = { ...map.section.titleBox, y: y - rowH };
    coverBox(page, titleBox, BG_COLOR);
    drawTextInBox(page, fontBold, section.name.toUpperCase(), titleBox, { 
      align: 'center', 
      size: 9, 
      color: BROWN 
    });
    
    y -= rowH;
    
    // Item Rows
    let sr = 1;
    let sectionTotal = 0;
    
    for (const item of section.items) {
      const hasImage = !!item.imageBase64;
      const itemRowH = hasImage ? map.table.rowHWithImage : rowH;
      
      if (y - itemRowH < map.table.safeBottomY) {
        page = await addTemplatePage(pdfDoc, contTemplateBytes);
        map = templateMapCont;
        isFirstPage = false;
        y = map.table.startY;
      }
      
      const cols = map.table.cols;
      const rowY = y - itemRowH;
      
      drawTextInBox(page, font, String(sr), rowBox(cols.sr, rowY, itemRowH), { align: 'center', size: 7 });
      drawTextInBox(page, font, item.name, rowBox(cols.name, rowY, itemRowH), { align: 'left', size: 7 });
      
      if (hasImage) {
        const imgBox = {
          x: cols.image.x,
          y: rowY + 3,
          w: cols.image.imgW || 30,
          h: cols.image.imgH || 30
        };
        await drawImageInBox(pdfDoc, page, item.imageBase64, imgBox);
      }
      
      drawTextInBox(page, font, item.size, rowBox(cols.size, rowY, itemRowH), { align: 'center', size: 7 });
      drawTextInBox(page, font, item.rateBox || '', rowBox(cols.rateBox, rowY, itemRowH), { align: 'right', size: 6 });
      drawTextInBox(page, font, item.rateSqft || '', rowBox(cols.rateSqft, rowY, itemRowH), { align: 'right', size: 6 });
      drawTextInBox(page, font, item.qty || '', rowBox(cols.qty, rowY, itemRowH), { align: 'center', size: 6 });
      drawTextInBox(page, font, item.disc || '', rowBox(cols.disc, rowY, itemRowH), { align: 'center', size: 6 });
      drawTextInBox(page, fontBold, item.amount || '', rowBox(cols.amount, rowY, itemRowH), { align: 'right', size: 7 });
      
      sectionTotal += Number(item.amountNumeric ?? 0);
      sr++;
      y -= itemRowH;
    }
    
    // Section Total Row
    if (y - rowH < map.table.safeBottomY) {
      page = await addTemplatePage(pdfDoc, contTemplateBytes);
      map = templateMapCont;
      isFirstPage = false;
      y = map.table.startY;
    }
    
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
    
    y -= rowH + 5;
  }
  
  // Footer (if on page 1 and has space)
  if (isFirstPage && map.footer && y > 150) {
    if (data.subtotal !== undefined) {
      drawTextInBox(page, font, `₹${Math.round(data.subtotal).toLocaleString('en-IN')}`, map.footer.totalAmount, { align: 'right', size: 7.5 });
    }
    if (data.charges?.transport !== undefined) {
      drawTextInBox(page, font, `₹${Math.round(data.charges.transport).toLocaleString('en-IN')}`, map.footer.transport, { align: 'right', size: 7.5 });
    }
    if (data.charges?.unloading !== undefined) {
      drawTextInBox(page, font, `₹${Math.round(data.charges.unloading).toLocaleString('en-IN')}`, map.footer.unloading, { align: 'right', size: 7.5 });
    }
    if (data.gstAmount !== undefined && data.gstAmount > 0) {
      drawTextInBox(page, font, `₹${Math.round(data.gstAmount).toLocaleString('en-IN')}`, map.footer.gst, { align: 'right', size: 7.5 });
    } else {
      drawTextInBox(page, font, 'As applicable', map.footer.gst, { align: 'right', size: 7, color: rgb(0.4, 0.4, 0.4) });
    }
    if (data.grandTotal !== undefined) {
      drawTextInBox(page, fontBold, `₹${Math.round(data.grandTotal).toLocaleString('en-IN')}`, map.footer.finalAmount, { align: 'right', size: 8, color: rgb(1, 1, 1) });
    }
    if (data.remarks) {
      drawTextInBox(page, font, data.remarks, map.footer.remarks, { align: 'left', size: 7 });
    }
  }
  
  // Page Numbers
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

export function convertInvoiceToSections(invoice) {
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
  
  let dateStr = invoice.invoice_date;
  if (dateStr) {
    try {
      const d = new Date(dateStr);
      dateStr = d.toLocaleDateString('en-GB');
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

export default {
  generateInvoicePDF,
  convertInvoiceToSections,
  coverBox,
  drawTextInBox,
  drawImageInBox
};
