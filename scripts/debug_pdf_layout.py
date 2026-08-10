from app.resume_processing.parsers.pdf_parser import PDFParser


PDF_PATH = "data/uploads/0d9a9aa9-29af-42c8-a989-a251b075797b.pdf"

result = PDFParser.parse(PDF_PATH)

page = result["pages"][0]

print("=" * 100)
print("PDF:", PDF_PATH)
print("PAGE:", page["page_index"])
print("SIZE:", page["width"], "x", page["height"])
print("BLOCKS:", len(page["blocks"]))
print("=" * 100)

for block in page["blocks"]:
    bbox = block["bbox"]

    print(
        "{} | {} | "
        "x={:.1f}-{:.1f} | "
        "y={:.1f}-{:.1f} | "
        "{}".format(
            block["block_index"],
            block["type"],
            bbox["x0"],
            bbox["x1"],
            bbox["y0"],
            bbox["y1"],
            repr(block.get("text", "")[:150]),
        )
    )