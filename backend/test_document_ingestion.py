from app.rag.document_ingestion import DocumentIngestion

ingestion = DocumentIngestion()

count = ingestion.ingest_pdf(
    "sample.pdf"
)

print(f"Inserted {count} chunks")
