<?php
/**
 * Invoices API Endpoints
 * Handles CRUD operations for invoices with line items
 */

require_once __DIR__ . '/../utils/invoice_helper.php';

$db = Database::getInstance()->getConnection();
$helper = new InvoiceHelper($db);

// Get request variables from router
$requestMethod = $GLOBALS['requestMethod'];
$id = $GLOBALS['id'] ?? null;
$action = $GLOBALS['action'] ?? null;

error_log("Invoices API - Method: $requestMethod, ID: " . ($id ?? 'null') . ", Action: " . ($action ?? 'null'));

// Helper: filter array keys for PDO execute
function pickKeys(array $source, array $allowedKeys): array {
    $out = [];
    foreach ($allowedKeys as $k) {
        $out[$k] = $source[$k] ?? null;
    }
    return $out;
}

/**
 * ---------------------------
 * GET /api/invoices - Get all invoices
 * ---------------------------
 */
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

/**
 * ---------------------------
 * GET /api/invoices/:id - Get single invoice with line items
 * ---------------------------
 */
elseif ($requestMethod === 'GET' && $id && $action !== 'pdf') {
    try {
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

/**
 * ---------------------------
 * POST /api/invoices - Create new invoice
 * ---------------------------
 */
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

        // Get customer
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

        // Prepare invoice base
        $invoice = [
            'invoice_id' => $invoiceId,
            'customer_id' => $data['customer_id'],
            'customer_name' => $customer['name'],
            'customer_phone' => $customer['phone'],
            'customer_address' => $customer['address'],
            'customer_gstin' => $customer['gstin'],

            // If frontend does not send ship_to_*, fallback to customer
            'ship_to_name' => $data['ship_to_name'] ?? $customer['name'],
            'ship_to_address' => $data['ship_to_address'] ?? $customer['address'],

            // Optional fields
            'reference_name' => $data['reference_name'] ?? '',
            'remarks' => $data['remarks'] ?? '',
            'date' => $data['date'] ?? date('Y-m-d'),

            // Charges / status
            'gst_percent' => isset($data['gst_percent']) ? (float)$data['gst_percent'] : 18,
            'transport_charges' => isset($data['transport_charges']) ? (float)$data['transport_charges'] : 0,
            'unloading_charges' => isset($data['unloading_charges']) ? (float)$data['unloading_charges'] : 0,
            'amount_paid' => isset($data['amount_paid']) ? (float)$data['amount_paid'] : 0,
            'status' => $data['status'] ?? 'Draft'
        ];

        // Add totals (subtotal/gst_amount/grand_total/pending_balance etc.)
        $invoice = $helper->calculateInvoiceTotals($invoice, $calculatedItems);

        // INSERT invoice (IMPORTANT: send only params that exist in SQL)
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

        $invoiceParams = pickKeys($invoice, [
            'invoice_id', 'customer_id', 'customer_name', 'customer_phone', 'customer_address',
            'customer_gstin', 'ship_to_name', 'ship_to_address', 'reference_name', 'remarks',
            'date', 'subtotal', 'gst_percent', 'gst_amount', 'transport_charges', 'unloading_charges',
            'grand_total', 'amount_paid', 'pending_balance', 'status'
        ]);

        $stmt->execute($invoiceParams);

        // INSERT items (IMPORTANT: filter params)
                $itemStmt = $db->prepare("
            INSERT INTO invoice_items (
                invoice_id, tile_id, section_name, product_name, tile_name, tile_image,
                size, coverage,
                box_coverage_sqft, rate_per_sqft, rate_per_box, box_qty, extra_sqft,
                total_sqft, discount_percent, amount_before_discount, discount_amount,
                final_amount, remarks
            ) VALUES (
                :invoice_id, :tile_id, :section_name, :product_name, :tile_name, :tile_image,
                :size, :coverage,
                :box_coverage_sqft, :rate_per_sqft, :rate_per_box, :box_qty, :extra_sqft,
                :total_sqft, :discount_percent, :amount_before_discount, :discount_amount,
                :final_amount, :remarks
            )
        ");

        foreach ($calculatedItems as $item) {
            $item['invoice_id'] = $invoiceId;

            $itemParams = pickKeys($item, [
            'invoice_id', 'tile_id', 'section_name', 'product_name', 'tile_name', 'tile_image',
            'size', 'coverage',
            'box_coverage_sqft', 'rate_per_sqft', 'rate_per_box', 'box_qty', 'extra_sqft',
            'total_sqft', 'discount_percent', 'amount_before_discount', 'discount_amount',
            'final_amount', 'remarks'
        ]);
            $itemStmt->execute($itemParams);
        }

        // Recalculate customer pending
        $helper->recalculateCustomerPending($data['customer_id']);

        $db->commit();

        // Return created invoice + items
        $stmt = $db->prepare("SELECT * FROM invoices WHERE invoice_id = :id");
        $stmt->execute(['id' => $invoiceId]);
        $createdInvoice = $stmt->fetch();

        $stmt = $db->prepare("SELECT * FROM invoice_items WHERE invoice_id = :id ORDER BY item_id ASC");
        $stmt->execute(['id' => $invoiceId]);
        $createdInvoice['line_items'] = $stmt->fetchAll();

        sendJSON($createdInvoice, 201);

    } catch (PDOException $e) {
        if ($db->inTransaction()) {
            $db->rollBack();
        }
        sendError('Error creating invoice: ' . $e->getMessage(), 500);
    }
}

/**
 * ---------------------------
 * PUT /api/invoices/:id - Update invoice + line items
 * ---------------------------
 */
elseif (($requestMethod === 'PUT' || $requestMethod === 'PATCH') && $id) {
    try {
        $data = getRequestData();
        $invoiceId = $data['invoice_id'] ?? rawurldecode($id);

        if (empty($data['customer_id'])) {
            sendError('Customer ID is required', 400);
        }
        if (empty($data['line_items']) || !is_array($data['line_items'])) {
            sendError('Line items are required', 400);
        }

        $db->beginTransaction();

        // Fetch existing invoice
        $stmt = $db->prepare("SELECT * FROM invoices WHERE invoice_id = :id AND deleted = 0");
        $stmt->execute(['id' => $invoiceId]);
        $existingInvoice = $stmt->fetch();

        if (!$existingInvoice) {
            $db->rollBack();
            sendError('Invoice not found', 404);
        }

        // Get customer
        $stmt = $db->prepare("SELECT * FROM customers WHERE customer_id = :id AND deleted = 0");
        $stmt->execute(['id' => $data['customer_id']]);
        $customer = $stmt->fetch();

        if (!$customer) {
            $db->rollBack();
            sendError('Customer not found', 404);
        }

        // Recalculate line items
        $calculatedItems = [];
        foreach ($data['line_items'] as $item) {
            $calculatedItem = $helper->calculateLineItem($item);

            // Keep tile_name + tile_image if frontend sends
            $calculatedItem['tile_name']  = $item['tile_name'] ?? ($item['product_name'] ?? '');
            $calculatedItem['tile_image'] = $item['tile_image'] ?? null;

            $calculatedItems[] = $calculatedItem;
        }

        // Build updated invoice
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
            'date' => $data['date'] ?? ($existingInvoice['date'] ?? date('Y-m-d')),

            'gst_percent' => isset($data['gst_percent']) ? (float)$data['gst_percent'] : (float)($existingInvoice['gst_percent'] ?? 18),
            'transport_charges' => isset($data['transport_charges']) ? (float)$data['transport_charges'] : (float)($existingInvoice['transport_charges'] ?? 0),
            'unloading_charges' => isset($data['unloading_charges']) ? (float)$data['unloading_charges'] : (float)($existingInvoice['unloading_charges'] ?? 0),
            'amount_paid' => isset($data['amount_paid']) ? (float)$data['amount_paid'] : (float)($existingInvoice['amount_paid'] ?? 0),
            'status' => $data['status'] ?? ($existingInvoice['status'] ?? 'Draft'),
        ];

        // Totals
        $invoice = $helper->calculateInvoiceTotals($invoice, $calculatedItems);

        // UPDATE invoice
        $stmt = $db->prepare("
            UPDATE invoices SET
                customer_id = :customer_id,
                customer_name = :customer_name,
                customer_phone = :customer_phone,
                customer_address = :customer_address,
                customer_gstin = :customer_gstin,
                ship_to_name = :ship_to_name,
                ship_to_address = :ship_to_address,
                reference_name = :reference_name,
                remarks = :remarks,
                date = :date,
                subtotal = :subtotal,
                gst_percent = :gst_percent,
                gst_amount = :gst_amount,
                transport_charges = :transport_charges,
                unloading_charges = :unloading_charges,
                grand_total = :grand_total,
                amount_paid = :amount_paid,
                pending_balance = :pending_balance,
                status = :status
            WHERE invoice_id = :invoice_id AND deleted = 0
        ");

        $invoiceParams = pickKeys($invoice, [
            'invoice_id', 'customer_id', 'customer_name', 'customer_phone', 'customer_address',
            'customer_gstin', 'ship_to_name', 'ship_to_address', 'reference_name', 'remarks',
            'date', 'subtotal', 'gst_percent', 'gst_amount', 'transport_charges', 'unloading_charges',
            'grand_total', 'amount_paid', 'pending_balance', 'status'
        ]);

        $stmt->execute($invoiceParams);

        // Replace items: delete old + insert new
        $stmt = $db->prepare("DELETE FROM invoice_items WHERE invoice_id = :id");
        $stmt->execute(['id' => $invoiceId]);

        $itemStmt = $db->prepare("
            INSERT INTO invoice_items (
                invoice_id, tile_id, section_name, product_name, tile_name, tile_image,
                size, coverage,
                box_coverage_sqft, rate_per_sqft, rate_per_box, box_qty, extra_sqft,
                total_sqft, discount_percent, amount_before_discount, discount_amount,
                final_amount, remarks
            ) VALUES (
                :invoice_id, :tile_id, :section_name, :product_name, :tile_name, :tile_image,
                :size, :coverage,
                :box_coverage_sqft, :rate_per_sqft, :rate_per_box, :box_qty, :extra_sqft,
                :total_sqft, :discount_percent, :amount_before_discount, :discount_amount,
                :final_amount, :remarks
            )
        ");

        foreach ($calculatedItems as $item) {
            $item['invoice_id'] = $invoiceId;

            $itemParams = pickKeys($item, [
                'invoice_id', 'tile_id', 'section_name', 'product_name', 'tile_name', 'tile_image',
                'size', 'coverage',
                'box_coverage_sqft', 'rate_per_sqft', 'rate_per_box', 'box_qty', 'extra_sqft',
                'total_sqft', 'discount_percent', 'amount_before_discount', 'discount_amount',
                'final_amount', 'remarks'
            ]);

            $itemStmt->execute($itemParams);
        }

        // Recalculate customer pending
        $helper->recalculateCustomerPending($data['customer_id']);

        $db->commit();

        // Return updated invoice
        $stmt = $db->prepare("SELECT * FROM invoices WHERE invoice_id = :id");
        $stmt->execute(['id' => $invoiceId]);
        $updatedInvoice = $stmt->fetch();

        $stmt = $db->prepare("SELECT * FROM invoice_items WHERE invoice_id = :id ORDER BY item_id ASC");
        $stmt->execute(['id' => $invoiceId]);
        $updatedInvoice['line_items'] = $stmt->fetchAll();

        sendJSON($updatedInvoice);

    } catch (PDOException $e) {
        if ($db->inTransaction()) $db->rollBack();
        sendError('Error updating invoice: ' . $e->getMessage(), 500);
    }
}


/**
 * ---------------------------
 * DELETE /api/invoices/:id - Soft delete invoice
 * ---------------------------
 */
elseif ($requestMethod === 'DELETE' && $id) {
    try {
        $invoiceId = urldecode($id);

        $db->beginTransaction();

        // Find customer_id
        $stmt = $db->prepare("SELECT customer_id FROM invoices WHERE invoice_id = :id AND deleted = 0");
        $stmt->execute(['id' => $invoiceId]);
        $invoice = $stmt->fetch();

        if (!$invoice) {
            $db->rollBack();
            sendError('Invoice not found', 404);
        }

        $stmt = $db->prepare("
            UPDATE invoices 
            SET deleted = 1 
            WHERE invoice_id = :id
        ");
        $stmt->execute(['id' => $invoiceId]);

        $helper->recalculateCustomerPending($invoice['customer_id']);

        $db->commit();

        sendJSON(['message' => 'Invoice deleted successfully']);
    } catch (PDOException $e) {
        if ($db->inTransaction()) {
            $db->rollBack();
        }
        sendError('Error deleting invoice: ' . $e->getMessage(), 500);
    }
}

/**
 * ---------------------------
 * GET /api/invoices/:id/pdf - Generate PDF
 * ---------------------------
 */
elseif ($requestMethod === 'GET' && $id && $action === 'pdf') {
    require_once __DIR__ . '/../utils/pdf_generator.php';

    try {
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

        $stmt = $db->prepare("
            SELECT * FROM invoice_items 
            WHERE invoice_id = :id 
            ORDER BY item_id ASC
        ");
        $stmt->execute(['id' => $invoiceId]);
        $invoice['line_items'] = $stmt->fetchAll();

        $pdfGenerator = new PDFGenerator();
        $pdfPath = $pdfGenerator->generateInvoicePDF($invoice);

        if (!$pdfPath || !file_exists($pdfPath)) {
            sendError('Failed to generate PDF', 500);
        }

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