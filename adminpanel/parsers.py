"""
File parsers and validators for Article documents (PDF, DOCX) and media images.
"""
import os
import re
from PIL import Image

MAX_DOCUMENT_SIZE = 15 * 1024 * 1024  # 15MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024     # 10MB

ALLOWED_DOC_EXTENSIONS = ('.pdf', '.docx')
ALLOWED_DOC_MIMES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'application/zip',
    'application/x-zip-compressed',
    'application/octet-stream',
}

ALLOWED_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')
ALLOWED_IMAGE_MIMES = {'image/jpeg', 'image/png', 'image/webp'}


def validate_document_file(uploaded_file):
    """
    Validate uploaded document (PDF or Word .docx).
    Returns (is_valid: bool, error_msg: str | None, doc_type: 'pdf' | 'docx' | None).
    """
    if not uploaded_file:
        return True, None, None

    if uploaded_file.size > MAX_DOCUMENT_SIZE:
        return False, 'Το μέγεθος του αρχείου υπερβαίνει το μέγιστο επιτρεπτό όριο των 15MB.', None

    filename = uploaded_file.name.lower()
    ext = os.path.splitext(filename)[1]

    if ext not in ALLOWED_DOC_EXTENSIONS:
        return False, 'Μη υποστηριζόμενος τύπος εγγράφου. Επιτρέπονται μόνο αρχεία PDF (.pdf) και Word (.docx).', None

    content_type = getattr(uploaded_file, 'content_type', '').lower()
    if content_type and content_type not in ALLOWED_DOC_MIMES:
        return False, f'Μη έγκυρος τύπος περιεχομένου MIME ({content_type}).', None

    doc_type = 'docx' if ext == '.docx' else 'pdf'
    return True, None, doc_type


def validate_image_file(uploaded_file):
    """
    Validate uploaded image (JPG, PNG, WebP) using extension, MIME, and Pillow verification.
    Returns (is_valid: bool, error_msg: str | None).
    """
    if not uploaded_file:
        return True, None

    if uploaded_file.size > MAX_IMAGE_SIZE:
        return False, 'Το μέγεθος της εικόνας υπερβαίνει το επιτρεπτό όριο των 10MB.'

    filename = uploaded_file.name.lower()
    ext = os.path.splitext(filename)[1]

    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False, 'Μη υποστηριζόμενος τύπος εικόνας. Επιτρέπονται αρχεία JPG, PNG και WebP.'

    content_type = getattr(uploaded_file, 'content_type', '').lower()
    if content_type and content_type not in ALLOWED_IMAGE_MIMES:
        return False, f'Μη έγκυρος τύπος εικόνας MIME ({content_type}).'

    # Deep verification with Pillow to catch corrupted or malicious payloads
    try:
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)
        img.verify()
        uploaded_file.seek(0)
    except Exception:
        return False, 'Το αρχείο εικόνας είναι κατεστραμμένο ή μη έγκυρο.'

    return True, None


def extract_docx_content(file_obj) -> str:
    """Extract HTML content from Word (.docx) file, omitting embedded images so only clean body text is extracted."""
    try:
        file_obj.seek(0)
        import mammoth
        # convert_image=lambda img: [] ignores inline document images to prevent duplicates with featured lead image
        res = mammoth.convert_to_html(file_obj, convert_image=lambda img: [])
        html = res.value.strip()
        if html:
            return html
    except Exception:
        pass

    try:
        file_obj.seek(0)
        import docx
        doc = docx.Document(file_obj)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        if paragraphs:
            return "".join(f"<p>{p}</p>" for p in paragraphs)
    except Exception:
        pass

    return ""


def _load_optional_module(module_name: str):
    """Safely load an optional module dynamically to satisfy IDE linters."""
    try:
        import importlib
        return importlib.import_module(module_name)
    except Exception:
        return None


