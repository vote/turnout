"""
pypdftk

Forked from: https://github.com/revolunet/pypdftk/blob/d394427ea253d2daf726f9a3ef64c8d2fd27710d/pypdftk.py
to add instrumentation.

License (https://github.com/revolunet/pypdftk/blob/d394427ea253d2daf726f9a3ef64c8d2fd27710d/licence.txt):
3-Clause BSD
"""

import itertools
import logging
import os
import shutil
import subprocess
import tempfile
from typing import Dict, List, Optional, Tuple, cast

from common.apm import tracer

log = logging.getLogger("pypdftk")

PDFTK_PATH_ENV = os.getenv("PDFTK_PATH")
if PDFTK_PATH_ENV:
    PDFTK_PATH = PDFTK_PATH_ENV
else:
    PDFTK_PATH = "/usr/bin/pdftk"
    if not os.path.isfile(PDFTK_PATH):
        PDFTK_PATH = "pdftk"


def run_command(command: List[str], shell=False, timeout=60) -> List[bytes]:
    """ run a system command and yield output """
    result = subprocess.run(command, timeout=timeout, capture_output=True)

    if result.returncode != 0:
        cmdstr = " ".join(command)
        log.error(
            f"pdftk shell-out returned exit code {result.returncode}",
            extra={"cmd": cmdstr, "stdout": result.stdout, "stderr": result.stderr},
        )

        # Raise an error
        result.check_returncode()

    return result.stdout.split(b"\n")


try:
    run_command([PDFTK_PATH])
except OSError:
    logging.warning("pdftk test call failed (PDFTK_PATH=%r).", PDFTK_PATH)


def pdftk_cmd_util(
    pdf_path: str,
    action="compress",
    out_file: Optional[str] = None,
    flatten: bool = True,
) -> str:
    """
    :type action: should valid action, in string format. Eg: "uncompress"
    :param pdf_path: input PDF file
    :param out_file: (default=auto) : output PDF path. will use tempfile if not provided
    :param flatten: (default=True) : flatten the final PDF
    :return: name of the output file.
    """
    actions = ["compress", "uncompress"]
    assert action in actions, (
        "Unknown action. Failed to perform given action '%s'." % action
    )

    handle = None
    cleanOnFail = False
    if not out_file:
        cleanOnFail = True
        handle, out_file = tempfile.mkstemp()

    cmd = [PDFTK_PATH, pdf_path, "output", out_file, action]

    if flatten:
        cmd.append("flatten")
    try:
        run_command(cmd, True)
    except:
        if cleanOnFail:
            os.remove(out_file)
        raise
    finally:
        if handle:
            os.close(handle)
    return out_file


