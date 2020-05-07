from rest_framework.parsers import FileUploadParser


class UnnamedFileUploadParser(FileUploadParser):
    """
    A subclass of FileUploadParser that doesn't require the client to pass
    a file name.
    """

    def get_filename(self, stream, media_type, parser_context):
        return "Unnamed File"
