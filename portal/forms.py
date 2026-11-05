"""
Forms for public portal interactions.

NOTE: WriterApplicationForm and WriterArticleSubmitForm have been removed as
part of SEC-01/SEC-04 — the site now operates exclusively under a single
Super Admin. All article creation goes through /adminpanel/.
"""
from adminpanel.models import Article, Category
from adminpanel.parsers import (
    validate_document_file,
    validate_image_file,
    extract_document_content,
)
