# Using the Hugging Face Invoice/Receipt Dataset

This guide shows you how to download and use the [invoices-and-receipts_ocr_v1](https://huggingface.co/datasets/mychen76/invoices-and-receipts_ocr_v1) dataset with your DocSage platform.

## Quick Start

### 1. Install Required Packages

```bash
pip install datasets pillow
```

Or reinstall all requirements:

```bash
pip install -r requirements.txt
```

### 2. Download Dataset (Test with Small Sample)

Start with a small sample to test:

```bash
# Download first 20 images from training set
python3 scripts/download_huggingface_dataset.py --split train --max-images 20
```

### 3. Download Full Dataset

Once you've tested, download more:

```bash
# Download all training images (2,040 images)
python3 scripts/download_huggingface_dataset.py --split train

# Or download test set (125 images)
python3 scripts/download_huggingface_dataset.py --split test

# Or download validation set (70 images)
python3 scripts/download_huggingface_dataset.py --split valid
```

### 4. Download with OCR Data

To also extract the pre-computed OCR text:

```bash
python3 scripts/download_huggingface_dataset.py --split train --max-images 50 --extract-ocr
```

This will save:
- Images as PNG files in `data/raw_docs/`
- OCR data as JSON files alongside images

### 5. Ingest Documents

After downloading, process them with your IDP pipeline:

```bash
python3 scripts/ingest_docs.py
```

This will:
- Extract text from images using OCR
- Classify document types
- Extract structured fields
- Create transaction records

### 6. Build Embeddings

Create the FAISS index for RAG:

```bash
python3 scripts/build_embeddings.py
```

### 7. Start Services

```bash
# Terminal 1: API Server
python3 -m app.main

# Terminal 2: Streamlit UI
streamlit run frontend/streamlit_app.py
```

## Script Options

```bash
python3 scripts/download_huggingface_dataset.py --help
```

**Available options:**
- `--dataset`: Hugging Face dataset name (default: `mychen76/invoices-and-receipts_ocr_v1`)
- `--output`: Output directory (default: `data/raw_docs`)
- `--split`: Dataset split - `train`, `test`, or `valid` (default: `train`)
- `--max-images`: Limit number of images (useful for testing)
- `--extract-ocr`: Also save OCR text as JSON files

## Examples

### Download 10 test images
```bash
python3 scripts/download_huggingface_dataset.py --split test --max-images 10
```

### Download all validation images with OCR data
```bash
python3 scripts/download_huggingface_dataset.py --split valid --extract-ocr
```

### Download to custom directory
```bash
python3 scripts/download_huggingface_dataset.py --output data/my_documents --max-images 50
```

## Dataset Information

- **Total Images**: 2,238
  - Train: 2,040 images
  - Test: 125 images
  - Valid: 70 images
- **Format**: PNG images (will be processed via OCR)
- **Size**: ~282 MB
- **Source**: [Hugging Face Dataset](https://huggingface.co/datasets/mychen76/invoices-and-receipts_ocr_v1)

## Troubleshooting

### "ModuleNotFoundError: No module named 'datasets'"
```bash
pip install datasets pillow
```

### "Connection Error" or "Download Failed"
- Check your internet connection
- Hugging Face datasets require internet access
- Try again - sometimes downloads can be interrupted

### "Out of Memory" Error
- Use `--max-images` to limit the download
- Process in smaller batches
- Download one split at a time

### Images Not Processing
- Make sure Tesseract OCR is installed
- Check that images are in `data/raw_docs/`
- Verify file permissions

## Next Steps

After downloading and ingesting:

1. **View Documents**: Check Streamlit UI → Documents tab
2. **Ask Questions**: Use Chat tab to query the data
3. **View Analytics**: See vendor stats and category breakdowns
4. **Add More Data**: Download additional splits or add your own PDFs

## Alternative: Use Your Own Documents

You can also add your own PDFs or images:

```bash
# Copy your files
cp /path/to/your/documents/*.pdf data/raw_docs/
cp /path/to/your/images/*.png data/raw_docs/

# Ingest
python3 scripts/ingest_docs.py
```

