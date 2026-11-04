-- Kitaab Bank - Database Schema DDL
-- Local SQLite 3 with Write-Ahead Logging (WAL)

PRAGMA foreign_keys = ON;

-- 1. Teachers / Staff Table
CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT,
    role TEXT NOT NULL DEFAULT 'teacher', -- 'admin', 'teacher'
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_teachers_username ON teachers(username);

-- 2. Books Table (Standardized 6-digit code: KB-BK-000001)
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    author TEXT,
    subject TEXT NOT NULL, -- 'Mathematics', 'Science', 'English', 'Urdu', etc.
    class_grade TEXT NOT NULL, -- 'Class 6', 'Class 7', 'Class 8'
    language TEXT NOT NULL DEFAULT 'Urdu', -- 'Urdu', 'English', 'Sindhi'
    publisher TEXT,
    edition_year INTEGER,
    condition_state TEXT NOT NULL DEFAULT 'Good', -- 'Like New', 'Good', 'Fair'
    description TEXT,
    image_path TEXT,
    qr_code_path TEXT,
    status TEXT NOT NULL DEFAULT 'available', -- 'available', 'reserved', 'handed_over', 'retired'
    is_approved INTEGER NOT NULL DEFAULT 1,
    donation_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (donation_id) REFERENCES donations(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_books_status_grade ON books(status, class_grade);
CREATE INDEX IF NOT EXISTS idx_books_code ON books(book_code);
CREATE INDEX IF NOT EXISTS idx_books_subject ON books(subject);

-- 3. Donations Table
CREATE TABLE IF NOT EXISTS donations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donation_code TEXT UNIQUE NOT NULL, -- Format: KB-DON-XXXX-XXXX
    title TEXT NOT NULL,
    author TEXT,
    subject TEXT NOT NULL,
    class_grade TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'Urdu',
    condition_state TEXT NOT NULL DEFAULT 'Good',
    description TEXT,
    temp_image_path TEXT,
    donor_name TEXT NOT NULL,
    donor_class TEXT NOT NULL,
    donor_roll_no TEXT NOT NULL,
    donor_contact TEXT,
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    rejection_reason TEXT,
    reviewed_by INTEGER,
    reviewed_at TIMESTAMP,
    book_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reviewed_by) REFERENCES teachers(id) ON DELETE SET NULL,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_donations_status ON donations(status);
CREATE INDEX IF NOT EXISTS idx_donations_code ON donations(donation_code);

-- 4. Requests Table
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tracking_code TEXT UNIQUE NOT NULL, -- Format: KB-REQ-XXXX-XXXX
    book_id INTEGER NOT NULL,
    requester_name TEXT NOT NULL,
    requester_class TEXT NOT NULL,
    requester_roll_no TEXT NOT NULL,
    requester_contact TEXT NOT NULL,
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'completed', 'cancelled'
    rejection_reason TEXT,
    reviewed_by INTEGER,
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE RESTRICT,
    FOREIGN KEY (reviewed_by) REFERENCES teachers(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_requests_tracking ON requests(tracking_code);
CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_book ON requests(book_id);

-- 5. Physical Handovers Table
CREATE TABLE IF NOT EXISTS handovers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL UNIQUE, -- Crucial: Prevents double-handover of same request
    book_id INTEGER NOT NULL,
    recipient_name TEXT NOT NULL,
    recipient_class TEXT NOT NULL,
    recipient_roll_no TEXT NOT NULL,
    handed_over_by INTEGER NOT NULL,
    handover_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    remarks TEXT,
    FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE RESTRICT,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE RESTRICT,
    FOREIGN KEY (handed_over_by) REFERENCES teachers(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_handovers_date ON handovers(handover_date);
CREATE INDEX IF NOT EXISTS idx_handovers_book ON handovers(book_id);

-- 6. Activity Logs Table
CREATE TABLE IF NOT EXISTS activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER,
    actor_type TEXT NOT NULL DEFAULT 'system',
    actor_name TEXT,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_activity_created ON activity_logs(created_at);

-- 7. System Settings Table
CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Backup Records Table
CREATE TABLE IF NOT EXISTS backup_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL UNIQUE,
    file_size_bytes INTEGER NOT NULL,
    checksum_sha256 TEXT NOT NULL,
    verification_status TEXT NOT NULL DEFAULT 'VALID',
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES teachers(id) ON DELETE SET NULL
);

-- Default Seed System Settings
INSERT OR IGNORE INTO system_settings (key, value, description) VALUES
    ('school_name', 'Government Model High School', 'Official school name displayed on headers and labels'),
    ('academic_year', '2026-2027', 'Current active academic session'),
    ('default_language', 'en', 'Default system language (en, ur, sd)'),
    ('catalogue_public_view', '1', 'Public catalogue accessibility toggle');