class PyPDFTK:
    def get_num_pages(self, pdf_path: str) -> int:
        """ return number of pages in a given PDF file """
        for line in run_command([PDFTK_PATH, pdf_path, "dump_data"]):
            if line.lower().startswith(b"numberofpages"):
                return int(line.split(b":")[1])
        return 0

    @tracer.wrap(name="fill_form", service="pypdftk")
    def fill_form(
        self,
        pdf_path: str,
        datas: Dict[str, str] = {},
        out_file: Optional[str] = None,
        flatten: bool = True,
    ) -> str:
        """
            Fills a PDF form with given dict input data.
            Return temp file if no out_file provided.
        """
        cleanOnFail = False
        tmp_fdf = self.gen_xfdf(datas)
        handle = None
        if not out_file:
            cleanOnFail = True
            handle, out_file = tempfile.mkstemp()

        cmd = [PDFTK_PATH, pdf_path, "fill_form", tmp_fdf, "output", out_file]
        if flatten:
            cmd.append("flatten")
        try:
            run_command(cmd, True)
        except:
            if cleanOnFail:
                os.remove(tmp_fdf)
            raise
        finally:
            if handle:
                os.close(handle)
        os.remove(tmp_fdf)
        return out_file

    @tracer.wrap(name="dump_data_fields", service="pypdftk")
    def dump_data_fields(self, pdf_path: str) -> List[Dict[str, str]]:
        """
            Return list of dicts of all fields in a PDF.
        """
        cmd = [PDFTK_PATH, pdf_path, "dump_data_fields"]
        # Either can return strings with :
        #    field_data = map(lambda x: x.decode("utf-8").split(': ', 1), run_command(cmd, True))
        # Or return bytes with : (will break tests)
        #    field_data = map(lambda x: x.split(b': ', 1), run_command(cmd, True))
        field_data = map(
            lambda x: cast(
                Tuple[str, str], tuple(x.decode("utf-8").split(": ", 1)[0:2])
            ),
            run_command(cmd, True),
        )
        fields = [
            list(group)
            for k, group in itertools.groupby(field_data, lambda x: len(x) == 1)
            if not k
        ]
        return [dict(f) for f in fields]

    @tracer.wrap(name="concat", service="pypdftk")
    def concat(self, files: List[str], out_file: Optional[str] = None) -> str:
        """
            Merge multiples PDF files.
            Return temp file if no out_file provided.
        """
        cleanOnFail = False
        handle = None
        if not out_file:
            cleanOnFail = True
            handle, out_file = tempfile.mkstemp()
        if len(files) == 1:
            shutil.copyfile(files[0], out_file)
        args = [PDFTK_PATH]
        args += files
        args += ["cat", "output", out_file]
        try:
            run_command(args)
        except:
            if cleanOnFail:
                os.remove(out_file)
            raise
        finally:
            if handle:
                os.close(handle)
        return out_file

    @tracer.wrap(name="split", service="pypdftk")
    def split(self, pdf_path: str, out_dir: Optional[str] = None) -> List[str]:
        """
            Split a single PDF file into pages.
            Use a temp directory if no out_dir provided.
        """
        cleanOnFail = False
        if not out_dir:
            cleanOnFail = True
            out_dir = tempfile.mkdtemp()
        out_pattern = "%s/page_%%06d.pdf" % out_dir
        try:
            run_command([PDFTK_PATH, pdf_path, "burst", "output", out_pattern])
        except:
            if cleanOnFail:
                shutil.rmtree(out_dir)
            raise
        out_files = os.listdir(out_dir)
        out_files.sort()
        return [os.path.join(out_dir, filename) for filename in out_files]

    @tracer.wrap(name="gen_xfdf", service="pypdftk")
    def gen_xfdf(self, datas: Dict[str, str] = {}):
        """ Generates a temp XFDF file suited for fill_form function, based on dict input data """
        fields = []
        for key, value in datas.items():
            fields.append(
                """        <field name="%s"><value>%s</value></field>""" % (key, value)
            )
        tpl = """<?xml version="1.0" encoding="UTF-8"?>
    <xfdf xmlns="http://ns.adobe.com/xfdf/" xml:space="preserve">
        <fields>
    %s
        </fields>
    </xfdf>""" % "\n".join(
            fields
        )
        handle, out_file = tempfile.mkstemp()
        f = os.fdopen(handle, "wb")
        f.write((tpl.encode("UTF-8")))
        f.close()
        return out_file

    @tracer.wrap(name="replace_page", service="pypdftk")
    def replace_page(self, pdf_path: str, page_number: int, pdf_to_insert_path: str):
        """
        Replace a page in a PDF (pdf_path) by the PDF pointed by pdf_to_insert_path.
        page_number is the number of the page in pdf_path to be replaced. It is 1-based.
        """
        A = "A=" + pdf_path
        B = "B=" + pdf_to_insert_path
        output_temp = tempfile.mktemp(suffix=".pdf")

        if page_number == 1:  # At begin
            upper_bound = "A" + str(page_number + 1) + "-end"
            args = [PDFTK_PATH, A, B, "cat", "B", upper_bound, "output", output_temp]
        elif page_number == self.get_num_pages(pdf_path):  # At end
            lower_bound = "A1-" + str(page_number - 1)
            args = [PDFTK_PATH, A, B, "cat", lower_bound, "B", "output", output_temp]
        else:  # At middle
            lower_bound = "A1-" + str(page_number - 1)
            upper_bound = "A" + str(page_number + 1) + "-end"
            args = [
                PDFTK_PATH,
                A,
                B,
                "cat",
                lower_bound,
                "B",
                upper_bound,
                "output",
                output_temp,
            ]

        run_command(args)
        shutil.copy(output_temp, pdf_path)
        os.remove(output_temp)

    @tracer.wrap(name="stamp", service="pypdftk")
    def stamp(
        self, pdf_path: str, stamp_pdf_path: str, output_pdf_path: Optional[str] = None
    ) -> str:
        """
        Applies a stamp (from stamp_pdf_path) to the PDF file in pdf_path. Useful for watermark purposes.
        If not output_pdf_path is provided, it returns a temporary file with the result PDF.
        """
        output = output_pdf_path or tempfile.mktemp(suffix=".pdf")
        args = [PDFTK_PATH, pdf_path, "multistamp", stamp_pdf_path, "output", output]
        run_command(args)
        return output

    @tracer.wrap(name="compress", service="pypdftk")
    def compress(
        self, pdf_path: str, out_file: Optional[str] = None, flatten: bool = True
    ) -> str:
        """
        These are only useful when you want to edit PDF code in a text
        editor like vim or emacs.  Remove PDF page stream compression by
        applying the uncompress filter. Use the compress filter to
        restore compression.

        :param pdf_path: input PDF file
        :param out_file: (default=auto) : output PDF path. will use tempfile if not provided
        :param flatten: (default=True) : flatten the final PDF
        :return: name of the output file.
        """

        return pdftk_cmd_util(pdf_path, "compress", out_file, flatten)

    @tracer.wrap(name="uncompress", service="pypdftk")
    def uncompress(
        self, pdf_path: str, out_file: Optional[str] = None, flatten: bool = True
    ) -> str:
        """
        These are only useful when you want to edit PDF code in a text
        editor like vim or emacs.  Remove PDF page stream compression by
        applying the uncompress filter. Use the compress filter to
        restore compression.

        :param pdf_path: input PDF file
        :param out_file: (default=auto) : output PDF path. will use tempfile if not provided
        :param flatten: (default=True) : flatten the final PDF
        :return: name of the output file.
        """

        return pdftk_cmd_util(pdf_path, "uncompress", out_file, flatten)
