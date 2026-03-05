<?php
/**
 * The Tile Shop - API Router
 * Main entry point for all API requests
 */

// Error logging
error_reporting(E_ALL);
ini_set('display_errors', 1);
ini_set('log_errors', 1);

// Enable CORS
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With');
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

// Parse URI
$uri = parse_url($requestUri, PHP_URL_PATH);
$uri = trim($uri, '/');

// REMOVE base folder if present (fix for subfolder install like /backend-php/)
$scriptName = str_replace('/index.php', '', $_SERVER['SCRIPT_NAME']);
$basePath = trim(dirname($scriptName), '/');

if ($basePath && strpos($uri, $basePath) === 0) {
    $uri = substr($uri, strlen($basePath));
    $uri = trim($uri, '/');
}

// Extra fallback (Hostinger subfolder case)
if (strpos($uri, 'backend-php/') === 0) {
    $uri = substr($uri, strlen('backend-php/'));
}
if ($uri === 'backend-php') {
    $uri = '';
}

// Remove 'api' prefix if present
$uri = preg_replace('#^api/?#', '', $uri);

// Route the request
try {

    $parts = explode('/', $uri);
    $resource = $parts[0] ?? '';
    $id = isset($parts[1]) ? urldecode($parts[1]) : null;
    $action = $parts[2] ?? null;

    $GLOBALS['requestMethod'] = $requestMethod;
    $GLOBALS['id'] = $id;
    $GLOBALS['action'] = $action;

    switch ($resource) {

        case 'tiles':
            require_once __DIR__ . '/api/tiles.php';
            break;

        case 'customers':
            require_once __DIR__ . '/api/customers.php';
            break;

        case 'invoices':
        case 'public':
            if ($resource === 'public' && $parts[1] === 'invoices') {
                $id = isset($parts[2]) ? urldecode($parts[2]) : null;
                $action = $parts[3] ?? null;
                $GLOBALS['id'] = $id;
                $GLOBALS['action'] = $action;
            }
            require_once __DIR__ . '/api/invoices.php';
            break;

        case 'health':
        case '':
            sendJSON([
                'status' => 'ok',
                'message' => 'The Tile Shop API is running',
                'timestamp' => date('Y-m-d H:i:s')
            ]);
            break;

        default:
            sendError('Endpoint not found: ' . $resource, 404);
    }

} catch (Exception $e) {
    sendError('Internal server error: ' . $e->getMessage(), 500);
}
?>