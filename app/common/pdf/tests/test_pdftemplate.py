import os
import subprocess
import tempfile

from PIL import Image

from common.pdf.pdftemplate import PDFTemplate, PDFTemplateSection, SignatureBoundingBox


def relpath(path):
    return os.path.join(os.path.dirname(__file__), path)


# From: https://github.com/python-needle/needle/blob/master/needle/engines/imagemagick_engine.py
compare_path = "compare"
compare_command = (
    "{compare} -metric RMSE -subimage-search -dissimilarity-threshold 1.0 {baseline} "
    "{new} {diff}"
)


def assertSameFiles(output_file, baseline_file, threshold=0):
    diff_file = output_file.replace(".png", ".diff.png")

    compare_cmd = compare_command.format(
        compare=compare_path, baseline=baseline_file, new=output_file, diff=diff_file,
    )
    process = subprocess.Popen(
        compare_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    compare_stdout, compare_stderr = process.communicate()

    difference = float(compare_stderr.split()[1][1:-1])
    if difference <= threshold:
        os.remove(diff_file)
        return

    raise AssertionError(
        "The new screenshot '{new}' did not match "
        "the baseline '{baseline}' (See {diff}):\n"
        "{stdout}{stderr}".format(
            new=output_file,
            baseline=baseline_file,
            diff=diff_file,
            stdout=compare_stdout,
            stderr=compare_stderr,
        )
    )


def test_pdftemplate():
    input_data = {
        "is_18_or_over": True,
        "title_mr": False,
        "title_ms": True,
        "first_name": "Foo",
        "last_name": "Bar",
        "address1": "None",
        "zipcode": None,
        "mailto_line_1": "some address!",
    }

    template = PDFTemplate(
        [
            PDFTemplateSection(path=relpath("test-input-page-1.pdf"), is_form=True),
            PDFTemplateSection(
                path=relpath("test-input-page-2-3.pdf"),
                is_form=True,
                signature_locations={
                    1: SignatureBoundingBox(x=300, y=490, width=200, height=37)
                },
            ),
            PDFTemplateSection(
                path=relpath("test-input-page-4.pdf"),
                signature_locations={
                    1: SignatureBoundingBox(x=188, y=50, width=200, height=28)
                },
            ),
        ]
    )

    with template.fill(
        input_data, signature=Image.open(relpath("sig.jpeg"))
    ) as output_pdf:
        tmpdir = tempfile.mkdtemp()
        output_dir = os.path.join(tmpdir, "actual-output-page.png")

        assert os.system(f"convert {output_pdf.name} {output_dir}") == 0

        for page in range(0, 4):
            assertSameFiles(
                os.path.join(tmpdir, f"actual-output-page-{page}.png"),
                relpath(f"test-output-page-{page}.png"),
                0.005,
            )
