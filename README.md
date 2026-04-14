# imageToMarkdownFiles

Convert images and PDFs into Markdown files — so you can paste clean text into ChatGPT, Claude, or any LLM instead of uploading images (which cost way more tokens).

## Supported input formats
- PDF (`.pdf`)
- Images: `.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif`, `.bmp`, `.webp`

## Output
All converted `.md` files land in the `output/` folder inside this project. Open them in any text editor and paste the contents straight into your LLM of choice.

---

## Setup (one time)

### 1. Install Tesseract (required for image OCR)
Tesseract is the engine that reads text out of images. Install it with Homebrew:
```bash
brew install tesseract
```
> Don't have Homebrew? Install it first at https://brew.sh

### 2. Create a virtual environment and install dependencies
Run these three commands from inside the project folder:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

That's it — you're ready to go.

---

## Usage

> **Important:** Make sure your virtual environment is active before running the script. You'll know it's active when you see `(venv)` at the start of your terminal prompt. If it's not active, run `source venv/bin/activate` from the project folder first.

```bash
python3 convert.py path/to/your/file.pdf
python3 convert.py path/to/your/image.png
```

You can also point it at a whole folder and it'll convert everything inside:
```bash
python3 convert.py path/to/folder/
```

Your `.md` files will appear in the `output/` folder.

---

## Example

```bash
cd imageToMarkdownFiles
source venv/bin/activate
python3 convert.py ~/Downloads/resume.pdf
# → output/resume.md
```

Open `output/resume.md`, copy the text, paste into Claude or ChatGPT. Done.
