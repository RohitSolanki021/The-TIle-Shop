<?php
/**
 * PDF Generator (mPDF) - Quotation layout like your sample
 * IMPORTANT:
 * - Put this file at: backend-php/utils/pdf_generator.php
 * - Make sure PDF_DIR is writable (backend-php/invoices/ or whatever your config uses)
 */

class PDFGenerator {

    private $mpdfAvailable = false;

    // ---- CHANGE THESE IF YOUR FOLDERS DIFFER ----
    private $brandDirFs;   // filesystem path for brand logos
    private $uploadDirFs;  // filesystem path for uploads (product images etc.)
    private $brandDirUrl;  // URL fallback for brand logos (only if needed)
    private $uploadDirUrl; // URL fallback for uploads (only if needed)

    public function __construct() {
        // Composer autoload
        $autoload = __DIR__ . '/../vendor/autoload.php';
        if (file_exists($autoload)) {
            require_once $autoload;
            if (class_exists('\\Mpdf\\Mpdf')) {
                $this->mpdfAvailable = true;
            }
        }

        // Folders (filesystem)
        $this->brandDirFs  = realpath(__DIR__ . '/../assets/brand_logos');
        $this->uploadDirFs = realpath(__DIR__ . '/../uploads');

        // URL fallback (only if filesystem not accessible)
        if (defined('APP_URL')) {
            $base = rtrim(APP_URL, '/');
            $this->brandDirUrl  = $base . '/backend-php/assets/brand_logos';
            $this->uploadDirUrl = $base . '/backend-php/uploads';
        } else {
            $this->brandDirUrl  = '';
            $this->uploadDirUrl = '';
        }
    }

    public function generateInvoicePDF($invoice) {
        if (!$this->mpdfAvailable) {
            throw new Exception("mPDF not installed. Run: composer require mpdf/mpdf inside backend-php/");
        }
        return $this->generateWithMPDF($invoice);
    }

    private function generateWithMPDF($invoice) {
        @ini_set('pcre.backtrack_limit', '8000000');
        @ini_set('pcre.recursion_limit', '2000000');

        $tempDir = __DIR__ . '/../tmp/mpdf';
        if (!file_exists($tempDir)) {
            @mkdir($tempDir, 0755, true);
        }

        $mpdf = new \Mpdf\Mpdf([
            'mode' => 'utf-8',
            'format' => 'A4',
            'margin_left' => 8,
            'margin_right' => 8,
            'margin_top' => 8,
            'margin_bottom' => 10,
            'tempDir' => $tempDir,
        ]);

        $mpdf->SetTitle('Quotation ' . ($invoice['invoice_id'] ?? ''));
        $mpdf->showImageErrors = true;

        // 1) CSS
        $mpdf->WriteHTML($this->css(), \Mpdf\HTMLParserMode::HEADER_CSS);

        // 2) Header/top blocks
        $mpdf->WriteHTML($this->topBlockHtml($invoice), \Mpdf\HTMLParserMode::HTML_BODY);

        // 3) Items grouped by location + SR reset
        $this->writeItemsTable($mpdf, $invoice);

        // 4) Totals + bank + remarks + terms + brands
        $mpdf->WriteHTML($this->bottomBlockHtml($invoice), \Mpdf\HTMLParserMode::HTML_BODY);

        $filename = $this->getFilename($invoice['invoice_id'] ?? 'TTS');
        $filepath = rtrim(PDF_DIR, '/\\') . DIRECTORY_SEPARATOR . $filename;

        $mpdf->Output($filepath, 'F');
        return $filepath;
    }

