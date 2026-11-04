# Product Requirements Document (PRD)
## Project: Kitaab Bank – Smart School Book Exchange (کتاب بینک)

---

## 1. Document Control & Metadata
- **Project Name:** Kitaab Bank – Smart School Book Exchange
- **Version:** 1.0.0 (Phase 0 Baseline)
- **Status:** Approved / Planning Phase
- **Target Audience:** School Students (Grades 6–8), Teachers, School Librarians, Exhibition Evaluators
- **Operating Environment:** Local School Server (Windows PC / Laptop) running offline on Local Wi-Fi Network with optional secure ngrok tunnel.

---

## 2. Executive Summary & Vision

### 2.1 The Problem
At the conclusion of each academic session, thousands of school students hold educational textbooks, guides, and reference material that they no longer require. Simultaneously, incoming students—many from families facing financial constraints—struggle with the rising cost of new textbooks. Traditional school book drives are manual, unorganized, paper-heavy, and lack real-time visibility into what is available, leading to wasted educational resources and unnecessary expenses.

### 2.2 The Solution
**Kitaab Bank** is a streamlined, lightweight, offline-first web application designed specifically for school environments. It empowers students to donate their surplus textbooks, lets fellow students discover and request needed books, and provides teachers with a clean administrative desk to supervise quality, approve donations, manage reservations, generate printable QR stickers, and record verified physical handovers.

### 2.3 Core Value Proposition
- **Financial Relief:** Eliminates textbook purchasing costs for vulnerable families.
- **Eco-Friendly Sustainability:** Promotes the circular economy and book reuse.
- **100% Offline Capability:** Works reliably in schools without internet access over local Wi-Fi.
- **Zero Friction for Children:** No student passwords, emails, or accounts needed.
- **Strict Quality Control:** Every donation and request is supervised and verified by teachers.

---

## 3. Target User Personas

### 3.1 Student Donor (e.g., Zeeshan, Class 8)
- **Needs:** Easily list last year's Class 7 Science and Math books without hassle.
- **Behavior:** Uses a school computer or parent's mobile phone on school Wi-Fi. Does not have a personal email.
- **Expectation:** Simple form, fast picture upload of the book condition, instant donation confirmation with a reference number.

### 3.2 Student Requester (e.g., Fatima, Class 6)
- **Needs:** Find a clean English Grammar and Social Studies book for Class 6.
- **Behavior:** Browses the catalogue, filters by Class and Subject, requests the book using her Roll Number and Class.
- **Expectation:** Clean book photos, clear condition status (e.g., Good, Fair), and a private Tracking Code to see when her request is approved for pickup.

### 3.3 Teacher / School Administrator (e.g., Sir Tariq, School Coordinator)
- **Needs:** Verify incoming donations, reject torn/outdated syllabus books, approve requests on a first-come first-served or merit basis, print QR labels for physical tagging, and log handovers.
- **Expectation:** Secure password-protected dashboard, simple one-click actions, real-time statistics for school leadership, exportable reports.

### 3.4 Exhibition Evaluator / Guest
- **Needs:** Review the system during a STREAM / Science exhibition.
- **Expectation:** Fast, responsive UI, engaging Light/Dark themes, bilingual interface (English / Urdu / Sindhi), interactive QR scanning demo.

---

## 4. Scope & Feature Requirements

### 4.1 Student Portal (Public & Frictionless)
| ID | Feature | Description | Priority |
|---|---|---|---|
| **STU-01** | **Homepage & Discovery** | Welcoming landing page showing mission, live reuse counters, search bar, and featured recently added books. | P0 (Must Have) |
| **STU-02** | **Book Catalogue** | Public searchable catalogue showing only teacher-approved books. Grid view with book covers, class tag, subject tag, condition badge, and availability status. | P0 (Must Have) |
| **STU-03** | **Filtering & Search** | Multi-faceted filtering: Class (6, 7, 8), Subject (Math, Science, English, Urdu, Islamiat, Social Studies, Computer), Language (Urdu, English, Sindhi), and Book Condition. | P0 (Must Have) |
| **STU-04** | **Book Details Page** | High-resolution local image view, book metadata, syllabus edition, condition remarks, and "Request This Book" call to action. | P0 (Must Have) |
| **STU-05** | **Book Donation Workflow** | Simple submission form: Book Title, Class, Subject, Condition (Like New, Good, Fair), Donor Name, Class & Roll No., and optional book cover photo. Generates a Donation Reference (`KB-DON-XXXX`). | P0 (Must Have) |
| **STU-06** | **Book Request Workflow** | One-click request form for available books. Student enters Name, Class, Roll No., Parent Phone/Contact, and optional note. Generates a private Tracking Code (`KB-REQ-XXXX`). | P0 (Must Have) |
| **STU-07** | **Request Tracking** | Dedicated lookup page where students enter their Tracking Code to view live status (`Submitted` $\rightarrow$ `Under Review` $\rightarrow$ `Ready for Pickup` $\rightarrow$ `Handed Over`). | P0 (Must Have) |
| **STU-08** | **QR Scanner & Direct Code Entry** | Built-in offline camera scanner allowing a student to scan a physical book's QR code to view its details, or enter the 6-character Book Code manually. | P1 (High) |
| **STU-09** | **Theme Switcher** | Light Mode, Dark Mode, and System Default toggle accessible from the top navbar, persisting in local storage with zero screen flash. | P0 (Must Have) |
| **STU-10** | **Multilingual Support** | Instant UI language toggling between English, Urdu (اردو), and Sindhi (سنڌي) with proper RTL layout switching. | P1 (High) |

