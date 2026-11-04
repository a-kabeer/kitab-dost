"""
Concurrency & Simultaneous Submissions Test Suite
Tests:
- 10 simultaneous threads writing to SQLite WAL database
- Verification that PRAGMA busy_timeout = 5000 and BEGIN IMMEDIATE prevent crashes
- Verification of total record integrity
"""

import sys
import threading
from app import create_app
from app.database import get_db, db_transaction

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def worker_submission(app, student_index, results):
    with app.app_context():
        try:
            with db_transaction() as db:
                cur = db.cursor()
                cur.execute(
                    "INSERT INTO activity_logs (action, entity_type, actor_type, actor_name, details) "
                    "VALUES ('STUDENT_SUBMIT', 'test', 'student', ?, ?);",
                    (f"Student_{student_index}", f"Simultaneous submission payload {student_index}")
                )
            results.append((student_index, True, None))
        except Exception as e:
            results.append((student_index, False, str(e)))

def test_simultaneous_submissions():
    print("=" * 64)
    print("TESTING SIMULTANEOUS STUDENT SUBMISSIONS OVER SQLITE WAL")
    print("=" * 64)
    app = create_app('development')

    threads = []
    results = []
    num_students = 15  # Simulating 15 students in a school lab submitting simultaneously

    for i in range(1, num_students + 1):
        t = threading.Thread(target=worker_submission, args=(app, i, results))
        threads.append(t)

    print(f"Launching {num_students} concurrent student submissions...")
    for t in threads:
        t.start()

    for t in threads:
        t.join()

    success_count = sum(1 for r in results if r[1])
    failure_count = sum(1 for r in results if not r[1])

    print(f"Results: {success_count} succeeded, {failure_count} failed")
    for r in results:
        status = "PASS" if r[1] else f"FAIL ({r[2]})"
        print(f"  Student {r[0]}: {status}")

    assert failure_count == 0, f"{failure_count} threads failed during concurrent submissions!"

    with app.app_context():
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) FROM activity_logs WHERE action = 'STUDENT_SUBMIT';")
        total_in_db = cur.fetchone()[0]
        print(f"Total verified concurrent records in database: {total_in_db}")
        assert total_in_db >= num_students

    print("\n" + "=" * 64)
    print("CONCURRENCY & SIMULTANEOUS SUBMISSION TEST PASSED!")
    print("=" * 64)

if __name__ == '__main__':
    test_simultaneous_submissions()
