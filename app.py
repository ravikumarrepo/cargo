"""
Cargo - Bulk Content & PDF Generator
Main Flask application entry point with authentication
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
import os
import json
import zipfile
from io import BytesIO
from datetime import datetime

from services.replacement import ReplacementService
from services.pdf_generator import PDFGenerator
from services.validation import ValidationService
from services.template_manager import TemplateManager
from services.models import db, User
from services.auth_service import AuthService
from services.admin_service import AdminService
from services.decorators import auth_required, admin_required, get_current_user
import config

app = Flask(__name__)

# Load configuration
app.config.from_object('config')

# Initialize database
db.init_app(app)
migrate = Migrate(app, db)

# Runtime overrides for paths (kept absolute so they work under any CWD)
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['GENERATED_FOLDER'] = config.GENERATED_FOLDER

# Ensure required directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)

# Initialize services
replacement_service = ReplacementService()
pdf_generator = PDFGenerator()
validation_service = ValidationService()
template_manager = TemplateManager()


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/login', methods=['GET'])
def login_page():
    """Render login page"""
    return render_template('login.html')


@app.route('/register', methods=['GET'])
def register_page():
    """Render registration page"""
    return render_template('register.html')


@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.json
        email = data.get('email', '').strip()
        full_name = data.get('fullName', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirmPassword', '')

        success, message, user = AuthService.register_user(
            email=email,
            full_name=full_name,
            password=password,
            confirm_password=confirm_password
        )

        if success:
            return jsonify({
                'success': True,
                'message': message
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Registration failed: {str(e)}'
        }), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login a user"""
    try:
        data = request.json
        email = data.get('email', '').strip()
        password = data.get('password', '')

        success, message, session, user = AuthService.authenticate(email, password)

        if success:
            response = jsonify({
                'success': True,
                'message': message,
                'token': session.token,
                'refreshToken': session.refresh_token,
                'expiresAt': session.expires_at.isoformat(),
                'refreshExpiresAt': session.refresh_expires_at.isoformat(),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'is_admin': user.is_admin
                }
            })
            # Set secure cookie
            response.set_cookie(
                'auth_token',
                session.token,
                httponly=True,
                secure=app.config.get('SESSION_COOKIE_SECURE', False),
                samesite='Lax',
                max_age=900  # 15 minutes
            )
            return response, 200
        else:
            # Determine which status page to show
            status = 'login_failed'
            if user:
                status = user.account_status

            return jsonify({
                'success': False,
                'error': message,
                'status': status,
                'rejected_reason': user.rejected_reason if user and user.account_status == 'rejected' else None
            }), 401

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Login failed: {str(e)}'
        }), 500


