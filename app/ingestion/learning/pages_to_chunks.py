import json
from pathlib import Path

input_path = Path("tmp/page_records.json")
with input_path.open("r", encoding="utf-8") as input_file:
    page_records = json.load(input_file)

chunk_size = 800
chunk_overlap = 100
chunk_records = []

for page_record in page_records:
    text = page_record["text"]
    start = 0
    chunk_number = 1

    while start < len(text):
        requested_end = min(start + chunk_size, len(text))
        chunk_end = requested_end

        # Keep the end of a chunk on a word boundary.
        if requested_end < len(text):
            boundary = text.rfind(" ", start, requested_end)
            if boundary > start:
                chunk_end = boundary

        chunk_text = text[start:chunk_end]
        chunk_records.append({
            "source_name": page_record["source_name"],
            "source_path": page_record["source_path"],
            "pdf_page_number": page_record["pdf_page_number"],
            "printed_page_number": page_record["printed_page_number"],
            "chunk_number_on_page": chunk_number,
            "text": chunk_text,
        })

        # The final chunk is complete; do not create an overlap-only duplicate.
        if chunk_end >= len(text):
            break

        # Start overlap at the next complete word.
        candidate_start = max(chunk_end - chunk_overlap, start + 1)
        next_space = text.find(" ", candidate_start, chunk_end)
        if next_space != -1:
            next_start = next_space + 1
        else:
            next_start = candidate_start

        if next_start <= start:
            break

        start = next_start
        chunk_number += 1

output_path = Path("tmp/chunk_records.json")
output_path.parent.mkdir(exist_ok=True)
with output_path.open("w", encoding="utf-8") as output_file:
    json.dump(chunk_records, output_file, indent=2, ensure_ascii=False)

print("Total page records:", len(page_records))
print("Total chunk records:", len(chunk_records))
print("Saved chunks to:", output_path)
