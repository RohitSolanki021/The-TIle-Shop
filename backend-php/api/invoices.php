<?php
/**
 * Invoices API Endpoints
 * Handles CRUD operations for invoices with line items
 */

require_once __DIR__ . '/../utils/invoice_helper.php';

$db = Database::getInstance()->getConnection();
$helper = new InvoiceHelper($db);

// GET /api/invoices - Get all invoices
if ($requestMethod === 'GET' && !$id) {
    try {
        $stmt = $db->prepare("
            SELECT * FROM invoices 
            WHERE deleted = 0 
            ORDER BY created_at DESC
        ");
        $stmt->execute();
        $invoices = $stmt->fetchAll();
        
        sendJSON($invoices);
    } catch (PDOException $e) {
        sendError('Error fetching invoices: ' . $e->getMessage(), 500);
    }
}

// GET /api/invoices/:id - Get single invoice with line items
elseif ($requestMethod === 'GET' && $id && $action !== 'pdf') {
    try {
        // URL decode invoice ID (handles spaces and slashes)
        $invoiceId = urldecode($id);
        
        $stmt = $db->prepare("
            SELECT * FROM invoices 
            WHERE invoice_id = :id AND deleted = 0
        ");
        $stmt->execute(['id' => $invoiceId]);
        $invoice = $stmt->fetch();
        
        if (!$invoice) {
            sendError('Invoice not found', 404);
        }
        
        // Get line items
        $stmt = $db->prepare("
            SELECT * FROM invoice_items 
            WHERE invoice_id = :id 
            ORDER BY item_id ASC
        ");
        $stmt->execute(['id' => $invoiceId]);
        $invoice['line_items'] = $stmt->fetchAll();
        
        sendJSON($invoice);
    } catch (PDOException $e) {
        sendError('Error fetching invoice: ' . $e->getMessage(), 500);
    }
}

// POST /api/invoices - Create new invoice
elseif ($requestMethod === 'POST' && !$id) {
    try {
        $data = getRequestData();
        
        // Validate required fields
        if (empty($data['customer_id'])) {
            sendError('Customer ID is required', 400);
        }
        if (empty($data['line_items']) || !is_array($data['line_items'])) {
            sendError('Line items are required', 400);
        }
        
        $db->beginTransaction();
        
        // Generate invoice ID
        $invoiceId = $helper->generateInvoiceId();
        
        // Get customer details
        $stmt = $db->prepare("SELECT * FROM customers WHERE customer_id = :id AND deleted = 0");
        $stmt->execute(['id' => $data['customer_id']]);
        $customer = $stmt->fetch();
        
        if (!$customer) {
            $db->rollBack();
            sendError('Customer not found', 404);
        }
        
        // Calculate line items
        $calculatedItems = [];
        foreach ($data['line_items'] as $item) {
            $calculatedItem = $helper->calculateLineItem($item);
            $calculatedItems[] = $calculatedItem;
        }
        
        // Prepare invoice data
        $invoice = [
            'invoice_id' => $invoiceId,
            'customer_id' => $data['customer_id'],
            'customer_name' => $customer['name'],
            'customer_phone' => $customer['phone'],
            'customer_address' => $customer['address'],
            'customer_gstin' => $customer['gstin'],
            'ship_to_name' => $data['ship_to_name'] ?? $customer['name'],
            'ship_to_address' => $data['ship_to_address'] ?? $customer['address'],
            'reference_name' => $data['reference_name'] ?? '',
            'remarks' => $data['remarks'] ?? '',
            'date' => $data['date'] ?? date('Y-m-d'),
            'gst_percent' => $data['gst_percent'] ?? 18,
            'transport_charges' => $data['transport_charges'] ?? 0,
            'unloading_charges' => $data['unloading_charges'] ?? 0,
            'amount_paid' => $data['amount_paid'] ?? 0,
            'status' => $data['status'] ?? 'Draft'
        ];
        
        // Calculate totals
        $invoice = $helper->calculateInvoiceTotals($invoice, $calculatedItems);
        
        // Insert invoice
        $stmt = $db->prepare("
            INSERT INTO invoices (
                invoice_id, customer_id, customer_name, customer_phone, customer_address,
                customer_gstin, ship_to_name, ship_to_address, reference_name, remarks,
                date, subtotal, gst_percent, gst_amount, transport_charges, unloading_charges,
                grand_total, amount_paid, pending_balance, status, deleted
            ) VALUES (
                :invoice_id, :customer_id, :customer_name, :customer_phone, :customer_address,
                :customer_gstin, :ship_to_name, :ship_to_address, :reference_name, :remarks,
                :date, :subtotal, :gst_percent, :gst_amount, :transport_charges, :unloading_charges,
                :grand_total, :amount_paid, :pending_balance, :status, 0
            )
        ");
        
        $stmt->execute($invoice);
        
        // Insert line items
        $itemStmt = $db->prepare("
            INSERT INTO invoice_items (
                invoice_id, tile_id, section_name, product_name, size, coverage,
                box_coverage_sqft, rate_per_sqft, rate_per_box, box_qty, extra_sqft,
                total_sqft, discount_percent, amount_before_discount, discount_amount,
                final_amount, remarks
            ) VALUES (
                :invoice_id, :tile_id, :section_name, :product_name, :size, :coverage,
                :box_coverage_sqft, :rate_per_sqft, :rate_per_box, :box_qty, :extra_sqft,
                :total_sqft, :discount_percent, :amount_before_discount, :discount_amount,
                :final_amount, :remarks
            )
        ");
        
        foreach ($calculatedItems as $item) {
            $item['invoice_id'] = $invoiceId;
            $itemStmt->execute($item);
        }
        
        // Update customer pending balance
        $helper->recalculateCustomerPending($data['customer_id']);
        
        $db->commit();
        
        // Fetch and return created invoice
        $stmt = $db->prepare("SELECT * FROM invoices WHERE invoice_id = :id");
        $stmt->execute(['id' => $invoiceId]);
        $createdInvoice = $stmt->fetch();
        
        $stmt = $db->prepare("SELECT * FROM invoice_items WHERE invoice_id = :id");
        $stmt->execute(['id' => $invoiceId]);
        $createdInvoice['line_items'] = $stmt->fetchAll();
        
        sendJSON($createdInvoice, 201);
    } catch (PDOException $e) {
        $db->rollBack();
        sendError('Error creating invoice: ' . $e->getMessage(), 500);
    }
}

// DELETE /api/invoices/:id - Soft delete invoice
elseif ($requestMethod === 'DELETE' && $id) {
    try {
        $invoiceId = urldecode($id);
        
        $db->beginTransaction();
        
        // Get invoice to find customer_id
        $stmt = $db->prepare("SELECT customer_id FROM invoices WHERE invoice_id = :id AND deleted = 0");
        $stmt->execute(['id' => $invoiceId]);
        $invoice = $stmt->fetch();
        
        if (!$invoice) {
            $db->rollBack();
            sendError('Invoice not found', 404);
        }
        
        // Soft delete invoice
        $stmt = $db->prepare("
            UPDATE invoices 
            SET deleted = 1 
            WHERE invoice_id = :id
        ");
        $stmt->execute(['id' => $invoiceId]);
        
        // Recalculate customer pending
        $helper->recalculateCustomerPending($invoice['customer_id']);
        
        $db->commit();
        
        sendJSON(['message' => 'Invoice deleted successfully']);
    } catch (PDOException $e) {
        $db->rollBack();
        sendError('Error deleting invoice: ' . $e->getMessage(), 500);
    }
}

// GET /api/invoices/:id/pdf OR /api/public/invoices/:id/pdf - Generate PDF
elseif ($requestMethod === 'GET' && $id && $action === 'pdf') {
    require_once __DIR__ . '/../utils/pdf_generator.php';
    
    try {
        $invoiceId = urldecode($id);
        
        // Get invoice with line items
        $stmt = $db->prepare("
            SELECT * FROM invoices 
            WHERE invoice_id = :id AND deleted = 0
        ");
        $stmt->execute(['id' => $invoiceId]);
        $invoice = $stmt->fetch();
        
        if (!$invoice) {
            sendError('Invoice not found', 404);
        }
        
        $stmt = $db->prepare("
            SELECT * FROM invoice_items 
            WHERE invoice_id = :id 
            ORDER BY item_id ASC
        ");
        $stmt->execute(['id' => $invoiceId]);
        $invoice['line_items'] = $stmt->fetchAll();
        
        // Generate PDF
        $pdfGenerator = new PDFGenerator();
        $pdfPath = $pdfGenerator->generateInvoicePDF($invoice);
        
        if (!$pdfPath || !file_exists($pdfPath)) {
            sendError('Failed to generate PDF', 500);
        }
        
        // Serve PDF
        header('Content-Type: application/pdf');
        header('Content-Disposition: inline; filename="Invoice_' . str_replace('/', '-', $invoiceId) . '.pdf"');
        header('Content-Length: ' . filesize($pdfPath));
        readfile($pdfPath);
        exit;
    } catch (Exception $e) {
        sendError('Error generating PDF: ' . $e->getMessage(), 500);
    }
}

else {
    sendError('Method not allowed', 405);
}
?>