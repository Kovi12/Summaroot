# **Sumaroot**

## **Project Overview**
This project **automatically processes documents**, extracts text, identifies matching segments, and highlights corresponding parts in **both summaries and source PDFs**.

The pipeline consists of **three main steps**:
1. **Step 1:** OCR-processing PDFs, extracting text with bounding boxes.
2. **Step 2:** Matching extracted text using **Cosine Similarity (TF-IDF)**.
3. **Step 3:** Highlighting matched text in **both summary and source PDFs**.

A **main script (`main.py`)** runs the entire pipeline sequentially.

---

## **Project Structure**
```
/project_root/
│── Input/                   # Folder where input PDFs should be placed
│   ├── group1/              # Example group folder
│   │   ├── sources/         # Source PDFs
│   │   ├── summary/         # Summary PDFs
│── Intermediary/            # Stores OCR-processed PDFs and extracted text
│── Output/                  # Stores final highlighted PDFs
│── step1.py                 # OCRs PDFs and extracts text with bounding boxes
│── step2.py                 # Matches summary and source text using similarity
│── step3.py                 # Highlights text in PDFs using saved bounding boxes
│── main.py                  # Runs all steps sequentially
│── README.md                # Project documentation
│── requirements.txt         # Required Python libraries
```

---

## **Required Libraries**
This project relies on the following Python libraries:

| **Library**       | **Used For** |
|------------------|-------------|
| `fitz` (PyMuPDF) | Extracting text & bounding boxes from PDFs |
| `pytesseract`    | OCR (Optical Character Recognition) for scanned PDFs |
| `pdf2image`      | Converting PDFs to images for OCR processing |
| `PyPDF2`         | Merging single-page OCR outputs into a full PDF |
| `scikit-learn`   | Implementing **TF-IDF + Cosine Similarity** for text matching |
| `shutil`         | Cleaning `Intermediary` and `Output` folders before processing |
| `logging`        | Logging execution steps for debugging |
| `subprocess`     | Running scripts automatically via `main.py` |

### **Install Dependencies**
Before running the project, install the required libraries:
```sh
pip install -r requirements.txt
```
If `pytesseract` is missing, install Tesseract OCR manually:
- **Windows:** Download from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki).
- **Linux/macOS:** Install via package manager (`sudo apt install tesseract-ocr`).

---

## **Pipeline Workflow**
### **Step 1: OCR and Text Extraction**
- **Clears the `Intermediary` folder** before starting.
- Processes PDFs from `Input/`, converting them to **OCR-readable versions**.
- Extracts **text + bounding box locations** and saves them as JSON.

### **Step 2: Text Matching with Similarity**
- Loads extracted text from JSON.
- Uses **TF-IDF & Cosine Similarity** to match **summary** text with the **most similar** source text.
- Saves matches in `metadata.json` (includes text, pages, bounding boxes, and colors).

### **Step 3: Highlighting Matched Text**
- Loads `metadata.json` and **applies highlights** to both summary and source PDFs.
- Saves results in the `Output/` folder.
- Clears **old highlights** before processing new ones.

### **Running the Full Pipeline**
Instead of manually running each step, use the main script:
```sh
python main.py
```
This will:
1. **Run Step 1** (OCR and text extraction)
2. **Run Step 2** (Text matching)
3. **Run Step 3** (Highlighting PDFs)

All results will be stored in the `Output/` folder.

---

## **Input and Output Example**
### **Before Processing (`Input/`)**
```
Input/
└── group1/
    ├── sources/
    │   ├── document_1.pdf
    │   ├── document_2.pdf
    ├── summary/
    │   ├── summary.pdf
```
### **After Processing (`Output/`)**
```
Output/
└── group1/
    ├── highlighted__summary_ocr.pdf
    ├── sources/
    │   ├── highlighted_document_1_ocr.pdf
    │   ├── highlighted_document_2_ocr.pdf
```

---

## **Troubleshooting & Logs**
- **Check logs for errors**  
  If something doesn’t work, check logs printed during execution.

- **Missing Highlights?**  
  - Ensure **OCR worked correctly** (check `Intermediary/` for `_ocr.pdf` files).
  - Verify that **bounding boxes exist in `metadata.json`**.
  - Check that **Step 3 applies highlights to correct coordinates**.

- **Incorrect Text Matching?**  
  - Review **TF-IDF matching in `step2.py`**.
  - Verify that source and summary **texts are well-structured**.


