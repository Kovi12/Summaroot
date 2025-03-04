import json
import logging
import os
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def load_json(file_path):
    """Load JSON file if it exists, otherwise return None."""
    if not os.path.exists(file_path):
        logging.error(f"JSON file not found: {file_path}")
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading JSON: {e}")
        return None

def generate_unique_color(used_colors):
    """Generate a unique highlight color."""
    while True:
        color = (random.uniform(0.3, 1), random.uniform(0.3, 1), random.uniform(0.3, 1))
        if color not in used_colors:
            used_colors.add(color)
            return color

def compute_similarity(summary_blocks, source_blocks, source_pdf):
    """Compute similarity using TF-IDF and store bounding box references."""
    if not summary_blocks or not source_blocks:
        logging.warning(f"Skipping similarity computation due to missing blocks.")
        return []

    vectorizer = TfidfVectorizer()
    texts = [block["text"] for block in summary_blocks + source_blocks]
    vectors = vectorizer.fit_transform(texts)

    summary_vectors = vectors[:len(summary_blocks)]
    source_vectors = vectors[len(summary_blocks):]

    metadata = []
    used_colors = set()

    for i, summary_vec in enumerate(summary_vectors):
        similarities = cosine_similarity(summary_vec, source_vectors).flatten()
        best_match_idx = int(similarities.argmax())

        metadata.append({
            "summary_text": summary_blocks[i]["text"],
            "summary_page": summary_blocks[i]["page"],
            "summary_bbox": summary_blocks[i]["bbox"],
            "source_text": source_blocks[best_match_idx]["text"],
            "source_pdf": source_pdf,
            "source_page": source_blocks[best_match_idx]["page"],
            "source_bbox": source_blocks[best_match_idx]["bbox"],
            "similarity_score": float(similarities[best_match_idx]),
            "highlight_color": generate_unique_color(used_colors)
        })

    return metadata

def process_group(group_path):
    """Process a group by computing similarity between summary and sources."""
    summary_folder = os.path.join(group_path, "summary")
    source_folder = os.path.join(group_path, "sources")

    # Locate the correct summary JSON file dynamically
    summary_files = [f for f in os.listdir(summary_folder) if f.endswith(".json")]
    if not summary_files:
        logging.error(f"No summary JSON file found in {summary_folder}")
        return

    summary_path = os.path.join(summary_folder, summary_files[0])  # Use the first detected JSON
    summary_data = load_json(summary_path)
    if not summary_data or "text_data" not in summary_data:
        logging.error(f"Invalid or empty summary data in {summary_path}")
        return

    summary_blocks = summary_data["text_data"]  # Ensure bbox is included from Step 1

    source_files = [f for f in os.listdir(source_folder) if f.endswith(".json")]
    if not source_files:
        logging.error(f"No source JSON files found in {source_folder}")
        return

    metadata = []
    for source_file in source_files:
        source_path = os.path.join(source_folder, source_file)
        source_data = load_json(source_path)
        if not source_data or "text_data" not in source_data:
            logging.warning(f"Skipping invalid or empty source file: {source_path}")
            continue

        source_pdf = source_data.get("ocr_pdf", source_file.replace(".json", ".pdf"))
        metadata.extend(compute_similarity(summary_blocks, source_data["text_data"], source_pdf))

    if metadata:
        output_path = os.path.join(group_path, "metadata.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)
        logging.info(f"Metadata saved: {output_path}")

def main():
    intermediary_root = "Intermediary"

    for group_name in os.listdir(intermediary_root):
        group_path = os.path.join(intermediary_root, group_name)
        if os.path.isdir(group_path):
            process_group(group_path)

if __name__ == "__main__":
    main()
