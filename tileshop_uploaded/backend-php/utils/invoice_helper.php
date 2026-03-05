<?php
/**
 * Invoice Helper Functions
 * Invoice number generation and calculations
 */

class InvoiceHelper {
    private $db;
    
    public function __construct($db) {
        $this->db = $db;
    }
    
    /**
     * Generate invoice ID in format: TTS / XXX / YYYY-YY
     * Financial year: April to March
     */
    public function generateInvoiceId() {
        $now = new DateTime();
        $currentMonth = (int)$now->format('n');
        $currentYear = (int)$now->format('Y');
        
        // Determine financial year
        if ($currentMonth >= 4) {
            $fyStart = $currentYear;
            $fyEnd = $currentYear + 1;
        } else {
            $fyStart = $currentYear - 1;
            $fyEnd = $currentYear;
        }
        
        $fyString = $fyStart . '-' . substr($fyEnd, 2, 2); // e.g., "2025-26"
        
        // Get or create sequence for this financial year
        $stmt = $this->db->prepare("
            SELECT last_sequence FROM invoice_sequence 
            WHERE financial_year = :fy FOR UPDATE
        ");
        $stmt->execute(['fy' => $fyString]);
        $row = $stmt->fetch();
        
        if ($row) {
            $nextSequence = $row['last_sequence'] + 1;
            $stmt = $this->db->prepare("
                UPDATE invoice_sequence 
                SET last_sequence = :seq 
                WHERE financial_year = :fy
            ");
            $stmt->execute(['seq' => $nextSequence, 'fy' => $fyString]);
        } else {
            $nextSequence = 1;
            $stmt = $this->db->prepare("
                INSERT INTO invoice_sequence (financial_year, last_sequence) 
                VALUES (:fy, :seq)
            ");
            $stmt->execute(['fy' => $fyString, 'seq' => $nextSequence]);
        }
        
        // Format: TTS / 001 / 2025-26
        $invoiceId = sprintf('TTS / %03d / %s', $nextSequence, $fyString);
        
        return $invoiceId;
    }
    
    /**
     * Calculate bidirectional rates
     */
    public function calculateBidirectionalRate($coverage, $rateSqft, $rateBox) {
        if ($coverage <= 0) {
            return [$rateSqft ?: 0, $rateBox ?: 0];
        }
        
        if ($rateSqft && $rateSqft > 0 && (!$rateBox || $rateBox == 0)) {
            $rateBox = $rateSqft * $coverage;
        } elseif ($rateBox && $rateBox > 0 && (!$rateSqft || $rateSqft == 0)) {
            $rateSqft = $rateBox / $coverage;
        }
        
        return [$rateSqft ?: 0, $rateBox ?: 0];
    }
    
    /**
     * Calculate line item amounts
     */
    public function calculateLineItem($item) {
        $coverage = $item['coverage'] > 0 ? $item['coverage'] : $item['box_coverage_sqft'];
        
        // Calculate bidirectional rates
        list($rateSqft, $rateBox) = $this->calculateBidirectionalRate(
            $coverage,
            $item['rate_per_sqft'] ?? 0,
            $item['rate_per_box'] ?? 0
        );
        
        $item['rate_per_sqft'] = $rateSqft;
        $item['rate_per_box'] = $rateBox;
        
        // Calculate total sqft
        $item['total_sqft'] = ($item['box_qty'] * $coverage) + ($item['extra_sqft'] ?? 0);
        
        // Calculate amount before discount
        $item['amount_before_discount'] = $item['total_sqft'] * $rateSqft;
        
        // Calculate discount
        $discountPercent = $item['discount_percent'] ?? 0;
        $item['discount_amount'] = $item['amount_before_discount'] * ($discountPercent / 100);
        
        // Calculate final amount
        $item['final_amount'] = $item['amount_before_discount'] - $item['discount_amount'];
        
        return $item;
    }
    
    /**
     * Calculate invoice totals
     */
    public function calculateInvoiceTotals($invoice, $lineItems) {
        $subtotal = 0;
        foreach ($lineItems as $item) {
            $subtotal += $item['final_amount'];
        }
        
        $invoice['subtotal'] = $subtotal;
        
        // Calculate GST
        $gstPercent = $invoice['gst_percent'] ?? 18;
        $invoice['gst_amount'] = $subtotal * ($gstPercent / 100);
        
        // Calculate grand total
        $invoice['grand_total'] = $subtotal + 
                                  $invoice['gst_amount'] + 
                                  ($invoice['transport_charges'] ?? 0) + 
                                  ($invoice['unloading_charges'] ?? 0);
        
        // Calculate pending balance
        $invoice['pending_balance'] = $invoice['grand_total'] - ($invoice['amount_paid'] ?? 0);
        
        return $invoice;
    }
    
    /**
     * Recalculate customer total pending
     */
    public function recalculateCustomerPending($customerId) {
        try {
            $stmt = $this->db->prepare("
                SELECT SUM(pending_balance) as total 
                FROM invoices 
                WHERE customer_id = :id AND deleted = 0
            ");
            $stmt->execute(['id' => $customerId]);
            $row = $stmt->fetch();
            
            $totalPending = $row['total'] ?: 0;
            
            $stmt = $this->db->prepare("
                UPDATE customers 
                SET total_pending = :total 
                WHERE customer_id = :id
            ");
            $stmt->execute(['total' => $totalPending, 'id' => $customerId]);
            
            return $totalPending;
        } catch (PDOException $e) {
            error_log("Error recalculating customer pending: " . $e->getMessage());
            return 0;
        }
    }
}
?>
