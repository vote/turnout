# simple wrappers around pdfrw
from pdfrw import PdfDict, PdfName, PdfObject, PdfReader, PdfWriter

ANNOT_KEY = "/Annots"
ANNOT_FIELD_KEY = "/T"
ANNOT_VAL_KEY = "/V"
ANNOT_RECT_KEY = "/Rect"
SUBTYPE_KEY = "/Subtype"
WIDGET_SUBTYPE_KEY = "/Widget"


def fill_form(input_file, output_file, data):
    """input_file can be file object or path name
    output_file can be file object or path name
    data is dictionary with keys corresponding to the form fields"""

    the_pdf = PdfReader(input_file)
    for page in the_pdf.pages:
        annotations = page[ANNOT_KEY]
        for annotation in annotations:
            if annotation[SUBTYPE_KEY] == WIDGET_SUBTYPE_KEY:
                key = annotation[ANNOT_FIELD_KEY][1:-1]
                if key in data.keys():
                    val = data[key]
                    if val == None:
                        # skip nulls
                        continue
                    if val == True:
                        # treat booleans as checkboxes
                        annotation.update(PdfDict(V=PdfName("On")))
                    else:
                        # set annotation value
                        annotation.update(PdfDict(V="{}".format(val)))
                        # and empty appearance to make field visible in Apple Preview
                        annotation.update(PdfDict(AP=""))
                    # mark the fields as un-editable
                    annotation.update(PdfDict(Ff=1))

    # set NeedAppearances to ensure the fields are visible in Adobe Reader
    if the_pdf.Root.AcroForm:
        the_pdf.Root.AcroForm.update(PdfDict(NeedAppearances=PdfObject("true")))

    PdfWriter().write(output_file, the_pdf)


def join_files(input_files, output_file):
    """input_files is a list of file objects or path names
    output_file can be file object or path name"""

    # standard PdfWriter does not copy AcroForm objects
    # modified from https://stackoverflow.com/a/57687160

    output = PdfWriter()
    output_acroform = None
    for pdf in input_files:
        input = PdfReader(pdf, verbose=False)
        output.addpages(input.pages)
        if (
            PdfName("AcroForm") in input[PdfName("Root")].keys()
        ):  # Not all PDFs have an AcroForm node
            source_acroform = input[PdfName("Root")][PdfName("AcroForm")]
            if PdfName("Fields") in source_acroform:
                output_formfields = source_acroform[PdfName("Fields")]
            else:
                output_formfields = []
            if output_acroform == None:
                # copy the first AcroForm node
                output_acroform = source_acroform
            else:
                for key in source_acroform.keys():
                    # Add new AcroForms keys if output_acroform already existing
                    if key not in output_acroform:
                        output_acroform[key] = source_acroform[key]
                # Add missing font entries in /DR node of source file
                if (PdfName("DR") in source_acroform.keys()) and (
                    PdfName("Font") in source_acroform[PdfName("DR")].keys()
                ):
                    if PdfName("Font") not in output_acroform[PdfName("DR")].keys():
                        # if output_acroform is missing entirely the /Font node under an existing /DR, simply add it
                        output_acroform[PdfName("DR")][
                            PdfName("Font")
                        ] = source_acroform[PdfName("DR")][PdfName("Font")]
                    else:
                        # else add new fonts only
                        for font_key in source_acroform[PdfName("DR")][
                            PdfName("Font")
                        ].keys():
                            if (
                                font_key
                                not in output_acroform[PdfName("DR")][PdfName("Font")]
                            ):
                                output_acroform[PdfName("DR")][PdfName("Font")][
                                    font_key
                                ] = source_acroform[PdfName("DR")][PdfName("Font")][
                                    font_key
                                ]
            if PdfName("Fields") not in output_acroform:
                output_acroform[PdfName("Fields")] = output_formfields
            else:
                # Add new fields
                output_acroform[PdfName("Fields")] += output_formfields
    output.trailer[PdfName("Root")][PdfName("AcroForm")] = output_acroform
    output.write(output_file)
