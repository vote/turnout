import base64
import json
import logging
import os
from typing import Any, Dict, Optional

from django.conf import settings
from django.core.files import File
from django.core.files.base import ContentFile
from pdf_template import PDFTemplate
from PIL import Image

from common.apm import tracer
from common.aws import lambda_client, s3_client
from storage.models import SecureUploadItem, StorageItem

from .lambdahelpers import clean_data, serialize_template

logger = logging.getLogger("pypdftk")


class PDFFillerLambdaError(Exception):
    def __init__(self, logs, message="PDF Filler lambda function failed"):
        self.logs = logs
        self.message = message
        super().__init__(message)


@tracer.wrap()
def fill_pdf_template_lambda(
    template: PDFTemplate,
    data: Dict[str, Any],
    item: StorageItem,
    file_name: str,
    signature: Optional[SecureUploadItem] = None,
):
    # Call out to lambda
    signature_url = None
    if signature:
        signature_url = signature.file.url

    cleaned_data = clean_data(data)

    template_data = serialize_template(template)

    with tracer.trace("common.pdf.pdftemplate.save_blank"):
        # Save an empty blob to S3 to set the headers, etc., then generate
        # a presigned PUT
        item.file.save(file_name, ContentFile(""), False)

    output_url = s3_client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.AWS_STORAGE_PRIVATE_BUCKET_NAME,  # type:ignore
            "Key": os.path.join(item.file.storage.location, item.file.name),
        },
    )

    with tracer.trace("common.pdf.pdftemplate.generate_payload"):
        lambda_payload = bytes(
            json.dumps(
                {
                    "template": template_data,
                    "data": cleaned_data,
                    "signature": signature_url,
                    "output": output_url,
                }
            ),
            "utf-8",
        )

    with tracer.trace("common.pdf.pdftemplate.call_lambda"):
        response = lambda_client.invoke(
            FunctionName="pdf-filler-local-fill",
            InvocationType="RequestResponse",
            LogType="Tail",
            Payload=lambda_payload,
        )

    if response.get("FunctionError"):
        logs = base64.b64decode(response["LogResult"]).decode()
        msg = f"Error from PDF Filler Lambda function: {response['FunctionError']}"

        logger.error(
            msg, extra={"lambda_logs": logs},
        )

        raise PDFFillerLambdaError(logs, msg)

    item.save()


@tracer.wrap()
def fill_pdf_template_local(
    template: PDFTemplate,
    data: Dict[str, Any],
    item: StorageItem,
    file_name: str,
    signature: Optional[SecureUploadItem] = None,
):
    # Call into PDFTemplate directly
    signature_image = None
    if signature:
        signature_image = Image.open(signature.file)

    with template.fill(data, signature_image) as filled_pdf:
        item.file.save(file_name, File(filled_pdf), True)


def fill_pdf_template(
    template: PDFTemplate,
    data: Dict[str, Any],
    item: StorageItem,
    file_name: str,
    signature: Optional[SecureUploadItem] = None,
):
    if settings.PDF_GENERATION_LAMBDA_ENABLED:
        fill_pdf_template_lambda(template, data, item, file_name, signature)
    else:
        fill_pdf_template_local(template, data, item, file_name, signature)
