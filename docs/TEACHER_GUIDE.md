# Kitaab Bank — Teacher & Administrator User Guide

> **کتاب بینک — اساتذہ اور ایڈمنسٹریٹر کے لیے رہنمائی**  
> *A Complete Operational Handbook for School Teachers and Library Managers*

---

## 1. Quick Start & Logging In

1. Open your web browser on any school computer or smartphone connected to the school Wi-Fi network.
2. Navigate to: `http://<School_Host_IP>:5000/auth/login` (or click **Teacher Sign In** on the public homepage).
3. Enter your assigned Teacher credentials:
   - **Default Username:** `teacher`
   - **Default Password:** `Teacher@123`
4. Click **Sign In**. You will arrive at the **Teacher Dashboard**.

> [!IMPORTANT]
> **Change Default Password:** Upon your first login, immediately go to **Settings > Account Security** (`/teacher/settings?tab=security`) and update your password.

---

## 2. Teacher Dashboard Overview

The Teacher Dashboard provides real-time circulation metrics derived directly from local database records:
- **Total Registered Books:** Breakdown of Available, Reserved, and Handed Over books.
- **Pending Review Badges:** Instant alerts for donations and student requests requiring teacher action.
- **Class 6, 7 & 8 Distribution:** Ratio of textbooks across core curriculum grades.
- **30-Day Circulation Velocity:** Number of handovers completed in the past 7 and 30 days.
- **Recent Activity Stream:** Chronological log of donations, requests, and handovers.

---

## 3. Reviewing Student Donations

When a student donates an old textbook through the public portal (`/donate`), it enters the **Donation Review Queue** with a status of `pending_review`.

### Step-by-Step Donation Review:
1. Navigate to **Donations Desk** (`/teacher/donations`).
2. Click **Review** on any pending donation item.
3. Review the student's name, roll number, textbook title, class grade, subject, and the condition photo uploaded by the student.
4. **Approve Donation:**
   - Verify the physical condition of the book (Good, Fair, or Poor).
   - Click **Approve Donation**.
   - The book is assigned a permanent Book Code (e.g., `KB-BK-000042`) and automatically listed as `available` in the public catalogue.
5. **Reject Donation:**
   - If the book is completely torn or missing critical chapters, provide a kind, constructive explanation (e.g., *"Pages 12 to 24 are torn. Please donate books with readable text"*).
   - Click **Reject Donation**. The student can view this feedback using their Tracking Code.

---

## 4. Processing Student Book Requests

When a student finds an available book in the catalogue and submits a request (`/catalogue`), it appears in the **Requests Desk** (`/teacher/requests`).

### Request Approval & Reservation Defense:
1. Open **Requests Desk**.
2. Compare pending requests for the same physical book.
3. Click **Approve Request** for the selected student.
4. **Automatic Circulation Defense:**
   - The selected book transitions immediately to `reserved`.
   - The requesting student's status changes to `approved` (Valid for 3 school days to collect).
   - **No Orphaned Requests:** All competing pending requests for that exact physical copy are automatically closed with a helpful notice: *"Another student's earlier request was approved for this copy. Please browse the catalogue for other available copies."*
   - Other students cannot submit new requests for this reserved book.

---

## 5. Physical Book Handover Workflow

When the student arrives at the teacher's desk or library counter to collect their reserved textbook:

### Step-by-Step Handover:
1. Go to **Handovers Desk** (`/teacher/handovers`).
2. Search by student name, roll number, or Book Code.
3. Click **Confirm Physical Handover**.
4. Check both verification boxes:
   - `[✓] I have verified the student's identity (Roll Number / Name).`
   - `[✓] The physical book has been handed over in acceptable condition.`
5. Optional: Enter teacher notes (e.g., *"Cover slightly creased, student notified"*).
6. Click **Confirm Handover & Issue Receipt**.
7. The system:
   - Assigns a permanent Handover Reference (e.g., `KB-HO-000015`).
   - Updates the book status to `handed_over`.
   - Locks the record permanently (immutable audit entry).
   - Generates an **A4 Printable Handover Receipt** with teacher and student signature lines.

---

## 6. QR Code Generation, Labels & Scanner

Every textbook in Kitaab Bank has a unique QR code linking directly to its digital history and status.

### Printing QR Stickers & Sheets:
1. Navigate to **Book Inventory** (`/teacher/inventory`).
2. **Individual Label:** Click **QR Label** next to any book for a print-ready 2" × 2" sticker.
3. **A4 Bulk Print Sheet:** Select multiple books or click **Print A4 QR Sheet (24 Labels)**. The browser print dialog formats 24 standardized stickers with cut-lines, book codes, grades, and titles.

### Using the QR Scanner:
- Access `/scan` on any smartphone or tablet camera.
- Point the camera at any textbook sticker:
  - If a **Book QR** is detected: Instantly opens the book's details page.
  - If a **Request Tracking QR** is detected: Automatically routes to the student's live tracking timeline.
- **Manual Code Entry:** If the camera is unavailable or lens is smudged, type the code (e.g., `KB-BK-000012` or `REQ-2026-00045`) into the fallback box.

---

## 7. Reports, Analytics & CSV Export

1. Go to **Reports & Analytics** (`/teacher/reports`).
2. View interactive breakdowns:
   - Books by Class Grade (Class 6, Class 7, Class 8)
   - Books by Subject (Mathematics, Science, English, Urdu, Sindhi, Social Studies, Islamiat, Computer)
   - Books by Language (Urdu, Sindhi, English)
   - Books by Physical Condition (Good, Fair, Poor)
3. **Export CSV:**
   - Click **Export Inventory CSV** or **Export Handovers CSV**.
   - All exported files include a **UTF-8 BOM**, ensuring Urdu and Sindhi student names and book titles open flawlessly in Microsoft Excel without garbled characters.
4. **Print A4 School Circulation Summary:**
   - Click **Print Summary** for an official school administration report.

---

## 8. Hot Backups & Exhibition Showcase Mode

### Creating Hot Backups:
- Go to **Settings > Database Backup & Restore** (`/teacher/settings?tab=backup`).
- Click **Create Live Backup Now**.
- Backups are captured without interrupting active students or teachers.
- Every backup has a cryptographic **SHA-256 Checksum** and SQLite **Integrity Status**.
- **Sole Backup Defense:** The system will refuse to delete your only verified backup.

### Exhibition Showcase Mode:
- For school exhibitions, science fairs, or department inspections, go to **Settings > Exhibition Showcase Mode** (`/teacher/settings?tab=demo`).
- Confirm the checkbox and click **Seed Exhibition Demo Data**.
- An automated safety backup of your real data (`*_pre_demo.db`) is captured immediately.
- 18 sample curriculum textbooks across Classes 6–8 are loaded with sample donations and handovers.
- A prominent orange banner displays across the app: `✨ Exhibition Demo Mode Active`.
- When the exhibition ends, click **Exit Demo & Restore Real Data** to instantly restore your school's actual database.
