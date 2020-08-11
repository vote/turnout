import base64
import dataclasses
import numbers
import unicodedata
from typing import Any, Dict, List

from pdf_template import PDFTemplate, PDFTemplateSection

from common.apm import tracer

MAX_FIELD_LEN = 1024

# These characters are in the unicode category Cc (control characters) which we
# mostly want to exclude (because it includes things like null bytes) but
# we don't want to remove newlines. List from: https://stackoverflow.com/a/14245311
WHITESPACE = {"\t", "\n", "\v", "\r", "\f"}


def chr_is_valid(c: str) -> bool:
    if c in WHITESPACE:
        return True

    return unicodedata.category(c) not in ["Cc", "Cn"]


def clean_data_str(field: str) -> str:
    if len(field) > MAX_FIELD_LEN:
        field = field[:MAX_FIELD_LEN]

    # Filter out control characters like null bytes
    return "".join(c for c in field if chr_is_valid(c))


def clean_data_field(field: Any) -> Any:
    if field is None:
        return None

    if isinstance(field, numbers.Number):
        return field

    if isinstance(field, bool):
        return field

    if isinstance(field, bytes):
        return clean_data_str(field.decode())

    if isinstance(field, str):
        return clean_data_str(field)

    return clean_data_str(str(field))


def clean_data(in_data: Dict[str, Any]) -> Dict[str, Any]:
    return {k: clean_data_field(v) for k, v in in_data.items()}


BASE64_PDF_CACHE: Dict[str, str] = {}


def get_base64_pdf(path: str) -> str:
    if BASE64_PDF_CACHE.get(path):
        return BASE64_PDF_CACHE[path]

    with open(path, "rb") as f:
        pdf = base64.b64encode(f.read()).decode()
        BASE64_PDF_CACHE[path] = pdf

        return pdf


def serialize_template_section(section: PDFTemplateSection) -> Dict[str, Any]:
    serialized = dataclasses.asdict(section)
    serialized["pdf"] = get_base64_pdf(serialized.pop("path"))

    return serialized


@tracer.wrap()
def serialize_template(template: PDFTemplate) -> List[Dict[str, Any]]:
    return [serialize_template_section(section) for section in template.template_files]
