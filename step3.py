import json
import logging
import os
import shutil
import fitz

# Configure logging
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
    """Highlight matched text directly using stored bounding boxes and avoid overlap."""
    try:
        doc = fitz.open(pdf_path)
        applied_highlights = 0
        highlighted_areas = set()  # Store already highlighted areas to prevent overlap

        for entry in metadata:
            summary_text = entry["summary_text"]
            highlight_color = entry["highlight_color"]
            top_sources = entry["top_sources"]

            if not top_sources:
                continue  # No valid sources, skip highlighting

            # Extract the best source match
            best_source = top_sources[0]  # Highest-ranked match
            similarity_score = best_source["similarity_score"]

            # Skip highlighting if similarity score is too low
            if similarity_score < 0.2:
                continue

            # Highlight summary text and add a comment
            if is_summary:
                bbox = entry["summary_bbox"]
                page_num = entry["summary_page"]
                page = doc[page_num - 1]
                rect = fitz.Rect(*bbox)

                # Apply highlight annotation
                highlight = page.add_highlight_annot(rect)
                highlight.set_colors(stroke=highlight_color)
                highlight.update(opacity=0.4)

                # Add a proper popup note (comment) to the highlight
                comment_text = f"Best match:\n{best_source['source_text']}\n(Score: {similarity_score:.2f})"
                popup = page.add_text_annot((rect.tl.x, rect.tl.y - 10), comment_text)  # Adjust Y-position slightly
                popup.update()

                applied_highlights += 1

            else:
                for source in top_sources:
                    bbox = source["source_bbox"]
                    page_num = source["source_page"]

                    if tuple(bbox) in highlighted_areas:
                        continue  # Skip if already highlighted

                    highlighted_areas.add(tuple(bbox))  # Mark area as highlighted

                    page = doc[page_num - 1]
                    rect = fitz.Rect(*bbox)

                    # Apply highlight annotation
                    highlight = page.add_highlight_annot(rect)
                    highlight.set_colors(stroke=highlight_color)
                    highlight.update(opacity=0.4)

                    applied_highlights += 1

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
        (os.path.join(input_group_path, "summary", f) for f in os.listdir(os.path.join(input_group_path, "summary")) if
         f.endswith("_ocr.pdf")), None
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
            for source in entry["top_sources"]:
                source_pdf_filename = os.path.basename(source["source_pdf"])  # Get just the filename

                # Ensure correct _ocr.pdf filename
                if not source_pdf_filename.endswith("_ocr.pdf"):
                    source_pdf_filename = source_pdf_filename.replace(".pdf", "_ocr.pdf")

                source_pdf_path = os.path.join(source_folder, source_pdf_filename)  # Correct path

                if os.path.exists(source_pdf_path):
                    source_output_path = os.path.join(output_sources_folder, f"highlighted_{source_pdf_filename}")

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
