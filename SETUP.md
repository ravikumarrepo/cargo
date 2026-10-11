# SETUP AND INSTALLATION GUIDE

## Quick Start (5 minutes)

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python run.py
```

The application will start on **http://localhost:5000**

### 3. Open in Browser

Navigate to http://localhost:5000 and start generating content!

---

## System Requirements

- **Python:** 3.8 or higher
- **pip:** Latest version
- **Modern Web Browser:** Chrome, Firefox, Safari, or Edge

### Check Python Version

```bash
python --version
```

Should be `Python 3.8.0` or higher.

---

## Installation Steps (Detailed)

### 1. Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Verify Installation

```bash
python -c "import flask, reportlab; print('✓ All dependencies installed')"
```

### 4. Start Development Server

```bash
python run.py
```

You should see:
```
 * Running on http://0.0.0.0:5000
```

---

## Usage Guide

### Basic Workflow

1. **Enter Content**
   - Add a title with `{{AIRLINE_NAME}}` placeholder
   - Add content body
   - The placeholder will be replaced with each airline

2. **Add Airlines**
   - Paste airline names (one per line)
   - Or upload a CSV/TXT file
   - Or enter comma-separated values

3. **Choose Output Mode**
   - **Copy-Ready Posts:** Navigate and copy content
   - **Bulk PDFs:** Download all as ZIP
   - **Both:** Get posts + PDFs

4. **Generate**
   - Click "Generate Content"
   - View results immediately
   - Download or copy as needed

### Advanced Features

**Original-Name Mode:**
- Replace an existing airline name instead of a placeholder
- Useful when content already mentions an airline

**Case-Sensitive Matching:**
- Exact case matching for replacements
- Useful for acronyms like "US Airways" vs "us airways"

**Templates:**
- Save your content as templates
- Load saved templates for reuse
- Manage multiple project templates

---

## Production Deployment

### Option 1: Using Gunicorn (Recommended)

```bash
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Option 2: Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Build and run:

```bash
docker build -t cargo .
docker run -p 5000:5000 cargo
```

### Option 3: AWS/Heroku/DigitalOcean

1. Set environment variables:
   ```
   FLASK_ENV=production
   SECRET_KEY=<your-secure-key>
   ```

2. Set port to 8000 or container port

3. Deploy:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:$PORT app:app
   ```

---

## Environment Variables

Create `.env` file for configuration:

```env
# Flask
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-secure-secret-key-here

# Server
PORT=5000
HOST=0.0.0.0

# Logging
LOG_LEVEL=INFO
```

Load with:

```bash
pip install python-dotenv
```

---

## Testing

Run the test suite:

```bash
python -m pytest tests.py -v
```

Run specific test:

```bash
python -m pytest tests.py::TestReplacementService -v
```

Check test coverage:

```bash
pip install pytest-cov
python -m pytest tests.py --cov=services
```

---

## Troubleshooting

### Port 5000 Already in Use

```bash
# Find process using port 5000
lsof -i :5000  # macOS/Linux
netstat -ano | findstr :5000  # Windows

# Kill process or use different port
python run.py --port 5001
```

### SSL Certificate Errors

```bash
pip install --upgrade certifi
```

### PDF Generation Issues

Ensure ReportLab is properly installed:

```bash
pip install --upgrade reportlab pillow
```

### Template Loading Issues

Check permissions on `templates_data` folder:

```bash
chmod 755 templates_data  # macOS/Linux
icacls templates_data /grant Everyone:(F)  # Windows
```

---

## File Structure

```
cargo/
├── app.py                      # Flask main application
├── config.py                   # Configuration settings
├── run.py                      # Startup script
├── requirements.txt            # Python dependencies
├── tests.py                    # Test suite
├── README.md                   # Documentation
│
├── services/                   # Business logic
│   ├── replacement.py          # Text replacement
│   ├── pdf_generator.py        # PDF creation
│   ├── validation.py           # Input validation
│   ├── template_manager.py     # Template management
│   └── __init__.py
│
├── templates/                  # HTML templates
│   └── index.html              # Main application UI
│
├── static/                     # Static assets
│   ├── css/
│   │   └── styles.css          # Application styling
│   └── js/
│       ├── main.js             # Core logic
│       ├── generator.js        # Content generation
│       └── clipboard.js        # Clipboard operations
│
└── templates_data/             # User template storage
```

---

## Performance Optimization

### For Large Airline Lists (100+)

```python
# Adjust batch processing in generate_bulk_pdfs
BATCH_SIZE = 20
```

### Enable Caching

```bash
pip install flask-caching
```

### Database Optimization

Use SQLite for templates:

```bash
pip install flask-sqlalchemy
```

---

## Security Notes

1. **Change SECRET_KEY in Production**
   ```python
   SECRET_KEY = os.urandom(32).hex()
   ```

2. **Enable HTTPS**
   - Use reverse proxy (Nginx)
   - Let's Encrypt SSL certificate

3. **Input Validation**
   - All user input is validated
   - HTML is escaped for security

4. **File Upload Limits**
   - Maximum 16MB per file
   - Only TXT and CSV allowed

---

## Performance Benchmarks

- **Generating 100 posts:** ~500ms
- **Generating 100 PDFs:** ~10-15 seconds
- **ZIP file download (100 PDFs):** ~2-3 seconds

---

## Getting Help

### Common Issues

**Q: PDFs are blank**
A: Check ReportLab installation. Reinstall with:
```bash
pip install --force-reinstall reportlab==4.0.7
```

**Q: Clipboard not working**
A: Use fallback manual copy. Grant clipboard permissions in browser.

**Q: Templates not saving**
A: Check folder permissions. Ensure `templates_data/` is writable.

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Updates & Maintenance

### Update Dependencies

```bash
pip install --upgrade -r requirements.txt
```

### Backup Templates

```bash
tar -czf templates_backup.tar.gz templates_data/
```

### Monitor Application

```bash
# View logs
tail -f app.log

# Monitor resources
top -p $(pgrep -f "python run.py")
```

---

## Support & Contributing

**Created with 🧠 by Ravi**

For issues, suggestions, or contributions, please visit the project repository.

---

## License

This application is provided as-is for personal and commercial use.
