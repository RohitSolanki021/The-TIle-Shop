<?php
/**
 * The Tile Shop - API Router
 * Main entry point for all API requests
 */

// Enable CORS
header('Access-Control-Allow-Origin: ' . (defined('CORS_ORIGIN') ? CORS_ORIGIN : '*'));
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');
header('Access-Control-Allow-Credentials: true');

// Handle preflight requests
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// Load configuration
require_once __DIR__ . '/config/database.php';

// Get request URI and method
$requestUri = $_SERVER['REQUEST_URI'];
$requestMethod = $_SERVER['REQUEST_METHOD'];

// Remove query string and parse URI
$uri = parse_url($requestUri, PHP_URL_PATH);
$uri = trim($uri, '/');

// Remove 'api' prefix if present
$uri = preg_replace('#^api/#', '', $uri);

// Route the request
try {
    // Split URI into parts
    $parts = explode('/', $uri);
    $resource = $parts[0] ?? '';
    $id = $parts[1] ?? null;
    $action = $parts[2] ?? null;
    
    // Route to appropriate API file
    switch ($resource) {
        case 'tiles':
            require_once __DIR__ . '/api/tiles.php';
            break;
            
        case 'customers':
            require_once __DIR__ . '/api/customers.php';
            break;
            
        case 'invoices':
            require_once __DIR__ . '/api/invoices.php';
            break;
            
        case 'health':
        case '':
            sendJSON(['status' => 'ok', 'message' => 'The Tile Shop API is running']);
            break;
            
        default:
            sendError('Endpoint not found', 404);
    }
} catch (Exception $e) {
    error_log("API Error: " . $e->getMessage());
    sendError('Internal server error: ' . $e->getMessage(), 500);
}
?>