    // ----------------- CSS -----------------
    private function css() {
        return "
        body { font-family: Arial, sans-serif; font-size: 10pt; color:#2b2b2b; }
        .pageTitle { text-align:center; font-size:22pt; font-weight:bold; color:#6b4a35; margin: 8px 0 10px; font-family: Georgia, serif; }
        .outer { border:1px solid #d2b48c; padding:0; }
        .pad { padding:10px; }
        .muted { color:#555; }
        .b { font-weight:bold; }

        table { width:100%; border-collapse:collapse; }
        .border td, .border th { border:1px solid #d2b48c; }

        .headLeft { width:18%; vertical-align:top; }
        .headMid  { width:52%; vertical-align:top; }
        .headRight{ width:30%; vertical-align:top; }

        .logo { max-width:90px; max-height:90px; }
        .shopName { font-size:16pt; font-weight:bold; letter-spacing:0.5px; color:#3a2a1f; }
        .small { font-size:9pt; }
        .line { border-top:1px solid #d2b48c; margin:8px 0; }

        .th td {
            background:#e6e6e6;
            font-weight:bold;
            font-size:10pt;
            text-align:center;
            vertical-align:middle;
            padding:6px 4px;
        }

        .right { text-align:right; }
        .center { text-align:center; }

        .finalRow { background:#f2e6d6; font-weight:bold; }

        .boxTitle { font-weight:bold; padding:8px 10px; background:#fff; }
        .terms { font-size:9pt; line-height:1.35; }

        .brandsWrap { margin-top:12px; text-align:center; }
        .brandImg { height:50px; max-width:140px; margin:6px 8px; vertical-align:middle; }

        /* ✅ Location row like your sample */
        .locationRow td {
            background:#7a5a3a;
            color:#fff;
            font-weight:bold;
            text-align:center;
            padding:6px 8px;
        }

        /* ✅ Item image */
        .tileImg {
            max-height:45px;
            max-width:70px;
            display:block;
            margin:0 auto;
        }

        /* ✅ Section total row */
        .sectionTotalLabel { font-weight:bold; }
        .sectionTotalValue { font-weight:bold; }

        ";
    }

    // ----------------- Brand image paths -----------------
    private function brandImgPath($filename) {
        if (!$filename) return null;

        if (preg_match('/^https?:\/\//i', $filename) || (function_exists('str_starts_with') && str_starts_with($filename, 'data:image'))) {
            return $filename;
        }

        if ($this->brandDirFs) {
            $candidate = $this->brandDirFs . DIRECTORY_SEPARATOR . $filename;
            if (file_exists($candidate)) return $candidate;
        }

        if ($this->brandDirUrl) {
            return $this->brandDirUrl . '/' . rawurlencode($filename);
        }

        return null;
    }

    // ----------------- Upload image paths (line item images) -----------------
    private function uploadImgPath($value) {
        if (!$value) return null;

        // Already URL or data URI
        if (preg_match('/^https?:\/\//i', $value) || (function_exists('str_starts_with') && str_starts_with($value, 'data:image'))) {
            return $value;
        }

        // If value is an absolute filesystem path and exists
        if (is_string($value) && file_exists($value)) {
            return $value;
        }

        // Try inside uploads folder as filename or relative path
        if ($this->uploadDirFs) {
            $candidate = $this->uploadDirFs . DIRECTORY_SEPARATOR . ltrim($value, '/\\');
            if (file_exists($candidate)) return $candidate;
        }

        // URL fallback
        if ($this->uploadDirUrl) {
            return $this->uploadDirUrl . '/' . ltrim($value, '/');
        }

        return null;
    }

    private function safe($v) {
        return htmlspecialchars((string)$v, ENT_QUOTES, 'UTF-8');
    }

    // ----------------- Top block -----------------
    private function topBlockHtml($invoice) {
        $invoiceId = $this->safe($invoice['invoice_id'] ?? '');
        $dateRaw   = $invoice['date'] ?? date('Y-m-d');
        $date      = date('d/m/Y', strtotime($dateRaw));

        $refName = $this->safe($invoice['reference_name'] ?? '');

        $buyerName  = $this->safe($invoice['customer_name'] ?? '');
        $buyerPhone = $this->safe($invoice['customer_phone'] ?? '');
        $buyerAddr  = nl2br($this->safe($invoice['customer_address'] ?? ''));

        $shipName = $this->safe($invoice['ship_to_name'] ?? ($invoice['customer_name'] ?? ''));
        $shipAddr = nl2br($this->safe($invoice['ship_to_address'] ?? ($invoice['customer_address'] ?? '')));

        $mainLogo = $this->brandImgPath('main_logo.png');

        $companyBlock = '
            <div class="shopName">THE TILE SHOP</div>
            <div class="small muted b">A Subsidiary of SHREE SONANA SHETRPAL CERAMIC</div>
            <div class="small" style="margin-top:6px;">
                S No. 19, Shop No. 2,<br>
                Near Pravin Electronics, Pune Saswad Road,<br>
                Gondhale Nagar, Hadapsar, Pune - 411028
            </div>
            <div class="small" style="margin-top:6px;"><span class="b">Email:</span> thetileshoppune@gmail.com</div>
            <div class="small"><span class="b">GSTIN:</span> 27AAFFESDH324GN</div>
            <div class="small"><span class="b">PAN:</span> 27AAFFESDH</div>
        ';

        return '
        <div class="pageTitle">Quotation</div>

        <div class="outer">
            <table class="border">
                <tr>
                    <td class="headLeft pad">
                        ' . ($mainLogo ? '<img class="logo" src="'.$mainLogo.'" />' : '<div class="shopName">THE TILE SHOP</div>') . '
                    </td>
                    <td class="headMid pad">' . $companyBlock . '</td>
                    <td class="headRight pad">
                        <div class="small"><i>Quotation No. :</i> '.$invoiceId.'</div>
                        <div class="line"></div>
                        <div class="small"><i>Date :</i> '.$date.'</div>
                        <div class="line"></div>
                        <div class="small"><i>Reference Name :</i> '.$refName.'</div>
                    </td>
                </tr>

                <tr>
                    <td colspan="3" style="padding:0;">
                        <table class="border">
                            <tr>
                                <td class="pad" style="width:50%;">
                                    <div class="b" style="color:#5a3b26;">Buyer (Bill To):</div>
                                    <div style="margin-top:6px;">
                                        <div class="b">'.$buyerName.'</div>
                                        <div>'.$buyerPhone.'</div>
                                        <div>'.$buyerAddr.'</div>
                                    </div>
                                </td>
                                <td class="pad" style="width:50%;">
                                    <div class="b" style="color:#5a3b26;">Consignee (Ship To):</div>
                                    <div style="margin-top:6px;">
                                        <div class="b">'.$shipName.'</div>
                                        <div>'.$buyerPhone.'</div>
                                        <div>'.$shipAddr.'</div>
                                    </div>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </div>
        ';
    }

    // ✅ Normalize item image from various possible DB keys
    private function normalizeItemImage($it) {
        // Try common keys (adjust/add if your DB uses different ones)
        $candidates = [
            $it['image'] ?? null,
            $it['image_url'] ?? null,
            $it['product_image'] ?? null,
            $it['product_image_url'] ?? null,
            $it['tile_image'] ?? null,
            $it['tile_image_url'] ?? null,
            $it['img'] ?? null,
        ];

        foreach ($candidates as $c) {
            if (!$c) continue;
            $p = $this->uploadImgPath($c);
            if ($p) return $p;
        }
        return null;
    }

    // ----------------- Items table (GROUP BY LOCATION + SR RESET) -----------------
    private function writeItemsTable($mpdf, $invoice) {
        $lineItems = $invoice['line_items'] ?? [];
        if (!is_array($lineItems)) $lineItems = [];

        // Start table
        $mpdf->WriteHTML('
        <div class="outer" style="border-top:none;">
            <table class="border">
                <tr class="th center">
                    <td style="width:6%;">SR<br>NO.</td>
                    <td style="width:16%;">NAME</td>
                    <td style="width:12%;">IMAGE</td>
                    <td style="width:18%;">SIZE</td>
                    <td style="width:12%;">QUANTITY</td>
                    <td style="width:12%;">RATE /<br>BOX</td>
                    <td style="width:12%;">RATE /<br>SQFT</td>
                    <td style="width:8%;">DISC.<br>(%)</td>
                    <td style="width:12%;" class="right">AMOUNT</td>
                </tr>
        ', \Mpdf\HTMLParserMode::HTML_BODY);
        

        // ✅ Group by location/section
        $groups = [];
        foreach ($lineItems as $it) {
            $locKey = trim((string)($it['section_name'] ?? ''));

            if ($locKey === '') {
            $locKey = trim((string)($it['remarks'] ?? ''));
            }
if ($locKey === '') {
    $locKey = trim((string)($it['tile_name'] ?? ''));
}
if ($locKey === '') {
    $locKey = trim((string)($it['product_name'] ?? ''));
}
if ($locKey === '') {
    $locKey = 'Items';
}

$groups[$locKey][] = $it;
        }

        $htmlChunk = '';
        $chunkLimit = 12000; // safe chunk size

        foreach ($groups as $locationName => $items) {

            // Location header row
            $htmlChunk .= '
                <tr class="locationRow">
                    <td colspan="9">' . $this->safe($locationName) . '</td>
                </tr>
            ';

            $sr = 1;
            $sectionTotal = 0.0;

            foreach ($items as $it) {

    // ✅ LOCATION FIX
    $locationName = trim((string)($it['section_name'] ?? ''));

    // fallback if section_name empty
    if ($locationName === '') {
        $locationName = trim((string)($it['product_name'] ?? 'Items'));
    }

    $name   = $this->safe($it['product_name'] ?? $it['tile_name'] ?? '');
    $size   = $this->safe($it['size'] ?? '');
    $qtyBox = (float)($it['box_qty'] ?? $it['quantity_box'] ?? 0);
    $rateBox= (float)($it['rate_per_box'] ?? 0);
    $rateSf = (float)($it['rate_per_sqft'] ?? 0);
    $disc   = (float)($it['discount_percent'] ?? 0);

    // Amount calculation
    $amt = (float)($it['final_amount'] ?? $it['amount'] ?? 0);
    if ($amt <= 0 && $qtyBox > 0 && $rateBox > 0) {
        $amt = $qtyBox * $rateBox;
        if ($disc > 0) $amt = $amt * (1 - ($disc/100));
    }

    $sectionTotal += $amt;

    $img = $this->normalizeItemImage($it);

    $htmlChunk .= '<tr>';
    $htmlChunk .= '<td class="center">' . $sr . '</td>';
    $htmlChunk .= '<td>' . $name . '</td>';

    if ($img) {
        $htmlChunk .= '<td class="center"><img class="tileImg" src="' . $img . '" /></td>';
    } else {
        $htmlChunk .= '<td class="center">-</td>';
    }

    $htmlChunk .= '
        <td class="center">' . $size . '</td>
        <td class="center">' . ($qtyBox > 0 ? number_format($qtyBox, 0) . ' box' : '-') . '</td>
        <td class="right">₹' . number_format($rateBox, 2) . '</td>
        <td class="right">₹' . number_format($rateSf, 2) . '</td>
        <td class="center">' . number_format($disc, 0) . '%</td>
        <td class="right">₹' . number_format($amt, 2) . '</td>
    ';

    $htmlChunk .= '</tr>';

    $sr++;

    if (strlen($htmlChunk) > $chunkLimit) {
        $mpdf->WriteHTML($htmlChunk, \Mpdf\HTMLParserMode::HTML_BODY);
        $htmlChunk = '';
    }
}

            // Location total row
            $htmlChunk .= '
                <tr>
                    <td colspan="8" class="right sectionTotalLabel">' . $this->safe($locationName) . '\'s Total Amount :</td>
                    <td class="right sectionTotalValue">₹' . number_format($sectionTotal, 2) . '</td>
                </tr>
            ';

            if (strlen($htmlChunk) > $chunkLimit) {
                $mpdf->WriteHTML($htmlChunk, \Mpdf\HTMLParserMode::HTML_BODY);
                $htmlChunk = '';
            }
        }

        // Flush remaining html
        if ($htmlChunk !== '') {
            $mpdf->WriteHTML($htmlChunk, \Mpdf\HTMLParserMode::HTML_BODY);
        }

        // Close table + wrapper
        $mpdf->WriteHTML('
            </table>
        </div>
        ', \Mpdf\HTMLParserMode::HTML_BODY);
    }

    // ----------------- Bottom block -----------------
    private function bottomBlockHtml($invoice) {
        $subtotal   = (float)($invoice['subtotal'] ?? 0);
        $transport  = (float)($invoice['transport_charges'] ?? 0);
        $unloading  = (float)($invoice['unloading_charges'] ?? 0);
        $gstAmount  = (float)($invoice['gst_amount'] ?? 0);
        $grandTotal = (float)($invoice['grand_total'] ?? 0);
        $subtotalR   = (int) round($subtotal);
        $transportR  = (int) round($transport);
        $unloadingR  = (int) round($unloading);
        $gstAmountR  = (int) round($gstAmount);
        $grandTotalR = (int) round($grandTotal);

        $remarks = trim((string)($invoice['remarks'] ?? ''));

        // Brand logos
        $brandImgs = [];
        $seen = [];

        for ($i=1; $i<=15; $i++) {
            $fname = 'brand_' . str_pad((string)$i, 2, '0', STR_PAD_LEFT) . '.png';
            $p = $this->brandImgPath($fname);

            if ($p && !in_array($p, $seen, true)) {
                $brandImgs[] = $p;
                $seen[] = $p;
            }
        }

        $bankRow = '
        <table class="border" style="border-top:none;">
            <tr>
                <td class="pad"><span class="b">Account Name:</span><br>SHREE SONANA SHETRPAL CERAMIC</td>
                <td class="pad"><span class="b">Bank Name:</span><br>HDFC BANK</td>
                <td class="pad"><span class="b">Account No.:</span><br>50200069370271</td>
                <td class="pad"><span class="b">IFSC:</span><br>HDFC0005291</td>
                <td class="pad"><span class="b">Branch:</span><br>HYDE PARK</td>
            </tr>
        </table>';

        $terms = '
        <div class="outer" style="margin-top:0; border-top:none;">
            <div class="boxTitle">TERMS & CONDITION</div>
            <div class="pad terms">
                1. Payment: 100% Advance<br>
                2. 2% Breakage mandatory<br>
                3. Delivery: 8-10 days as per availability.<br>
                4. Quotation Price valid for fifteen days.<br>
                5. Goods once sold will not be taken back or exchanged.<br>
                6. Quality complaints will not be entertained unless laid as instructed.<br>
                7. We are not responsible for any damage during transit.<br>
                8. Batch wise variation is inherent characteristic of ceramic, NO COMPLAINTS WILL BE ENTERTAINED AFTER INSTALLATION OF TILES.<br>
                9. Our responsibility ceases after the dispatch of goods from our premises.
            </div>
        </div>';

        $totals = '
        <div class="outer" style="border-top:none;">
            <table class="border">
                <tr>
                    <td style="width:70%; padding:0; vertical-align:top;">
                    <table class="border" style="width:100%; border-collapse:collapse;">
                    <tr><td class="pad" style="height:28px;"></td></tr>
                    <tr><td class="pad" style="height:28px;"></td></tr>
                    <tr><td class="pad" style="height:28px;"></td></tr>
                    <tr><td class="pad" style="height:28px;"></td></tr>
                    <tr><td class="pad" style="height:28px;"></td></tr>
                    </table>
                </td>                   
                    <td style="width:30%; padding:0;">
                        <table class="border" style="width:100%; border-collapse:collapse;">
                            <tr><td class="right pad">Total Amount :</td><td class="right pad b">₹'.number_format($subtotalR,0).'</td></tr>
                            <tr><td class="right pad">Transport Charges :</td><td class="right pad b">₹'.number_format($transportR,0).'</td></tr>
                            <tr><td class="right pad">Unloading Charges :</td><td class="right pad b">₹'.number_format($unloadingR,0).'</td></tr>
                            <tr><td class="right pad">GST Amount :</td><td class="right pad b">₹'.number_format($gstAmountR,0).'</td></tr>
                            <tr class="finalRow"><td class="right pad">Final Amount :</td><td class="right pad b">₹'.number_format($grandTotalR,0).'</td></tr>
                        </table>
                    </td>
                </tr>
            </table>
        </div>';

        $remarksBlock = '
        <div class="outer" style="border-top:none;">
            <div class="boxTitle">Overall Remarks :</div>
            <div class="pad" style="min-height:40px;">'.$this->safe($remarks).'</div>
        </div>';

        $brandsHtml = '';
        if (count($brandImgs) > 0) {
            $brandsHtml .= '<div class="brandsWrap">';
            foreach ($brandImgs as $b) {
                $brandsHtml .= '<img class="brandImg" src="'.$b.'" />';
            }
            $brandsHtml .= '</div>';
        }

        return $totals . $bankRow . $remarksBlock . $terms . $brandsHtml;
    }

    private function getFilename($invoiceId) {
        $safe = preg_replace('/[^A-Za-z0-9\-_]+/', '_', (string)$invoiceId);
        return 'Invoice_' . $safe . '.pdf';
    }
}
?>