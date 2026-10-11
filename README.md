# Cargo — Bulk Content & PDF Generator

A professional web application for generating multiple versions of content by replacing airline names, with PDF export capabilities.

## Features

- ✅ Replace airline names using placeholder or original-name mode
- ✅ Generate separate PDFs for each airline with Unicode/emoji support
- ✅ Copy-ready posts with individual and bulk clipboard operations
- ✅ Bulk PDF download as ZIP
- ✅ Template management (save, load, reuse)
- ✅ Rich text editor with formatting preservation
- ✅ CSV/TXT import for airline lists
- ✅ Preview and validation before generation
- ✅ Responsive modern UI with dark mode

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python app.py
   ```

3. **Open your browser:**
   Navigate to `http://localhost:5000`

## Usage

1. **Enter Content:** Add your title and content with `{{AIRLINE_NAME}}` placeholders
2. **Add Airlines:** Paste airline names (one per line) or upload a CSV/TXT file
3. **Choose Output Mode:**
   - **Copy-Ready Posts:** Navigate and copy content directly
   - **Bulk PDFs:** Generate and download PDFs as ZIP
   - **Both:** Get posts and PDFs together
4. **Generate:** Preview, validate, and generate your content

## Project Structure

```
cargo/
├── app.py                 # Flask application entry point
├── services/
│   ├── replacement.py     # Text replacement logic
│   ├── pdf_generator.py   # PDF generation with Unicode support
│   ├── validation.py      # Input validation
│   └── template_manager.py # Template persistence
├── static/
│   ├── css/
│   │   └── styles.css     # Modern responsive styling
│   └── js/
│       ├── main.js        # Core application logic
│       ├── editor.js      # Content editor
│       ├── generator.js   # Generation workflow
│       └── clipboard.js   # Clipboard operations
├── templates/
│   └── index.html         # Main application interface
└── requirements.txt       # Python dependencies
```

## Technologies

- **Backend:** Flask (lightweight Python web framework)
- **PDF:** ReportLab (professional PDF generation with full Unicode support)
- **Frontend:** Vanilla JavaScript with modern ES6+
- **Styling:** Custom CSS with CSS Grid and Flexbox
- **Storage:** SQLite for templates, file-based for sessions

## Development

To run in development mode with auto-reload:

```bash
flask run --debug
```

## Production Deployment

For production deployment, use a WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## License

Created with 🧠 by Ravi
