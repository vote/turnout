import textwrap


def wraptext(text: str, indent: int = 4, wrap: int = 80) -> str:
    """
    Given a (potentially multi-line) block of text, wraps that text and indents
    it.
    """
    paras = [
        textwrap.indent(textwrap.fill(para, width=(wrap - indent)), " " * indent)
        for para in text.split("\n")
    ]
    return "\n".join(paras)
