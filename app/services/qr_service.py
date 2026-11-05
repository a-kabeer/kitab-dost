"""
QR Code Service: Generation, Label Layouts, and Code Parsing for Physical Circulation
100% Local & Offline (Zero external CDN / cloud calls)
"""

import io
import re
import base64
import os
import qrcode
from qrcode.image.pil import PilImage
from PIL import Image

def generate_qr_image(content: str, box_size: int = 8, border: int = 2) -> Image.Image:
    """Generate a PIL Image of a QR code from text content."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(content)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

def generate_qr_png_bytes(content: str, box_size: int = 8, border: int = 2) -> bytes:
    """Generate raw PNG bytes of a QR code."""
    img = generate_qr_image(content, box_size, border)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

def generate_qr_data_uri(content: str, box_size: int = 8, border: int = 2) -> str:
    """Generate a base64 data URI (data:image/png;base64,...) for embedding in HTML/printouts."""
    png_bytes = generate_qr_png_bytes(content, box_size, border)
    encoded = base64.b64encode(png_bytes).decode('ascii')
    return f"data:image/png;base64,{encoded}"

def get_book_qr_payload(book_code: str, base_url: str = None) -> str:
    """
    Format standard payload for a book's QR code.
    If base_url is provided, builds full absolute URL; otherwise relative URL /book/<book_code>.
    """
    clean_code = str(book_code).strip().upper()
    if base_url:
        return f"{base_url.rstrip('/')}/book/{clean_code}"
    return f"/book/{clean_code}"

def parse_scanned_book_code(raw_input: str) -> dict:
    """
    Parses and normalizes input from manual text entry or QR camera decoding.
    Handles full URLs, relative paths, standard codes, or numeric shortcuts.
    
    Returns a dict:
    {
        'type': 'book' | 'request' | 'donation' | 'unknown',
        'code': normalized_code,
        'original': raw_input
    }
    """
    if not raw_input:
        return {'type': 'unknown', 'code': '', 'original': ''}
    
    text = str(raw_input).strip()
    
    # 1. Check for Book URL match (e.g. http://.../book/KB-BK-000001 or /book/KB-BK-000001)
    book_url_match = re.search(r'/book/([A-Za-z0-9_-]+)', text, re.IGNORECASE)
    if book_url_match:
        text = book_url_match.group(1)
    
    # 2. Check for Track URL match (e.g. /track?code=KB-REQ-...)
    track_url_match = re.search(r'/track\?code=([A-Za-z0-9_-]+)', text, re.IGNORECASE)
    if track_url_match:
        return {'type': 'request', 'code': track_url_match.group(1).upper(), 'original': raw_input}

    clean = text.strip().upper()

    # 3. Check for Request tracking token (KB-REQ-XXXX-XXXX)
    if clean.startswith('KB-REQ-') or re.match(r'^[A-Z0-9]{4}-[A-Z0-9]{4}$', clean):
        full_req = clean if clean.startswith('KB-REQ-') else f"KB-REQ-{clean}"
        return {'type': 'request', 'code': full_req, 'original': raw_input}

    # 4. Check for Donation reference (KB-DON-XXXX-XXXX)
    if clean.startswith('KB-DON-'):
        return {'type': 'donation', 'code': clean, 'original': raw_input}

    # 5. Standard Book code: KB-BK-000001 or BK-000001 or BK-1
    match_std = re.match(r'^(?:KB-)?BK-(\d{1,6})$', clean)
    if match_std:
        num = int(match_std.group(1))
        return {'type': 'book', 'code': f"KB-BK-{num:06d}", 'original': raw_input}

    # 6. Pure digits: e.g. "1" or "000001" or "35"
    if clean.isdigit():
        num = int(clean)
        return {'type': 'book', 'code': f"KB-BK-{num:06d}", 'original': raw_input}

    # Default fallback: Treat as book search query / identifier
    return {'type': 'book', 'code': clean, 'original': raw_input}
