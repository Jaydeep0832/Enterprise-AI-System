from app.rag.pdf_loader import PDFLoader

pdf_path = "sample.pdf"

text = PDFLoader.load(pdf_path)

print(text[:1000])