def extract_pdf_content(file_obj) -> str:
    """Extract text from PDF file formatted into HTML paragraphs."""
    # 1. Try PyMuPDF (fitz)
    fitz_mod = _load_optional_module('fitz')
    if fitz_mod:
        try:
            file_obj.seek(0)
            data = file_obj.read()
            doc = fitz_mod.open(stream=data, filetype='pdf')
            pages = []
            for page in doc:
                txt = page.get_text().strip()
                if txt:
                    pages.append(txt)
            full_text = "\n\n".join(pages).strip()
            if full_text:
                paragraphs = [p.strip().replace("\n", " ") for p in full_text.split("\n\n") if p.strip()]
                file_obj.seek(0)
                return "".join(f"<p>{p}</p>" for p in paragraphs)
        except Exception:
            pass

    # 2. Try pdfplumber
    pdfplumber_mod = _load_optional_module('pdfplumber')
    if pdfplumber_mod:
        try:
            file_obj.seek(0)
            with pdfplumber_mod.open(file_obj) as pdf:
                pages = []
                for p in pdf.pages:
                    txt = p.extract_text()
                    if txt:
                        pages.append(txt)
                full_text = "\n\n".join(pages).strip()
                if full_text:
                    paragraphs = [p.strip().replace("\n", " ") for p in full_text.split("\n\n") if p.strip()]
                    file_obj.seek(0)
                    return "".join(f"<p>{p}</p>" for p in paragraphs)
        except Exception:
            pass

    # 3. Try pypdfium2
    pdfium_mod = _load_optional_module('pypdfium2')
    if pdfium_mod:
        try:
            file_obj.seek(0)
            pdf = pdfium_mod.PdfDocument(file_obj)
            pages = []
            for i in range(len(pdf)):
                page_txt = pdf[i].get_textpage().get_text_range()
                if page_txt:
                    pages.append(page_txt)
            full_text = "\n\n".join(pages).strip()
            if full_text:
                paragraphs = [p.strip().replace("\n", " ") for p in full_text.split("\n\n") if p.strip()]
                file_obj.seek(0)
                return "".join(f"<p>{p}</p>" for p in paragraphs)
        except Exception:
            pass

    file_obj.seek(0)
    return ""


def extract_document_content(file_obj) -> str:
    """
    Auto-detect document type from filename or header and extract formatted HTML.
    """
    if not file_obj:
        return ""

    filename = getattr(file_obj, 'name', '').lower()
    if filename.endswith('.docx'):
        content = extract_docx_content(file_obj)
    elif filename.endswith('.pdf'):
        content = extract_pdf_content(file_obj)
    else:
        # Try docx first, then pdf
        content = extract_docx_content(file_obj) or extract_pdf_content(file_obj)

    file_obj.seek(0)
    return content


def parse_docx_details(file_obj, filename: str = '') -> dict:
    """
    Extract title, excerpt, and clean HTML content from Word (.docx) file.
    """
    file_obj.seek(0)
    title = ''
    excerpt = ''
    first_p_idx = -1

    try:
        import docx
        doc = docx.Document(file_obj)

        # 1. Check core properties for a valid author-set title
        cp_title = getattr(getattr(doc, 'core_properties', None), 'title', '') or ''
        if cp_title and len(cp_title.strip()) > 3 and not cp_title.strip().lower().startswith(('microsoft word', 'document', 'untitled')):
            title = cp_title.strip()

        # 2. Check paragraph styles for 'Title' or 'Heading 1'
        if not title:
            for idx, p in enumerate(doc.paragraphs):
                style_name = (p.style.name if p.style else '').lower()
                text = p.text.strip()
                if text and ('title' in style_name or 'heading 1' in style_name):
                    title = text
                    first_p_idx = idx
                    break

        # 3. Fallback: First non-empty paragraph
        if not title:
            for idx, p in enumerate(doc.paragraphs):
                text = p.text.strip()
                if text:
                    title = text
                    first_p_idx = idx
                    break
        elif first_p_idx < 0:
            for idx, p in enumerate(doc.paragraphs):
                if p.text.strip() == title:
                    first_p_idx = idx
                    break

        # 4. Extract excerpt: next non-empty paragraph following the title
        if first_p_idx >= 0:
            for p in doc.paragraphs[first_p_idx + 1:]:
                text = p.text.strip()
                if text:
                    excerpt = text[:500]
                    break
    except Exception:
        pass

    # 5. Extract body content HTML
    content = extract_docx_content(file_obj)

    # 6. Fallback title from filename if empty
    if not title and filename:
        base = os.path.splitext(os.path.basename(filename))[0]
        title = base.replace('_', ' ').replace('-', ' ').strip()

    # 7. Strip duplicate leading title header from content if present
    if title and content:
        escaped_title = re.escape(title)
        stripped = re.sub(rf'^\s*<h[1-3][^>]*>\s*{escaped_title}\s*</h[1-3]>\s*', '', content, flags=re.IGNORECASE)
        if not stripped.strip():
            stripped = re.sub(rf'^\s*<p[^>]*>\s*<b>?\s*{escaped_title}\s*</b>?\s*</p>\s*', '', content, flags=re.IGNORECASE)
        if stripped.strip():
            content = stripped.strip()

    file_obj.seek(0)
    return {
        'title': title[:255],
        'excerpt': excerpt[:600],
        'content': content,
    }


