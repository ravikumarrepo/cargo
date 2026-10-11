# 🚀 Cargo - Quick Reference Card

## Installation (30 seconds)
```bash
pip install -r requirements.txt
python run.py
```
Open: http://localhost:5000

---

## Basic Usage (3 steps)

### 1️⃣ Enter Content
```
Title: Welcome to {{AIRLINE_NAME}}
Content: Book your flight with {{AIRLINE_NAME}} today! ✈️
```

### 2️⃣ Add Airlines
```
Air India
IndiGo
SpiceJet
Emirates
```

### 3️⃣ Generate
- Choose output mode (Posts / PDFs / Both)
- Click "Generate Content"
- Copy or download results

---

## Key Features

✅ **Replace** `{{AIRLINE_NAME}}` with each airline automatically  
✅ **Preserve** emojis, Unicode, line breaks, formatting  
✅ **Generate** separate PDFs for each airline  
✅ **Copy** to clipboard with one click  
✅ **Download** all PDFs as ZIP  
✅ **Save** templates for reuse  
✅ **Preview** before generating  
✅ **Validate** inputs automatically  

---

## Output Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| 📋 **Posts** | Copy-ready text | Social media, emails |
| 📄 **PDFs** | Downloadable documents | Reports, printing |
| 🚀 **Both** | Posts + PDFs | Complete campaigns |

---

## Replacement Modes

### Placeholder Mode (Default)
```
Input:  "Welcome to {{AIRLINE_NAME}}"
Output: "Welcome to Air India"
        "Welcome to IndiGo"
        "Welcome to SpiceJet"
```

### Original-Name Mode
```
Input:  "Welcome to Air India"
Original: "Air India"
Output: "Welcome to Emirates"
        "Welcome to Qatar Airways"
```

---

## PDF Settings

- **Page Size:** A4 / Letter
- **Orientation:** Portrait / Landscape
- **Font Size:** 8-18pt
- **Margins:** 20-100pt

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Generate | Ctrl + Enter |
| Preview | Ctrl + P |
| Save Template | Ctrl + S |
| New Project | Ctrl + N |

---

## File Formats

### Input
- ✅ TXT (plain text, one per line)
- ✅ CSV (with or without headers)
- ✅ Paste directly

### Output
- ✅ PDF (individual or ZIP)
- ✅ JSON (structured data)
- ✅ Clipboard (text)

---

## API Endpoints

```
POST /api/validate          - Validate inputs
POST /api/preview           - Preview single airline
POST /api/generate          - Generate all content
POST /api/generate-pdf      - Single PDF
POST /api/generate-bulk-pdfs - All PDFs as ZIP
POST /api/parse-airlines    - Parse airline list
GET  /api/templates         - List templates
POST /api/templates         - Save template
GET  /api/templates/:id     - Get template
DELETE /api/templates/:id   - Delete template
```

---

## Common Commands

```bash
# Start application
python run.py

# Run tests
python tests.py

# Install dependencies
pip install -r requirements.txt

# Production server
gunicorn -w 4 app:app
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Port in use | Change port: `python run.py --port 5001` |
| PDFs blank | Reinstall: `pip install --force-reinstall reportlab` |
| Import error | Install deps: `pip install -r requirements.txt` |
| Templates not saving | Check folder permissions |

---

## Example Workflows

### Social Media Campaign
1. Create post template with `{{AIRLINE_NAME}}`
2. Add 20 airlines
3. Select "Copy-Ready Posts"
4. Generate and copy each post
5. Paste directly to social media

### Monthly Report
1. Write report with `{{AIRLINE_NAME}}`
2. Add all airlines from CSV
3. Select "Bulk PDFs"
4. Generate and download ZIP
5. Extract and distribute

### Email Newsletter
1. Use original-name mode
2. Replace placeholder airline
3. Generate for 100+ recipients
4. Export as JSON for mail merge

---

## Performance

| Task | Time |
|------|------|
| 10 airlines | < 1 second |
| 100 airlines | ~500ms posts, ~15s PDFs |
| 500 airlines | ~2s posts, ~60s PDFs |

---

## File Structure

```
cargo/
├── app.py              # Main application
├── run.py              # Startup script
├── requirements.txt    # Dependencies
├── services/           # Business logic
├── templates/          # HTML templates
├── static/             # CSS & JavaScript
└── tests.py            # Test suite
```

---

## Configuration

Edit `.env` or environment variables:

```env
FLASK_ENV=production
SECRET_KEY=your-secret-key
PORT=5000
DEBUG=False
```

---

## Tips

💡 **Save templates** for frequently used content  
💡 **Preview first** to verify replacements  
💡 **Use CSV** for large airline lists  
💡 **Batch process** 50-100 at a time for best performance  
💡 **Enable case-sensitive** only when needed  

---

## Support

📖 **Full Docs:** README.md, SETUP.md, FEATURES.md  
🧪 **Tests:** `python tests.py`  
🐛 **Debug:** Set `FLASK_DEBUG=True`  

---

**Created with 🧠 by Ravi**

Cargo v1.0 - Bulk Content & PDF Generator
