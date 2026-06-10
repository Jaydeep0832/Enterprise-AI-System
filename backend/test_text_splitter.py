from app.rag.pdf_loader import PDFLoader
from app.rag.text_splitter import TextSplitter

pdf_text = PDFLoader.load("sample.pdf")

splitter = TextSplitter()

chunks = splitter.split_text(pdf_text)

print(f"Total Chunks: {len(chunks)}")

print("\nFirst Chunk:\n")
print(chunks[0])

print("\nChunk Length:")
print(len(chunks[0]))
