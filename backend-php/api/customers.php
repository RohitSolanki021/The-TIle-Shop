<?php
/**
 * Customers API Endpoints
 * Handles CRUD operations for customers
 */

$db = Database::getInstance()->getConnection();

// GET /api/customers - Get all customers
if ($requestMethod === 'GET' && !$id) {
    try {
        $stmt = $db->prepare("
            SELECT * FROM customers 
            WHERE deleted = 0 
            ORDER BY name ASC
        ");
        $stmt->execute();
        $customers = $stmt->fetchAll();
        
        sendJSON($customers);
    } catch (PDOException $e) {
        sendError('Error fetching customers: ' . $e->getMessage(), 500);
    }
}

// GET /api/customers/:id - Get single customer
elseif ($requestMethod === 'GET' && $id) {
    try {
        $stmt = $db->prepare("
            SELECT * FROM customers 
            WHERE customer_id = :id AND deleted = 0
        ");
        $stmt->execute(['id' => $id]);
        $customer = $stmt->fetch();
        
        if (!$customer) {
            sendError('Customer not found', 404);
        }
        
        sendJSON($customer);
    } catch (PDOException $e) {
        sendError('Error fetching customer: ' . $e->getMessage(), 500);
    }
}

// POST /api/customers - Create new customer
elseif ($requestMethod === 'POST' && !$id) {
    try {
        $data = getRequestData();
        
        // Validate required fields
        if (empty($data['name'])) {
            sendError('Name is required', 400);
        }
        if (empty($data['phone'])) {
            sendError('Phone is required', 400);
        }
        
        $customerId = generateUUID();
        
        $stmt = $db->prepare("
            INSERT INTO customers (
                customer_id, name, phone, address, gstin, total_pending, deleted
            ) VALUES (
                :customer_id, :name, :phone, :address, :gstin, 0, 0
            )
        ");
        
        $stmt->execute([
            'customer_id' => $customerId,
            'name' => $data['name'],
            'phone' => $data['phone'],
            'address' => $data['address'] ?? '',
            'gstin' => $data['gstin'] ?? null
        ]);
        
        // Fetch and return created customer
        $stmt = $db->prepare("SELECT * FROM customers WHERE customer_id = :id");
        $stmt->execute(['id' => $customerId]);
        $customer = $stmt->fetch();
        
        sendJSON($customer, 201);
    } catch (PDOException $e) {
        sendError('Error creating customer: ' . $e->getMessage(), 500);
    }
}

// PUT /api/customers/:id - Update customer
elseif ($requestMethod === 'PUT' && $id) {
    try {
        $data = getRequestData();
        
        // Check if customer exists
        $stmt = $db->prepare("SELECT * FROM customers WHERE customer_id = :id AND deleted = 0");
        $stmt->execute(['id' => $id]);
        if (!$stmt->fetch()) {
            sendError('Customer not found', 404);
        }
        
        // Build update query
        $updates = [];
        $params = ['id' => $id];
        
        $allowedFields = ['name', 'phone', 'address', 'gstin'];
        
        foreach ($allowedFields as $field) {
            if (isset($data[$field])) {
                $updates[] = "$field = :$field";
                $params[$field] = $data[$field];
            }
        }
        
        if (empty($updates)) {
            sendError('No valid fields to update', 400);
        }
        
        $sql = "UPDATE customers SET " . implode(', ', $updates) . " WHERE customer_id = :id";
        $stmt = $db->prepare($sql);
        $stmt->execute($params);
        
        // Fetch and return updated customer
        $stmt = $db->prepare("SELECT * FROM customers WHERE customer_id = :id");
        $stmt->execute(['id' => $id]);
        $customer = $stmt->fetch();
        
        sendJSON($customer);
    } catch (PDOException $e) {
        sendError('Error updating customer: ' . $e->getMessage(), 500);
    }
}

// DELETE /api/customers/:id - Soft delete customer
elseif ($requestMethod === 'DELETE' && $id) {
    try {
        $stmt = $db->prepare("
            UPDATE customers 
            SET deleted = 1 
            WHERE customer_id = :id AND deleted = 0
        ");
        $stmt->execute(['id' => $id]);
        
        if ($stmt->rowCount() === 0) {
            sendError('Customer not found', 404);
        }
        
        sendJSON(['message' => 'Customer deleted successfully']);
    } catch (PDOException $e) {
        sendError('Error deleting customer: ' . $e->getMessage(), 500);
    }
}

else {
    sendError('Method not allowed', 405);
}
?>
