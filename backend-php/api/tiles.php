<?php
/**
 * Tiles API Endpoints
 * Handles CRUD operations for tiles
 */

$db = Database::getInstance()->getConnection();

// GET /api/tiles - Get all tiles
if ($requestMethod === 'GET' && !$id) {
    try {
        $stmt = $db->prepare("
            SELECT * FROM tiles 
            WHERE deleted = 0 
            ORDER BY created_at DESC
        ");
        $stmt->execute();
        $tiles = $stmt->fetchAll();
        
        sendJSON($tiles);
    } catch (PDOException $e) {
        sendError('Error fetching tiles: ' . $e->getMessage(), 500);
    }
}

// GET /api/tiles/:id - Get single tile
elseif ($requestMethod === 'GET' && $id) {
    try {
        // Check if requesting by size
        if ($action === 'by-size') {
            $size = urldecode($id);
            $stmt = $db->prepare("
                SELECT * FROM tiles 
                WHERE size = :size AND deleted = 0 
                LIMIT 1
            ");
            $stmt->execute(['size' => $size]);
        } else {
            $stmt = $db->prepare("
                SELECT * FROM tiles 
                WHERE tile_id = :id AND deleted = 0
            ");
            $stmt->execute(['id' => $id]);
        }
        
        $tile = $stmt->fetch();
        
        if (!$tile) {
            sendError('Tile not found', 404);
        }
        
        sendJSON($tile);
    } catch (PDOException $e) {
        sendError('Error fetching tile: ' . $e->getMessage(), 500);
    }
}

// POST /api/tiles - Create new tile
elseif ($requestMethod === 'POST' && !$id) {
    try {
        $data = getRequestData();
        
        // Validate required fields
        if (empty($data['size'])) {
            sendError('Size is required', 400);
        }
        
        $tileId = generateUUID();
        
        $stmt = $db->prepare("
            INSERT INTO tiles (
                tile_id, size, coverage, box_coverage_sqft, box_packing,
                product_name, rate_per_sqft, rate_per_box, active, deleted
            ) VALUES (
                :tile_id, :size, :coverage, :box_coverage_sqft, :box_packing,
                :product_name, :rate_per_sqft, :rate_per_box, 1, 0
            )
        ");
        
        $stmt->execute([
            'tile_id' => $tileId,
            'size' => $data['size'],
            'coverage' => $data['coverage'] ?? 0,
            'box_coverage_sqft' => $data['box_coverage_sqft'] ?? $data['coverage'] ?? 0,
            'box_packing' => $data['box_packing'] ?? 0,
            'product_name' => $data['product_name'] ?? null,
            'rate_per_sqft' => $data['rate_per_sqft'] ?? null,
            'rate_per_box' => $data['rate_per_box'] ?? null
        ]);
        
        // Fetch and return created tile
        $stmt = $db->prepare("SELECT * FROM tiles WHERE tile_id = :id");
        $stmt->execute(['id' => $tileId]);
        $tile = $stmt->fetch();
        
        sendJSON($tile, 201);
    } catch (PDOException $e) {
        sendError('Error creating tile: ' . $e->getMessage(), 500);
    }
}

// PUT /api/tiles/:id - Update tile
elseif ($requestMethod === 'PUT' && $id) {
    try {
        $data = getRequestData();
        
        // Check if tile exists
        $stmt = $db->prepare("SELECT * FROM tiles WHERE tile_id = :id AND deleted = 0");
        $stmt->execute(['id' => $id]);
        if (!$stmt->fetch()) {
            sendError('Tile not found', 404);
        }
        
        // Build update query dynamically
        $updates = [];
        $params = ['id' => $id];
        
        $allowedFields = ['size', 'coverage', 'box_coverage_sqft', 'box_packing', 
                         'product_name', 'rate_per_sqft', 'rate_per_box'];
        
        foreach ($allowedFields as $field) {
            if (isset($data[$field])) {
                $updates[] = "$field = :$field";
                $params[$field] = $data[$field];
            }
        }
        
        if (empty($updates)) {
            sendError('No valid fields to update', 400);
        }
        
        $sql = "UPDATE tiles SET " . implode(', ', $updates) . " WHERE tile_id = :id";
        $stmt = $db->prepare($sql);
        $stmt->execute($params);
        
        // Fetch and return updated tile
        $stmt = $db->prepare("SELECT * FROM tiles WHERE tile_id = :id");
        $stmt->execute(['id' => $id]);
        $tile = $stmt->fetch();
        
        sendJSON($tile);
    } catch (PDOException $e) {
        sendError('Error updating tile: ' . $e->getMessage(), 500);
    }
}

// DELETE /api/tiles/:id - Soft delete tile
elseif ($requestMethod === 'DELETE' && $id) {
    try {
        $stmt = $db->prepare("
            UPDATE tiles 
            SET deleted = 1 
            WHERE tile_id = :id AND deleted = 0
        ");
        $stmt->execute(['id' => $id]);
        
        if ($stmt->rowCount() === 0) {
            sendError('Tile not found', 404);
        }
        
        sendJSON(['message' => 'Tile deleted successfully']);
    } catch (PDOException $e) {
        sendError('Error deleting tile: ' . $e->getMessage(), 500);
    }
}

else {
    sendError('Method not allowed', 405);
}
?>