@app.route('/api/auth/logout', methods=['POST'])
@auth_required
def logout():
    """Logout a user"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            token = request.cookies.get('auth_token')

        if token:
            AuthService.logout(token)

        response = jsonify({'success': True, 'message': 'Logged out'})
        response.delete_cookie('auth_token')
        return response, 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auth/refresh', methods=['POST'])
def refresh_session():
    """Refresh session using refresh token"""
    try:
        data = request.json
        refresh_token = data.get('refreshToken', '').strip()

        if not refresh_token:
            return jsonify({'success': False, 'error': 'Refresh token required'}), 400

        success, message, session = AuthService.refresh_session(refresh_token)

        if success:
            return jsonify({
                'success': True,
                'message': message,
                'token': session.token,
                'refreshToken': session.refresh_token,
                'expiresAt': session.expires_at.isoformat(),
                'refreshExpiresAt': session.refresh_expires_at.isoformat()
            }), 200
        else:
            return jsonify({'success': False, 'error': message}), 401

    except Exception as e:
        return jsonify({'success': False, 'error': f'Refresh failed: {str(e)}'}), 500


@app.route('/pending')
def pending_page():
    """Show pending approval message"""
    return render_template('pending.html')


@app.route('/rejected')
def rejected_page():
    """Show rejected message"""
    reason = request.args.get('reason', 'No reason provided')
    return render_template('rejected.html', reason=reason)


@app.route('/revoked')
def revoked_page():
    """Show revoked access message"""
    return render_template('revoked.html')


@app.route('/suspended')
def suspended_page():
    """Show suspended account message"""
    return render_template('suspended.html')


# ============================================================================
# HEALTH CHECK (used by Render / uptime monitors — does not touch the DB)
# ============================================================================

@app.route('/healthz')
def health_check():
    """Liveness probe. Keep this DB-free so it always answers."""
    return jsonify({'status': 'ok'}), 200


@app.route('/api/health')
def api_health():
    """Readiness probe including a lightweight database check."""
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'ok', 'database': 'connected'}), 200
    except Exception as exc:
        app.logger.error("Health check DB query failed: %s", exc)
        return jsonify({'status': 'degraded', 'database': 'unavailable'}), 503
    finally:
        db.session.remove()


# ============================================================================
# ADMIN ROUTES
# ============================================================================

@app.route('/admin')
@auth_required
@admin_required
def admin_dashboard():
    """Render admin dashboard"""
    return render_template('admin.html')


@app.route('/api/admin/stats', methods=['GET'])
@auth_required
@admin_required
def admin_stats():
    """Get user statistics"""
    try:
        stats = AdminService.get_user_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/users', methods=['GET'])
@auth_required
@admin_required
def admin_users():
    """Get users with filtering and pagination"""
    try:
        status = request.args.get('status', None)
        search = request.args.get('search', None)
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))

        users, total = AdminService.get_users(status=status, search=search, limit=limit, offset=offset)

        return jsonify({
            'users': users,
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/users/<user_id>', methods=['GET'])
@auth_required
@admin_required
def admin_user_detail(user_id):
    """Get user details and history"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        history = AdminService.get_user_history(user_id)

        return jsonify({
            'user': user.to_dict(include_sensitive=True),
            'history': history
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/users/<user_id>/approve', methods=['POST'])
@auth_required
@admin_required
def admin_approve_user(user_id):
    """Approve a pending user"""
    try:
        admin = get_current_user()
        success, message = AdminService.approve_user(user_id, admin.id)

        if success:
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/users/<user_id>/reject', methods=['POST'])
@auth_required
@admin_required
def admin_reject_user(user_id):
    """Reject a pending user"""
    try:
        data = request.json
        reason = data.get('reason', '')
        admin = get_current_user()

        success, message = AdminService.reject_user(user_id, admin.id, reason)

        if success:
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/users/<user_id>/revoke', methods=['POST'])
@auth_required
@admin_required
def admin_revoke_user(user_id):
    """Revoke user access"""
    try:
        admin = get_current_user()
        success, message = AdminService.revoke_access(user_id, admin.id)

        if success:
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/users/<user_id>/restore', methods=['POST'])
@auth_required
@admin_required
def admin_restore_user(user_id):
    """Restore user access"""
    try:
        admin = get_current_user()
        success, message = AdminService.restore_access(user_id, admin.id)

        if success:
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/users/<user_id>/suspend', methods=['POST'])
@auth_required
@admin_required
def admin_suspend_user(user_id):
    """Suspend user account"""
    try:
        admin = get_current_user()
        success, message = AdminService.suspend_user(user_id, admin.id)

        if success:
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/users/<user_id>/logout', methods=['POST'])
@auth_required
@admin_required
def admin_logout_user(user_id):
    """Force logout user sessions"""
    try:
        admin = get_current_user()
        success, message = AdminService.logout_user_sessions(user_id, admin.id)

        if success:
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/audit-log', methods=['GET'])
@auth_required
@admin_required
def admin_audit_log():
    """Get audit log entries"""
    try:
        action = request.args.get('action', None)
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        logs, total = AdminService.get_audit_log(action=action, limit=limit, offset=offset)

        return jsonify({
            'logs': logs,
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# PROTECTED APPLICATION ROUTES
# ============================================================================

@app.route('/')
def index():
    """Render main application page (requires authentication)"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        token = request.cookies.get('auth_token')

    if token:
        valid, user = AuthService.verify_session(token)
        if valid and user:
            return render_template('index.html')

    return redirect(url_for('login_page'))


@app.route('/api/validate', methods=['POST'])
@auth_required
def validate_content():
    """Validate title, content, and airline list before generation"""
    try:
        data = request.json
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        airlines = data.get('airlines', [])
        replacement_mode = data.get('replacementMode', 'placeholder')
        original_name = data.get('originalName', '').strip()

        result = validation_service.validate(
            title=title,
            content=content,
            airlines=airlines,
            replacement_mode=replacement_mode,
            original_name=original_name
        )

        return jsonify(result)
    except Exception as e:
        return jsonify({'valid': False, 'errors': [str(e)]}), 400


@app.route('/api/preview', methods=['POST'])
@auth_required
def preview_content():
    """Generate preview for a single airline"""
    try:
        data = request.json
        title = data.get('title', '')
        content = data.get('content', '')
        airline = data.get('airline', '')
        replacement_mode = data.get('replacementMode', 'placeholder')
        original_name = data.get('originalName', '')
        case_sensitive = data.get('caseSensitive', False)

        preview_result = replacement_service.generate_preview(
            title=title,
            content=content,
            airline=airline,
            replacement_mode=replacement_mode,
            original_name=original_name,
            case_sensitive=case_sensitive
        )

        return jsonify(preview_result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/generate', methods=['POST'])
@auth_required
def generate_content():
    """Generate content for all airlines"""
    try:
        data = request.json
        title = data.get('title', '')
        content = data.get('content', '')
        airlines = data.get('airlines', [])
        replacement_mode = data.get('replacementMode', 'placeholder')
        original_name = data.get('originalName', '')
        case_sensitive = data.get('caseSensitive', False)
        output_mode = data.get('outputMode', 'posts')

        results = replacement_service.generate_all(
            title=title,
            content=content,
            airlines=airlines,
            replacement_mode=replacement_mode,
            original_name=original_name,
            case_sensitive=case_sensitive
        )

        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/generate-pdf', methods=['POST'])
@auth_required
def generate_single_pdf():
    """Generate a single PDF for one airline"""
    try:
        data = request.json
        airline = data.get('airline', '')
        title = data.get('title', '')
        content = data.get('content', '')
        settings = data.get('settings', {})

        pdf_buffer = pdf_generator.generate_pdf(
            airline=airline,
            title=title,
            content=content,
            page_size=settings.get('pageSize', 'A4'),
            orientation=settings.get('orientation', 'portrait'),
            font_size=settings.get('fontSize', 11),
            margin=settings.get('margin', 50)
        )

        filename = pdf_generator.sanitize_filename(f"{airline}.pdf")

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 400



@app.route('/api/generate-bulk-pdfs', methods=['POST'])
@auth_required
def generate_bulk_pdfs():
    """Generate PDFs for all airlines and return as ZIP."""
    try:
        data = request.json or {}
        results = data.get('results', [])
        settings = data.get('settings', {})

        documents = [
            {
                "airline": result.get("airline", ""),
                "title": result.get("generatedTitle", ""),
                "content": result.get("generatedContent", ""),
                "page_size": settings.get("pageSize", "A4"),
                "orientation": settings.get("orientation", "portrait"),
                "font_size": settings.get("fontSize", 11),
                "margin": settings.get("margin", 10),
            }
            for result in results
        ]

        # Generate each PDF once using the shared browser.
        pdf_buffers = pdf_generator.generate_pdfs(documents)

        # Create ZIP file in memory.
        zip_buffer = BytesIO()

        with zipfile.ZipFile(
            zip_buffer, 'w', zipfile.ZIP_DEFLATED
        ) as zip_file:
            for result, pdf_buffer in zip(results, pdf_buffers):
                airline = result.get('airline', '')
                filename = pdf_generator.sanitize_filename(
                    f"{airline}.pdf"
                )
                zip_file.writestr(filename, pdf_buffer.getvalue())

        zip_buffer.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'cargo_pdfs_{timestamp}.zip'
        )

    except Exception as e:
        app.logger.exception("Bulk PDF generation failed")
        return jsonify({'error': str(e)}), 400


@app.route('/api/parse-airlines', methods=['POST'])
@auth_required
def parse_airlines():
    """Parse airline list from text or CSV file"""
    try:
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                content = file.read().decode('utf-8')
                airlines = validation_service.parse_airline_list(content)
                return jsonify({'success': True, 'airlines': airlines})

        text = request.form.get('text', '')
        airlines = validation_service.parse_airline_list(text)

        return jsonify({'success': True, 'airlines': airlines})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/templates', methods=['GET'])
@auth_required
def get_templates():
    """Get all saved templates"""
    try:
        templates = template_manager.get_all_templates()
        return jsonify({'success': True, 'templates': templates})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/templates', methods=['POST'])
@auth_required
def save_template():
    """Save a new template"""
    try:
        data = request.json
        template_id = template_manager.save_template(data)
        return jsonify({'success': True, 'templateId': template_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/templates/<template_id>', methods=['GET'])
@auth_required
def get_template(template_id):
    """Get a specific template"""
    try:
        template = template_manager.get_template(template_id)
        if template:
            return jsonify({'success': True, 'template': template})
        else:
            return jsonify({'success': False, 'error': 'Template not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/templates/<template_id>', methods=['DELETE'])
@auth_required
def delete_template(template_id):
    """Delete a template"""
    try:
        success = template_manager.delete_template(template_id)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Template not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error. Please try again.'}), 500


# ============================================================================
# CONTEXT PROCESSORS
# ============================================================================

@app.context_processor
def inject_user():
    """Inject current user into template context"""
    user = get_current_user()
    return {'current_user': user}


# # if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
#     app.run(debug=True, host='0.0.0.0', port=5000)

def _init_database_with_retry(max_attempts=5, base_delay=2):
    """Create tables + seed admin, retrying on Neon cold-start connection errors."""
    import time

    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            with app.app_context():
                db.create_all()

                admin_email = os.environ.get(
                    "ADMIN_EMAIL", "dmtoravi@gmail.com"
                ).strip().lower()

                admin_password = os.environ.get("ADMIN_PASSWORD")

                if admin_password and User.query.count() == 0:
                    admin = User(
                        email=admin_email,
                        full_name="Administrator",
                        password_hash=AuthService.hash_password(admin_password),
                        account_status="approved",
                        is_admin=True
                    )
                    db.session.add(admin)
                    db.session.commit()
                    app.logger.info("Initial admin account created")
            return
        except Exception as exc:
            last_error = exc
            delay = base_delay * attempt
            app.logger.warning(
                "Database init attempt %d/%d failed (%s); retrying in %ds",
                attempt, max_attempts, exc, delay
            )
            db.session.remove()
            time.sleep(delay)

    raise last_error


_init_database_with_retry()

if __name__ == '__main__':
    # Render/Heroku style: honor $PORT, fall back to 5000 for local dev
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes')
    app.run(
        debug=debug,
        host='0.0.0.0',
        port=port,
    )