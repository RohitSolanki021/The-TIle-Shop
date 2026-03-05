<?php
/**
 * Database Configuration (Hostinger / Shared Hosting)
 */

// ✅ 1) PUT YOUR REAL HOSTINGER DB DETAILS HERE (from hPanel -> Databases -> MySQL Databases)
define('DB_HOST', 'localhost');                 // usually localhost on Hostinger
define('DB_NAME', 'u289643234_tileshop');              // e.g. u289643234_tileshop
define('DB_USER', 'u289643234_tileshop');              // e.g. u289643234_user
define('DB_PASS', 'Liftup@12');          // MUST NOT be empty on Hostinger
define('DB_CHARSET', 'utf8mb4');

// ✅ 2) Set your live domain here
define('APP_URL', 'https://tileshop.family-tree.in');
define('CORS_ORIGIN', '*');

// File upload settings
define('UPLOAD_DIR', __DIR__ . '/../uploads/');
define('MAX_UPLOAD_SIZE', 5 * 1024 * 1024); // 5MB

// PDF storage
define('PDF_DIR', __DIR__ . '/../pdfs/');

// ✅ In production keep display_errors OFF (but log errors ON)
error_reporting(E_ALL);
ini_set('display_errors', 0);
ini_set('log_errors', 1);

// Timezone
date_default_timezone_set('Asia/Kolkata');

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
                PDO::ATTR_TIMEOUT => 10,
            ];

            $this->conn = new PDO($dsn, DB_USER, DB_PASS, $options);

            // ✅ quick sanity check
            $this->conn->query("SELECT 1");

        } catch (PDOException $e) {
            error_log("Database Connection Error: " . $e->getMessage());
            http_response_code(500);
            header('Content-Type: application/json');
            echo json_encode([
                'error' => 'Database connection failed',
                'hint'  => 'Check DB_HOST/DB_NAME/DB_USER/DB_PASS in config/database.php (Hostinger does not use root).'
            ]);
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
    $raw = file_get_contents('php://input');
    $data = json_decode($raw, true);
    return is_array($data) ? $data : [];
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