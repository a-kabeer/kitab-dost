"""
Unit and Integration Tests for Phase 2: Student Website & Book Discovery
Tests homepage, book catalogue, multi-faceted filtering, search, and book detail pages.
"""

import os
import sys
import unittest

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from app import create_app
from app.database import get_db
from app.services import book_service

class Phase2StudentDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app('testing')
        cls.client = cls.app.test_client()

    def test_01_homepage_renders_and_contains_stats(self):
        """Test homepage renders with live stats, search bar, and featured books."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        # Check project branding
        self.assertIn('Kitaab Bank', html)
        self.assertIn('Pass Knowledge Forward', html)

        # Check search bar and action links
        self.assertIn('action="/catalogue"', html)
        self.assertIn('name="q"', html)
        self.assertIn('Explore All Books', html)
        self.assertIn('Donate an Unused Book', html)

        # Check live metrics
        self.assertIn('Total Books Donated', html)
        self.assertIn('Currently Available', html)
        self.assertIn('Successfully Reused', html)
        self.assertIn('Student Beneficiaries', html)

        # Check featured books section
        self.assertIn('Recently Added Educational Books', html)
        self.assertIn('KB-BK-', html)

    def test_02_catalogue_unfiltered_shows_all_books(self):
        """Test catalogue without filters returns all approved books."""
        response = self.client.get('/catalogue')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        self.assertIn('School Book Catalogue', html)
        self.assertIn('Showing <strong>16</strong> available books', html)

    def test_03_catalogue_filter_by_class(self):
        """Test filtering by class level."""
        for grade in ['Class 6', 'Class 7', 'Class 8']:
            response = self.client.get(f'/catalogue?class_grade={grade}')
            self.assertEqual(response.status_code, 200)
            html = response.get_data(as_text=True)
            self.assertIn(f'Active-Filter-Pill">{grade}'.lower(), html.lower())

        # Specifically test Class 6 count
        with self.app.app_context():
            books, count = book_service.get_available_books(class_grade='Class 6')
            self.assertEqual(count, 6)
            for b in books:
                self.assertEqual(b['class_grade'], 'Class 6')

    def test_04_catalogue_filter_by_subject(self):
        """Test filtering by subject."""
        with self.app.app_context():
            books, count = book_service.get_available_books(subject='Mathematics')
            self.assertGreater(count, 0)
            for b in books:
                self.assertEqual(b['subject'], 'Mathematics')

        response = self.client.get('/catalogue?subject=Mathematics')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('Mathematics', html)

    def test_05_catalogue_filter_by_language(self):
        """Test filtering by language (English, Urdu, Sindhi)."""
        languages = ['English', 'Urdu', 'Sindhi']
        for lang in languages:
            with self.app.app_context():
                books, count = book_service.get_available_books(language=lang)
                self.assertGreater(count, 0, f"Expected sample books in {lang}")
                for b in books:
                    self.assertEqual(b['language'], lang)

            response = self.client.get(f'/catalogue?language={lang}')
            self.assertEqual(response.status_code, 200)

    def test_06_catalogue_filter_by_condition(self):
        """Test filtering by condition (Like New, Good, Fair)."""
        for cond in ['Like New', 'Good', 'Fair']:
            with self.app.app_context():
                books, count = book_service.get_available_books(condition=cond)
                self.assertGreater(count, 0, f"Expected books with condition {cond}")
                for b in books:
                    self.assertEqual(b['condition_state'], cond)

    def test_07_catalogue_search_by_query(self):
        """Test keyword search across title, author, and book code."""
        # Search by english keyword
        response = self.client.get('/catalogue?q=General+Science')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('General Science', html)

        # Search by book code
        response = self.client.get('/catalogue?q=KB-BK-000002')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('KB-BK-000002', html)

        # Search by Urdu keyword
        response = self.client.get('/catalogue?q=اسلامیات')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('اسلامیات لازمی', html)

        # Search by Sindhi keyword
        response = self.client.get('/catalogue?q=سنڌي')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('سنڌي سليس', html)

    def test_08_empty_search_state(self):
        """Test empty search result shows the user-friendly empty state."""
        response = self.client.get('/catalogue?q=NonExistentQueryXYZ123')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        self.assertIn('No Books Found', html)
        self.assertIn('Clear All Filters', html)
        self.assertIn('Showing <strong>0</strong> available books', html)

    def test_09_book_detail_page_valid_code(self):
        """Test individual book detail page with full metadata and related books."""
        response = self.client.get('/book/KB-BK-000001')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        self.assertIn('Mathematics for Class 6', html)
        self.assertIn('Prof. Dr. M. A. Memon', html)
        self.assertIn('KB-BK-000001', html)
        self.assertIn('Sindh Textbook Board, Jamshoro', html)
        self.assertIn('Textbook Overview &amp; Curriculum Topics', html)
        self.assertIn('Other Available Books for Class 6', html)
        self.assertIn('Request This Book', html)

    def test_10_book_detail_page_multilingual(self):
        """Test individual book detail page for Urdu and Sindhi books."""
        # Urdu book
        res_urdu = self.client.get('/book/KB-BK-000003')
        self.assertEqual(res_urdu.status_code, 200)
        html_urdu = res_urdu.get_data(as_text=True)
        self.assertIn('اردو لازمی برائے جماعت ششم', html_urdu)

        # Sindhi book
        res_sindhi = self.client.get('/book/KB-BK-000004')
        self.assertEqual(res_sindhi.status_code, 200)
        html_sindhi = res_sindhi.get_data(as_text=True)
        self.assertIn('سنڌي سليس درجو ڇھون', html_sindhi)

    def test_11_book_detail_page_invalid_code_returns_404(self):
        """Test non-existent book code returns 404."""
        response = self.client.get('/book/KB-BK-999999')
        self.assertEqual(response.status_code, 404)

    def test_12_all_sample_cover_images_exist_locally(self):
        """Verify 100% of cover images referenced by books exist locally on disk (0 CDN)."""
        with self.app.app_context():
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT book_code, image_path FROM books;")
            rows = cur.fetchall()

            for code, img_path in rows:
                full_path = os.path.join(self.app.root_path, 'static', img_path)
                self.assertTrue(
                    os.path.isfile(full_path),
                    f"Cover image for {code} missing at {full_path}"
                )

if __name__ == '__main__':
    unittest.main()
