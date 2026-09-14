# Import PdfReader so Python can open and read PDF files.
from pypdf import PdfReader

# Import json so we can save structured page records.
import json

# Import re so we can detect the printed page number in the extracted footer.
import re

# Import Path for safe file and folder handling.
from pathlib import Path


# Store the location of the PDF.
pdf_path = Path(
    "data/raw/RAG on AWS using Terraform and Bedrock - selected.pdf"
)

# Open the PDF.
reader = PdfReader(pdf_path)

# Store one record for each page.
page_records = []

# Read the PDF page by page.
for page_number, page in enumerate(reader.pages, start=1):
    extracted_text = page.extract_text() or ""

    # For this PDF, the printed page number appears at the end of the extracted text.
    page_match = re.search(r"(\d+)\s*$", extracted_text.strip())

    printed_page_number = (
        int(page_match.group(1))
        if page_match
        else None
    )

    page_record = {
        "source_name": pdf_path.name,
        "source_path": str(pdf_path),
        "pdf_page_number": page_number,
        "printed_page_number": printed_page_number,
        "text": extracted_text,
    }

    page_records.append(page_record)

# Show how many page records were created.
print("Total page records:", len(page_records))

# Check whether any page contains no extractable text.
empty_pages = [
    record["pdf_page_number"]
    for record in page_records
    if not record["text"].strip()
]

print("Empty pages:", empty_pages)

# Choose where to save the structured output.
output_path = Path("tmp/page_records.json")

# Create the tmp folder if it does not already exist.
output_path.parent.mkdir(exist_ok=True)

# Save all page records as readable JSON.
with output_path.open("w", encoding="utf-8") as output_file:
    json.dump(
        page_records,
        output_file,
        indent=2,
        ensure_ascii=False,
    )

print("Saved page records to:", output_path)

# Inspect the first page record.
first_record = page_records[0]

print("\nFirst record source:", first_record["source_name"])
print("PDF page position:", first_record["pdf_page_number"])
print("Printed page number:", first_record["printed_page_number"])
print("Character count:", len(first_record["text"]))

print("\nFirst record text preview:\n")
print(first_record["text"][:1200])
