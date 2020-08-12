import shutil

from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw

from absentee.generateform import generate_pdf_template
from absentee.state_pdf_data import STATE_DATA
from common import enums


class Command(BaseCommand):
    help = "Development utility to generate a signed PDF"
    requires_system_checks = False

    def add_arguments(self, parser):
        parser.add_argument("state", type=str)

        parser.add_argument(
            "--box", action="store_true", help="Use a box instead of a signature image",
        )

    def handle(self, *args, **options):
        state = options["state"]

        if options["box"]:
            pos = list(STATE_DATA[state]["signatures"].values())[0]

            signature = Image.new(
                "RGB", (pos["width"] * 10, pos["height"] * 10), "white"
            )
            draw = ImageDraw.Draw(signature)
            draw.rectangle((0, 0) + signature.size, fill=(255, 0, 0))
        else:
            signature = Image.open("absentee/management/commands/sig.jpg")

        out = f"absentee/management/commands/out/{state}.pdf"

        template, n_pages = generate_pdf_template(state, enums.SubmissionType.LEO_EMAIL)
        with template.fill({}, signature) as filled_pdf:
            with open(out, "wb") as of:
                shutil.copyfileobj(filled_pdf, of)

        print(f"Generated: {out}")
