import { PDFDocument, StandardFonts, rgb } from 'pdf-lib';

/* ============================================
   CONSTANTS
============================================ */

const BLACK = rgb(0, 0, 0);
const BROWN = rgb(0.35, 0.22, 0.15);

/* ============================================
   UTILITIES
============================================ */

function textWidth(font, text, size) {
  try {
    return font.widthOfTextAtSize(text || '', size);
  } catch {
    return 0;
  }
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

/* ============================================
   IMAGE HANDLER (Node + Browser Safe)
============================================ */

async function drawImageInBox(pdfDoc, page, base64, box) {
  if (!base64) return;

  try {
    let clean = base64;
    if (clean.startsWith('data:image')) {
      clean = clean.split(',')[1];
    }

    const bytes =
      typeof window === 'undefined'
        ? Buffer.from(clean, 'base64')
        : Uint8Array.from(atob(clean), c => c.charCodeAt(0));

    let img;
    try {
      img = await pdfDoc.embedPng(bytes);
    } catch {
      img = await pdfDoc.embedJpg(bytes);
    }

    const dims = img.scale(1);
    const maxW = box.w;
    const maxH = box.h;

    const scale = Math.min(maxW / dims.width, maxH / dims.height);

    const w = dims.width * scale;
    const h = dims.height * scale;

    const x = box.x + (box.w - w) / 2;
    const y = box.y + (box.h - h) / 2;

    page.drawImage(img, { x, y, width: w, height: h });

  } catch (err) {
    console.warn('Image render failed:', err);
  }
}

/* ============================================
   TEMPLATE PAGE
============================================ */

async function addTemplatePage(pdfDoc, templateBytes) {
  const tpl = await PDFDocument.load(templateBytes);
  const [page] = await pdfDoc.copyPages(tpl, [0]);
  pdfDoc.addPage(page);
  return page;
}

/* ============================================
   MAIN ENGINE
============================================ */

export async function generateInvoicePDF(
  data,
  templatePage1Bytes,
  templateContBytes,
  page1Map,
  contMap
) {
  const pdfDoc = await PDFDocument.create();
  const font = await pdfDoc.embedFont(StandardFonts.Helvetica);
  const fontBold = await pdfDoc.embedFont(StandardFonts.HelveticaBold);

  let page = await addTemplatePage(pdfDoc, templatePage1Bytes);
  let map = page1Map;
  let y = map.table.startY;

  /* ================= HEADER ================= */

  drawTextInBox(page, fontBold, data.quotationNo, map.header.quotationNo);
  drawTextInBox(page, fontBold, data.date, map.header.date);
  drawTextInBox(page, font, data.referenceName, map.header.referenceName);

  /* ================= BUYER ================= */

  drawTextInBox(page, fontBold, data.buyer.name, map.buyer.name);
  drawTextInBox(page, font, `Ph: ${data.buyer.phone}`, map.buyer.phone);
  drawTextInBox(page, font, data.buyer.address, map.buyer.address1);
  drawTextInBox(page, font, `GSTIN: ${data.buyer.gstin}`, map.buyer.gstin);

  /* ================= CONSIGNEE ================= */

  drawTextInBox(page, fontBold, data.consignee.name, map.consignee.name);
  drawTextInBox(page, font, `Ph: ${data.consignee.phone}`, map.consignee.phone);
  drawTextInBox(page, font, data.consignee.address, map.consignee.address1);

  /* ================= TABLE ================= */

  for (const section of data.sections) {
    const rowH = map.table.rowH;

    // Section header
    drawTextInBox(
      page,
      fontBold,
      section.name.toUpperCase(),
      map.section.titleBox,
      { align: 'center', size: 9, color: BROWN }
    );

    y -= rowH;

    let sectionTotal = 0;
    let sr = 1;

    for (const item of section.items) {

      const itemRowH = item.imageBase64
        ? map.table.rowHWithImage
        : map.table.rowH;

      if (y - itemRowH < map.table.safeBottomY) {
        page = await addTemplatePage(pdfDoc, templateContBytes);
        map = contMap;
        y = map.table.startY;

        // re-render section title on new page
        drawTextInBox(
          page,
          fontBold,
          section.name.toUpperCase(),
          map.section.titleBox,
          { align: 'center', size: 9, color: BROWN }
        );

        y -= rowH;
      }

      const cols = map.table.cols;
      const rowY = y - itemRowH;

      drawTextInBox(page, font, sr, { ...cols.sr, y: rowY, h: itemRowH });
      drawTextInBox(page, font, item.name, { ...cols.name, y: rowY, h: itemRowH });
      drawTextInBox(page, font, item.size, { ...cols.size, y: rowY, h: itemRowH });

      drawTextInBox(page, font, item.rateBox, { ...cols.rateBox, y: rowY, h: itemRowH }, { align: 'right' });
      drawTextInBox(page, font, item.rateSqft, { ...cols.rateSqft, y: rowY, h: itemRowH }, { align: 'right' });
      drawTextInBox(page, font, item.qty, { ...cols.qty, y: rowY, h: itemRowH }, { align: 'center' });
      drawTextInBox(page, font, item.disc, { ...cols.disc, y: rowY, h: itemRowH }, { align: 'center' });
      drawTextInBox(page, fontBold, item.amount, { ...cols.amount, y: rowY, h: itemRowH }, { align: 'right' });

      if (item.imageBase64) {
        await drawImageInBox(pdfDoc, page, item.imageBase64, {
          x: cols.image.x,
          y: rowY + 4,
          w: cols.image.imgW,
          h: cols.image.imgH
        });
      }

      sectionTotal += item.amountNumeric || 0;
      sr++;
      y -= itemRowH;
    }

    // Section total
    drawTextInBox(
      page,
      fontBold,
      `${section.name}'s Total Amount`,
      map.section.totalLabelBox,
      { align: 'right', size: 8, color: BROWN }
    );

    drawTextInBox(
      page,
      fontBold,
      `₹${sectionTotal.toLocaleString('en-IN')}`,
      map.section.totalValueBox,
      { align: 'right', size: 8 }
    );

    y -= 25;
  }

  /* ================= FOOTER ON LAST PAGE ================= */

  const pages = pdfDoc.getPages();
  const lastPage = pages[pages.length - 1];
  const footer = page1Map.footer;

  drawTextInBox(lastPage, font, `₹${data.subtotal}`, footer.totalAmount, { align: 'right' });
  drawTextInBox(lastPage, font, `₹${data.charges.transport}`, footer.transport, { align: 'right' });
  drawTextInBox(lastPage, font, `₹${data.charges.unloading}`, footer.unloading, { align: 'right' });
  drawTextInBox(lastPage, font, `₹${data.gstAmount}`, footer.gst, { align: 'right' });
  drawTextInBox(lastPage, fontBold, `₹${data.grandTotal}`, footer.finalAmount, { align: 'right', size: 9 });
  drawTextInBox(lastPage, font, data.remarks, footer.remarks);

  /* ================= PAGE NUMBERS ================= */

  const pageCount = pdfDoc.getPageCount();
  pdfDoc.getPages().forEach((p, i) => {
    drawTextInBox(
      p,
      font,
      `Page ${i + 1} of ${pageCount}`,
      { x: 450, y: 820, w: 120, h: 12 },
      { align: 'right', size: 7 }
    );
  });

  return await pdfDoc.save();
}

/* ============================================
   HELPER: Convert Invoice to Sections Format
============================================ */

export function convertInvoiceToSections(invoice) {
  const sections = [];
  const locationMap = {};

  invoice.line_items.forEach(item => {
    const loc = item.location || 'GENERAL';
    if (!locationMap[loc]) {
      locationMap[loc] = [];
    }
    locationMap[loc].push(item);
  });

  Object.entries(locationMap).forEach(([location, items]) => {
    const sectionItems = items.map((item, idx) => ({
      name: item.tile_name || '',
      size: item.size || '',
      rateBox: item.rate_per_box ? `₹${item.rate_per_box.toFixed(2)}` : '',
      rateSqft: item.rate_per_sqft ? `₹${item.rate_per_sqft.toFixed(2)}` : '',
      qty: item.box_qty ? `${item.box_qty}` : '',
      disc: item.discount_percent ? `${item.discount_percent}%` : '0%',
      amount: `₹${(item.final_amount || 0).toFixed(2)}`,
      amountNumeric: item.final_amount || 0,
      imageBase64: item.tile_image || null
    }));

    sections.push({
      name: location,
      items: sectionItems
    });
  });

  return sections;
}
