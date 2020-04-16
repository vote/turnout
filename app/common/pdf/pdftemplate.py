# simple wrappers around pdfrw
import tempfile
from dataclasses import dataclass
from typing import IO, Any, Dict, List

from common.analytics import statsd

from .pypdftk import PyPDFTK


@dataclass
class PDFTemplateSection:
    path: str
    is_form: bool = False
    flatten_form: bool = True


class PDFTemplate:
    """
    Constructs a template out a set of input PDFs with fillable AcroForms.
    """

    def __init__(self, template_files: List[PDFTemplateSection]):
        self.template_files = template_files

    def fill(self, raw_data: Dict[str, Any]) -> IO:
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
        final_pdf = tempfile.NamedTemporaryFile("rb+")
        handles_to_close: List[IO] = []
        pypdftk = PyPDFTK()

        try:
            # Fill in all of the forms
            filled_templates = []
            for template_file in self.template_files:
                if not template_file.is_form:
                    filled_templates.append(template_file.path)
                    continue

                filled_template = tempfile.NamedTemporaryFile("r")
                handles_to_close.append(filled_template)
                pypdftk.fill_form(
                    pdf_path=template_file.path,
                    datas=data,
                    out_file=filled_template.name,
                    flatten=template_file.flatten_form,
                )

                filled_templates.append(filled_template.name)

            # Join the filled forms
            pypdftk.concat(files=filled_templates, out_file=final_pdf.name)

        except:
            statsd.increment("turnout.pdf.pdftk_exception")
            final_pdf.close()
            raise
        finally:
            for handle in handles_to_close:
                handle.close()

        return final_pdf
