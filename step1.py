import json
import logging
import os
import shutil
import fitz
import pytesseract
from pdf2image import convert_from_path
from PyPDF2 import PdfMerger


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def clear_intermediary_folder(folder_path):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    os.makedirs(folder_path)

def ocr_and_save_pdf(pdf_path, output_path):
    """Convert scanned pages to OCR-processed PDFs and save the complete document."""
    images = convert_from_path(pdf_path)
    merger = PdfMerger()

    temp_pdf_paths = []
    for i, img in enumerate(images):
        temp_pdf_path = f"{output_path}_page_{i + 1}.pdf"
        ocr_pdf = pytesseract.image_to_pdf_or_hocr(img, extension='pdf')
        with open(temp_pdf_path, "wb") as f:
            f.write(ocr_pdf)
        temp_pdf_paths.append(temp_pdf_path)

    # Merge all single-page PDFs into one full document
    for temp_pdf in temp_pdf_paths:
        merger.append(temp_pdf)

    merger.write(output_path)
    merger.close()

    # Cleanup temporary PDFs
    for temp_pdf in temp_pdf_paths:
        os.remove(temp_pdf)

    logging.info(f"OCR-processed PDF saved: {output_path}")

def extract_text_with_blocks(pdf_path):
    """Extract words, then merge them into larger bounding boxes."""
    doc = fitz.open(pdf_path)
    extracted_data = []

    for page_num, page in enumerate(doc):
        words = page.get_text("words")  # Extract words instead of blocks
        words.sort(key=lambda w: (w[1], w[0]))  # Sort words by y, then x

        if not words:
            continue

        current_text = []
        current_bbox = list(words[0][:4])  # Start with first word's bbox

        for word in words:
            x0, y0, x1, y1, text, *_ = word

            # If close enough vertically, merge into the same bounding box
            if abs(y0 - current_bbox[1]) < 250:
                current_text.append(text)
                current_bbox[0] = min(current_bbox[0], x0)
                current_bbox[1] = min(current_bbox[1], y0)
                current_bbox[2] = max(current_bbox[2], x1)
                current_bbox[3] = max(current_bbox[3], y1)
            else:
                # Save the last paragraph-sized bbox and reset
                extracted_data.append({
                    "text": " ".join(current_text),
                    "bbox": current_bbox,
                    "page": page_num + 1
                })
                current_text = [text]
                current_bbox = [x0, y0, x1, y1]

        # Save last detected paragraph
        if current_text:
            extracted_data.append({
                "text": " ".join(current_text),
                "bbox": current_bbox,
                "page": page_num + 1
            })

    return extracted_data


def save_extracted_data(output_path, text_data):
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(text_data, f, indent=4, ensure_ascii=False)
        logging.info(f"Extracted text saved: {output_path}")
    except Exception as e:
        logging.error(f"Error saving extracted text: {e}")

def process_pdf(pdf_path, output_folder):
    filename = os.path.splitext(os.path.basename(pdf_path))[0]
    ocr_pdf_path = os.path.join(output_folder, f"{filename}_ocr.pdf")
    json_output_path = os.path.join(output_folder, f"{filename}.json")

    # Apply OCR to generate full searchable PDF
    ocr_and_save_pdf(pdf_path, ocr_pdf_path)

    # Extract text with block locations
    text_data = extract_text_with_blocks(ocr_pdf_path)

    # Save extracted text along with source PDF reference
    save_extracted_data(json_output_path, {"filename": pdf_path, "ocr_pdf": ocr_pdf_path, "text_data": text_data})

def main():
    input_root, intermediary_root = "Input", "Intermediary"

    # Clear the entire Intermediary folder before processing
    clear_intermediary_folder(intermediary_root)

    for group_name in os.listdir(input_root):
        group_input_path = os.path.join(input_root, group_name)
        group_intermediary_path = os.path.join(intermediary_root, group_name)
        os.makedirs(group_intermediary_path, exist_ok=True)

        sources_folder = os.path.join(group_input_path, "sources")
        intermediary_summary_folder = os.path.join(group_intermediary_path, "summary")
        intermediary_sources_folder = os.path.join(group_intermediary_path, "sources")

        os.makedirs(intermediary_summary_folder, exist_ok=True)
        os.makedirs(intermediary_sources_folder, exist_ok=True)

        # Process summary PDFs
        for pdf_file in os.listdir(group_input_path):
            if pdf_file.endswith(".pdf"):
                process_pdf(os.path.join(group_input_path, pdf_file), intermediary_summary_folder)

        # Process source PDFs
        if os.path.exists(sources_folder):
            for pdf_file in os.listdir(sources_folder):
                if pdf_file.endswith(".pdf"):
                    process_pdf(os.path.join(sources_folder, pdf_file), intermediary_sources_folder)

if __name__ == "__main__":
    main()
