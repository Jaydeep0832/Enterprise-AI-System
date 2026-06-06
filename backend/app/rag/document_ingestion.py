from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.document import Document
from app.rag.embedder import Embedder
from app.rag.pdf_loader import PDFLoader
from app.rag.text_splitter import TextSplitter


class DocumentIngestion:

    def __init__(self):
        self.embedder = Embedder()
        self.splitter = TextSplitter()

    def ingest_pdf(self, file_path: str) -> int:
        text = PDFLoader.load(file_path)
        chunks = self.splitter.split_text(text)

        db: Session = SessionLocal()
        try:
            for chunk in chunks:
                embedding = self.embedder.embed(chunk)
                doc = Document(content=chunk, embedding=embedding)
                db.add(doc)
            db.commit()
        finally:
            db.close()

        return len(chunks)
