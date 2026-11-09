"""OCR + IDP. Document AI in cloud mode; plain-text stub locally."""
from .. import config

def extract_text(pdf_bytes: bytes) -> str:
    if config.LOCAL_MODE:
        try:
            return pdf_bytes.decode("utf-8")  # synthetic contracts are text
        except UnicodeDecodeError:
            return ""
    from google.cloud import documentai
    client = documentai.DocumentProcessorServiceClient()
    req = documentai.ProcessRequest(
        name=config.DOCAI_PROCESSOR,
        raw_document=documentai.RawDocument(content=pdf_bytes, mime_type="application/pdf"),
    )
    return client.process_document(request=req).document.text
