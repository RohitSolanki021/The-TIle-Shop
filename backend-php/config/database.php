<?php
/**
 * Database Configuration
 * Update these values with your shared hosting MySQL credentials
 */

// Database credentials
define('DB_HOST', 'localhost');          // Usually 'localhost' on shared hosting
define('DB_NAME', 'tileshop');          // Your database name
define('DB_USER', 'root');               // Your MySQL username
define('DB_PASS', '');                   // Your MySQL password
define('DB_CHARSET', 'utf8mb4');

// Application settings
define('APP_URL', 'http://localhost');   // Your domain URL
define('CORS_ORIGIN', '*');              // Frontend URL or * for all

// File upload settings
define('UPLOAD_DIR', __DIR__ . '/../uploads/');
define('MAX_UPLOAD_SIZE', 5 * 1024 * 1024); // 5MB

// PDF storage
define('PDF_DIR', __DIR__ . '/../pdfs/');

// Error reporting (set to 0 in production)
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Timezone
date_default_timezone_set('Asia/Kolkata');

// Database connection
class Database {
    private static $instance = null;
    private $conn;
    
    private function __construct() {
        try {
            $dsn = "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=" . DB_CHARSET;
            $options = [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES => false,
            ];
            
            $this->conn = new PDO($dsn, DB_USER, DB_PASS, $options);
        } catch(PDOException $e) {
            error_log("Database Connection Error: " . $e->getMessage());
            http_response_code(500);
            echo json_encode(['error' => 'Database connection failed']);
            exit;
        }
    }
    
    public static function getInstance() {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    public function getConnection() {
        return $this->conn;
    }
}

// Helper functions
function sendJSON($data, $statusCode = 200) {
    http_response_code($statusCode);
    header('Content-Type: application/json');
    echo json_encode($data);
    exit;
}

function sendError($message, $statusCode = 400) {
    sendJSON(['error' => $message], $statusCode);
}

function getRequestData() {
    $data = json_decode(file_get_contents('php://input'), true);
    return $data ?: [];
}

function generateUUID() {
    return sprintf('%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
        mt_rand(0, 0xffff), mt_rand(0, 0xffff),
        mt_rand(0, 0xffff),
        mt_rand(0, 0x0fff) | 0x4000,
        mt_rand(0, 0x3fff) | 0x8000,
        mt_rand(0, 0xffff), mt_rand(0, 0xffff), mt_rand(0, 0xffff)
    );
}

// Create necessary directories
if (!file_exists(UPLOAD_DIR)) {
    mkdir(UPLOAD_DIR, 0755, true);
}
if (!file_exists(PDF_DIR)) {
    mkdir(PDF_DIR, 0755, true);
}
?>
