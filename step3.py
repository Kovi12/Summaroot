import json
import logging
import os
import shutil
import fitz

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def clear_output_folder(folder_path):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    os.makedirs(folder_path)

def load_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading JSON: {e}")
        return None

def highlight_text_in_pdf(pdf_path, output_path, metadata, is_summary=False):
    """Highlight matched text directly using stored bounding boxes."""
    try:
        doc = fitz.open(pdf_path)
        applied_highlights = 0

        for entry in metadata:
            bbox = entry["summary_bbox"] if is_summary else entry["source_bbox"]
            page_num = entry["summary_page"] if is_summary else entry["source_page"]
            highlight_color = entry["highlight_color"]

            if bbox and isinstance(bbox, list) and len(bbox) == 4:
                bbox = [float(coord) for coord in bbox]
                page = doc[page_num - 1]
                rect = fitz.Rect(*bbox)

                # Apply highlight annotation
                highlight = page.add_highlight_annot(rect)
                highlight.set_colors(stroke=highlight_color)
                highlight.update(opacity=0.4)

                applied_highlights += 1
            else:
                logging.warning(f"Invalid bbox format in metadata for page {page_num}")

        doc.save(output_path)
        logging.info(f"Highlighted PDF saved: {output_path} with {applied_highlights} highlights.")

    except Exception as e:
        logging.error(f"Error highlighting text in {pdf_path}: {e}")

def process_highlighting(group_folder):
    """Process and highlight both summary and source PDFs."""
    logging.info(f"Processing highlighting for group: {group_folder}")
    metadata_path = os.path.join(group_folder, "metadata.json")

    if not os.path.exists(metadata_path):
        logging.warning(f"Metadata file not found in {group_folder}")
        return

    metadata = load_json(metadata_path)
    input_group_path = os.path.join("Intermediary", os.path.basename(group_folder))
    output_group_path = os.path.join("Output", os.path.basename(group_folder))
    output_sources_folder = os.path.join(output_group_path, "sources")

    os.makedirs(output_group_path, exist_ok=True)
    os.makedirs(output_sources_folder, exist_ok=True)

    # Process Summary PDF
    summary_pdf_path = next(
        (os.path.join(input_group_path, "summary", f) for f in os.listdir(os.path.join(input_group_path, "summary")) if f.endswith("_ocr.pdf")), None
    )

    if summary_pdf_path:
        summary_output_path = os.path.join(output_group_path, f"highlighted_{os.path.basename(summary_pdf_path)}")
        highlight_text_in_pdf(summary_pdf_path, summary_output_path, metadata, is_summary=True)
    else:
        logging.warning(f"No summary PDF found in {input_group_path}")

    # Process Source PDFs
    source_folder = os.path.join(input_group_path, "sources")
    if os.path.exists(source_folder):
        processed_files = {}

        for entry in metadata:
            source_pdf_filename = os.path.basename(entry["source_pdf"])

            if not source_pdf_filename.endswith("_ocr.pdf"):
                source_pdf_filename = source_pdf_filename.replace(".pdf", "_ocr.pdf")

            source_pdf_path = os.path.join(source_folder, source_pdf_filename)

            if os.path.exists(source_pdf_path):

                # Avoid overwriting by grouping highlights per file
                if source_pdf_path not in processed_files:
                    processed_files[source_pdf_path] = []

                processed_files[source_pdf_path].append(entry)
            else:
                logging.warning(f"Source PDF not found: {source_pdf_path}")

        # Apply all highlights per file
        for pdf_path, entries in processed_files.items():
            output_path = os.path.join(output_sources_folder, f"highlighted_{os.path.basename(pdf_path)}")
            highlight_text_in_pdf(pdf_path, output_path, entries, is_summary=False)

def main():
    """Main function to process all groups."""
    output_root = "Output"

    # Clear the Output folder before processing
    clear_output_folder(output_root)

    intermediary_root = "Intermediary"
    for group_name in os.listdir(intermediary_root):
        group_path = os.path.join(intermediary_root, group_name)
        if os.path.isdir(group_path):
            process_highlighting(group_path)

if __name__ == "__main__":
    main()
