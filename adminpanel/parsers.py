"""
File parsers and validators for Article documents (PDF, DOCX) and media images.
"""
import os
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


def extract_pdf_content(file_obj) -> str:
    """Extract text from PDF file formatted into HTML paragraphs."""
    try:
        file_obj.seek(0)
        import pdfplumber
        with pdfplumber.open(file_obj) as pdf:
            pages = []
            for p in pdf.pages:
                txt = p.extract_text()
                if txt:
                    pages.append(txt)
            full_text = "\n\n".join(pages).strip()
            if full_text:
                paragraphs = [p.strip().replace("\n", " ") for p in full_text.split("\n\n") if p.strip()]
                return "".join(f"<p>{p}</p>" for p in paragraphs)
    except Exception:
        pass

    try:
        file_obj.seek(0)
        import pypdfium2
        pdf = pypdfium2.PdfDocument(file_obj)
        pages = []
        for i in range(len(pdf)):
            page_txt = pdf[i].get_textpage().get_text_range()
            if page_txt:
                pages.append(page_txt)
        full_text = "\n\n".join(pages).strip()
        if full_text:
            paragraphs = [p.strip().replace("\n", " ") for p in full_text.split("\n\n") if p.strip()]
            return "".join(f"<p>{p}</p>" for p in paragraphs)
    except Exception:
        pass

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