def parse_pdf_details(file_obj, filename: str = '') -> dict:
    """
    Extract title, excerpt, and text content from PDF file.
    """
    file_obj.seek(0)
    title = ''
    excerpt = ''

    # 1. Try PyMuPDF (fitz)
    fitz_mod = _load_optional_module('fitz')
    if fitz_mod:
        try:
            file_obj.seek(0)
            data = file_obj.read()
            doc = fitz_mod.open(stream=data, filetype='pdf')
            meta = doc.metadata or {}
            meta_title = (meta.get('title') or '').strip()
            if meta_title and len(meta_title) > 3 and not meta_title.lower().startswith(('untitled', 'microsoft', 'word')):
                title = meta_title

            if len(doc) > 0:
                first_text = doc[0].get_text().strip()
                lines = [l.strip() for l in first_text.split('\n') if l.strip()]
                if not title and lines:
                    title = lines[0][:255]
                if len(lines) > 1:
                    excerpt = " ".join(lines[1:4])[:500]
        except Exception:
            pass

    # 2. Try pdfplumber
    if not title:
        pdfplumber_mod = _load_optional_module('pdfplumber')
        if pdfplumber_mod:
            try:
                file_obj.seek(0)
                with pdfplumber_mod.open(file_obj) as pdf:
                    meta = pdf.metadata or {}
                    meta_title = (meta.get('Title') or '').strip()
                    if meta_title and len(meta_title) > 3 and not meta_title.lower().startswith(('untitled', 'microsoft', 'word')):
                        title = meta_title

                    if len(pdf.pages) > 0:
                        first_text = pdf.pages[0].extract_text() or ''
                        lines = [l.strip() for l in first_text.split('\n') if l.strip()]
                        if not title and lines:
                            title = lines[0][:255]
                        if len(lines) > 1:
                            excerpt = " ".join(lines[1:4])[:500]
            except Exception:
                pass

    if not title and filename:
        base = os.path.splitext(os.path.basename(filename))[0]
        title = base.replace('_', ' ').replace('-', ' ').strip()

    content = extract_pdf_content(file_obj)
    file_obj.seek(0)
    return {
        'title': title[:255],
        'excerpt': excerpt[:600],
        'content': content,
    }


def parse_document_details(file_obj, filename: str = '') -> dict:
    """
    Extract title, excerpt, and full body content from a Word (.docx) or PDF document.
    """
    if not file_obj:
        return {'title': '', 'excerpt': '', 'content': ''}

    fname = (filename or getattr(file_obj, 'name', '')).lower()
    if fname.endswith('.docx'):
        details = parse_docx_details(file_obj, filename)
    elif fname.endswith('.pdf'):
        details = parse_pdf_details(file_obj, filename)
    else:
        try:
            details = parse_docx_details(file_obj, filename)
        except Exception:
            details = parse_pdf_details(file_obj, filename)

    file_obj.seek(0)
    return details


def extract_first_docx_image(file_obj) -> tuple | None:
    """
    Extract the first image embedded inside a Word (.docx) document.
    Returns (image_bytes: bytes, filename: str) or None if no images exist.
    """
    try:
        import zipfile
        file_obj.seek(0)
        with zipfile.ZipFile(file_obj, 'r') as z:
            media_files = [
                f for f in z.namelist()
                if f.startswith('word/media/') and os.path.splitext(f)[1].lower() in ('.jpg', '.jpeg', '.png', '.webp')
            ]
            media_files.sort()
            if media_files:
                img_data = z.read(media_files[0])
                ext = os.path.splitext(media_files[0])[1].lower()
                name = f"docx_lead{ext}"
                file_obj.seek(0)
                return img_data, name
    except Exception:
        pass
    file_obj.seek(0)
    return None