### 4.2 Teacher Administrative Portal (Protected)
| ID | Feature | Description | Priority |
|---|---|---|---|
| **TEA-01** | **Authentication** | Secure password-protected login with session protection, logout, and automatic idle timeout. | P0 (Must Have) |
| **TEA-02** | **Executive Dashboard** | Real-time metric cards: Total Donated, Currently Available, Reserved / Pending Pickup, Successfully Reused Books, and Pending Action alerts. | P0 (Must Have) |
| **TEA-03** | **Donation Review Queue** | List of pending donations. Teacher can inspect submitted book data/photo, approve to catalogue, or reject with reason. | P0 (Must Have) |
| **TEA-04** | **Inventory Management** | Full CRUD for books. Teachers can directly add school-purchased books, edit details, retire worn-out books, or mark lost items. | P0 (Must Have) |
| **TEA-05** | **Request Approval Desk** | Review incoming student requests. Approving a request automatically reserves the book (preventing duplicate claims) and flags it as `Ready for Pickup`. | P0 (Must Have) |
| **TEA-06** | **Handover Verification** | Physical collection confirmation. Teacher verifies the student's Roll No./ID, inputs any remarks, and marks the book as `Handed Over` (incrementing reuse count). | P0 (Must Have) |
| **TEA-07** | **QR Label Generator & Printing** | Generates printable adhesive sticker sheets or single labels featuring Book Code, Title, Class, and QR Code pointing to local book URL. | P0 (Must Have) |
| **TEA-08** | **Reports & Analytics** | Detailed breakdown: Most requested subjects, class-wise distribution, monthly reuse trends, and downloadable CSV/Printable summaries. | P1 (High) |
| **TEA-09** | **System Settings & Backup** | School details customization, one-click SQLite database backup creation, and pre-packaged Demo Data Seeder for exhibitions. | P1 (High) |

---

## 5. Non-Functional Requirements (NFRs)

### 5.1 Offline Autonomy & Zero Cloud Dependency
- The application **must not** make external network calls to CDNs (e.g. Google Fonts, unpkg, cdnjs, Bootstrap CDN, Tailwind CDN).
- All CSS, JavaScript, and Font assets must reside locally in `/static/`.
- System fonts (system-ui, Segoe UI, Roboto, Noto Nastaliq Urdu) will be prioritized to ensure crisp rendering without external downloads.

### 5.2 Concurrency & Network Topology
- The server will run on a standard Windows host via **Waitress WSGI** on port `5000` bound to `0.0.0.0`.
- Mobile devices and workstations connected to the same school Wi-Fi router must access the system via `http://<HOST_IP>:5000`.
- SQLite must operate in **WAL (Write-Ahead Logging)** mode with busy timeouts configured to seamlessly handle simultaneous requests from 20+ devices.

### 5.3 Student Privacy & Security
- Public views must never reveal sensitive student information (donor's or requester's phone numbers or roll numbers).
- Only book metadata and anonymized availability statuses are publicly viewable.
- Teacher routes must be strictly guarded behind authentication middlewares.

### 5.4 Performance & Resilience
- Page load time on local network < 200ms.
- Persistent storage: Server restarts or power interruptions must not corrupt SQLite or lose uploaded book pictures.
- Graceful degradation if camera permission is denied on mobile devices (fallback to manual Book Code input).

---

## 6. Anti-Goals & Explicit Exclusions (What We Will NOT Build)
1. **No Online Payment Gateways:** This is a 100% free school book sharing platform; no monetary transactions exist.
2. **No Student Login / Account Creation:** Eliminates forgotten passwords, fake account spam, and COPPA/privacy friction for middle school children.
3. **No Heavy Cloud Services:** No Firebase, AWS S3, or Supabase. Everything is stored on the local PC disk.
4. **No Premature Microservices:** A single, clean, robust Python Flask monolith with modular blueprints is far more reliable and easier to demonstrate.
