# simple wrappers around pdfrw
import tempfile
from dataclasses import dataclass
from typing import IO, Any, Dict, List, Optional

from django.conf import settings
from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from common.analytics import statsd

from .pypdftk import PyPDFTK


@dataclass
class SignatureBoundingBox:
    x: int
    y: int
    width: int
    height: int


@dataclass
class PDFTemplateSection:
    path: str
    is_form: bool = False
    flatten_form: bool = True

    # page number -> signature location
    signature_locations: Optional[Dict[int, SignatureBoundingBox]] = None


class PDFTemplate:
    """
    Constructs a template out a set of input PDFs with fillable AcroForms.
    """

    def __init__(self, template_files: List[PDFTemplateSection]):
        self.template_files = template_files
        self.pypdftk = PyPDFTK()

    def fill(
        self, raw_data: Dict[str, Any], signature: Optional[Image.Image] = None
    ) -> IO:
        """
        Concatenates all the template_files in this PDFTemplate, and fills in
        the concatenated form with the given data.
        """

        # remove "None" values from data and map True -> "On"
        data = {}
        for k, v in raw_data.items():
            if v is None:
                continue

            if v == True:
                data[k] = "On"
                continue

            data[k] = v

        # Create the final output file and track all the temp files we'll have
        # to close at the end
        final_pdf = tempfile.NamedTemporaryFile("rb+", delete=not settings.PDF_DEBUG)
        handles_to_close: List[IO] = []

        try:
            # Fill in all of the forms
            filled_templates = []
            for template_file in self.template_files:
                signed_pdf_path = template_file.path
                if signature and template_file.signature_locations:
                    signature_stamp_file = self._make_signature_stamp(
                        signature, template_file.signature_locations, template_file.path
                    )
                    handles_to_close.append(signature_stamp_file)

                    signed_pdf_file = tempfile.NamedTemporaryFile(
                        "r", delete=not settings.PDF_DEBUG
                    )
                    handles_to_close.append(signed_pdf_file)

                    self.pypdftk.stamp(
                        template_file.path,
                        signature_stamp_file.name,
                        signed_pdf_file.name,
                    )

                    signed_pdf_path = signed_pdf_file.name

                if not template_file.is_form:
                    filled_templates.append(signed_pdf_path)
                    continue

                filled_template = tempfile.NamedTemporaryFile(
                    "r", delete=not settings.PDF_DEBUG
                )
                handles_to_close.append(filled_template)
                self.pypdftk.fill_form(
                    pdf_path=signed_pdf_path,
                    datas=data,
                    out_file=filled_template.name,
                    flatten=template_file.flatten_form,
                )

                filled_templates.append(filled_template.name)

            # Join the filled forms
            self.pypdftk.concat(files=filled_templates, out_file=final_pdf.name)

        except:
            statsd.increment("turnout.pdf.pdftk_exception")
            final_pdf.close()
            raise
        finally:
            for handle in handles_to_close:
                handle.close()

        return final_pdf

    def _make_signature_stamp(
        self,
        signature: Image.Image,
        signature_locations: Dict[int, SignatureBoundingBox],
        pdf_path: str,
    ) -> IO:
        stamp_file = tempfile.NamedTemporaryFile("r", delete=not settings.PDF_DEBUG)
        stampPDF = canvas.Canvas(stamp_file.name)

        # for each page of the PDF, we generate either a page with a signature,
        # or a blank page if there's no signature on that page
        for page_num in range(1, self.pypdftk.get_num_pages(pdf_path) + 1):
            if page_num in signature_locations:
                loc = signature_locations[page_num]

                stampPDF.drawImage(
                    ImageReader(signature),
                    loc.x,
                    loc.y,
                    loc.width,
                    loc.height,
                    preserveAspectRatio=True,
                )

            stampPDF.showPage()

        stampPDF.save()

        return stamp_file
