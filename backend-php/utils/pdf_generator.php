<?php
/**
 * PDF Generator
 * Generates invoice PDFs using mPDF
 */

class PDFGenerator {
    private $useMPDF = false;
    
    public function __construct() {
        // Check if mPDF is available
        if (file_exists(__DIR__ . '/../vendor/autoload.php')) {
            require_once __DIR__ . '/../vendor/autoload.php';
            if (class_exists('\\Mpdf\\Mpdf')) {
                $this->useMPDF = true;
            }
        }
    }
    
    /**
     * Generate invoice PDF
     */
    public function generateInvoicePDF($invoice) {
        $html = $this->generateInvoiceHTML($invoice);
        
        if ($this->useMPDF) {
            return $this->generateWithMPDF($invoice, $html);
        } else {
            // Fallback: save as HTML
            return $this->saveAsHTML($invoice, $html);
        }
    }
    
    /**
     * Generate PDF using mPDF library
     */
    private function generateWithMPDF($invoice, $html) {
        try {
            $mpdf = new \Mpdf\Mpdf([
                'mode' => 'utf-8',
                'format' => 'A4',
                'margin_left' => 10,
                'margin_right' => 10,
                'margin_top' => 10,
                'margin_bottom' => 10
            ]);
            
            $mpdf->WriteHTML($html);
            
            $filename = $this->getFilename($invoice['invoice_id']);
            $filepath = PDF_DIR . $filename;
            
            $mpdf->Output($filepath, 'F');
            
            return $filepath;
        } catch (Exception $e) {
            error_log("mPDF Error: " . $e->getMessage());
            return $this->saveAsHTML($invoice, $html);
        }
    }
    
    /**
     * Save as HTML (fallback)
     */
    private function saveAsHTML($invoice, $html) {
        $filename = str_replace('.pdf', '.html', $this->getFilename($invoice['invoice_id']));
        $filepath = PDF_DIR . $filename;
        
        file_put_contents($filepath, $html);
        
        return $filepath;
    }
    
    /**
     * Generate invoice HTML
     */
    private function generateInvoiceHTML($invoice) {
        $invoiceId = htmlspecialchars($invoice['invoice_id']);
        $date = date('d-m-Y', strtotime($invoice['date']));
        
        $html = '<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Invoice ' . $invoiceId . '</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            font-size: 10pt;
            margin: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
        }
        .company-name {
            font-size: 24pt;
            font-weight: bold;
            color: #2563eb;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }
        th, td {
            border: 1px solid #ccc;
            padding: 8px;
        }
        th {
            background-color: #f3f4f6;
            text-align: left;
        }
        .text-right { text-align: right; }
        .totals { 
            float: right;
            width: 300px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="company-name">THE TILE SHOP</div>
        <div>Complete Tiles & Sanitary Solution</div>
    </div>
    
    <h2>TAX INVOICE</h2>
    
    <p><strong>Invoice No:</strong> ' . $invoiceId . '</p>
    <p><strong>Date:</strong> ' . $date . '</p>
    <p><strong>Customer:</strong> ' . htmlspecialchars($invoice['customer_name']) . '</p>
    <p><strong>Phone:</strong> ' . htmlspecialchars($invoice['customer_phone']) . '</p>
    
    <table>
        <thead>
            <tr>
                <th>Product</th>
                <th>Size</th>
                <th class="text-right">Box Qty</th>
                <th class="text-right">Total Sqft</th>
                <th class="text-right">Rate/Sqft</th>
                <th class="text-right">Amount</th>
            </tr>
        </thead>
        <tbody>';
        
        foreach ($invoice['line_items'] as $item) {
            $html .= '<tr>
                <td>' . htmlspecialchars($item['product_name']) . '</td>
                <td>' . htmlspecialchars($item['size']) . '</td>
                <td class="text-right">' . number_format($item['box_qty']) . '</td>
                <td class="text-right">' . number_format($item['total_sqft'], 2) . '</td>
                <td class="text-right">₹' . number_format($item['rate_per_sqft'], 2) . '</td>
                <td class="text-right">₹' . number_format($item['final_amount'], 2) . '</td>
            </tr>';
        }
        
        $html .= '</tbody>
    </table>
    
    <div class="totals">
        <p>Subtotal: ₹' . number_format($invoice['subtotal'], 2) . '</p>
        <p>GST (' . number_format($invoice['gst_percent'], 1) . '%): ₹' . number_format($invoice['gst_amount'], 2) . '</p>
        <p><strong>Grand Total: ₹' . number_format($invoice['grand_total'], 2) . '</strong></p>
        <p>Paid: ₹' . number_format($invoice['amount_paid'], 2) . '</p>
        <p><strong>Pending: ₹' . number_format($invoice['pending_balance'], 2) . '</strong></p>
    </div>
    
    <div style="clear: both; margin-top: 50px; text-align: center;">
        <p>Thank you for your business!</p>
    </div>
</body>
</html>';
        
        return $html;
    }
    
    /**
     * Get filename for invoice PDF
     */
    private function getFilename($invoiceId) {
        return 'Invoice_' . str_replace(['/', ' '], '_', $invoiceId) . '.pdf';
    }
}
?>