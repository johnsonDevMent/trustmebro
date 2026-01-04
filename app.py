"""
TRUSTMEBRO Flask Application
Main application file with all routes and business logic
"""

import os
import sqlite3
import hashlib
import secrets
import json
import re
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file, g
from werkzeug.security import generate_password_hash, check_password_hash

from paper_generator import PaperGenerator
from chart_generator import ChartGenerator
from pdf_generator import PDFGenerator

# =============================================================================
# APP FACTORY
# =============================================================================

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    app.config['DATABASE'] = os.path.join(app.instance_path, 'trustmebro.db')
    
    # Security settings
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    
    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'charts'), exist_ok=True)
    
    # Initialize database
    init_db(app)
    
    # Register routes
    register_routes(app)
    
    return app


# Rate limiting storage (simple in-memory, use Redis in production)
rate_limit_store = {}

def check_rate_limit(key, max_requests=10, window_seconds=60):
    """Simple rate limiting check"""
    now = datetime.now()
    window_start = now - timedelta(seconds=window_seconds)
    
    if key not in rate_limit_store:
        rate_limit_store[key] = []
    
    # Clean old entries
    rate_limit_store[key] = [t for t in rate_limit_store[key] if t > window_start]
    
    if len(rate_limit_store[key]) >= max_requests:
        return False
    
    rate_limit_store[key].append(now)
    return True

# =============================================================================
# DATABASE
# =============================================================================

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app):
    """Initialize database with all tables"""
    db_path = app.config['DATABASE']
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_admin INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0
        )
    ''')
    
    # Papers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id TEXT UNIQUE NOT NULL,
            fingerprint TEXT UNIQUE NOT NULL,
            claim TEXT NOT NULL,
            template TEXT NOT NULL,
            length TEXT NOT NULL,
            voice TEXT NOT NULL,
            tone TEXT NOT NULL,
            chart_count INTEGER NOT NULL,
            lock_seed INTEGER DEFAULT 0,
            title TEXT NOT NULL,
            authors TEXT NOT NULL,
            affiliations TEXT NOT NULL,
            abstract TEXT NOT NULL,
            introduction TEXT,
            methods TEXT,
            results TEXT,
            discussion TEXT,
            limitations TEXT NOT NULL,
            references_json TEXT NOT NULL,
            chart_data_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Share tokens table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS share_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            paper_id TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (paper_id) REFERENCES papers(paper_id)
        )
    ''')
    
    # Gallery posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gallery_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT UNIQUE NOT NULL,
            paper_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            vote_count INTEGER DEFAULT 0,
            is_hidden INTEGER DEFAULT 0,
            is_deleted INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deleted_at TIMESTAMP,
            FOREIGN KEY (paper_id) REFERENCES papers(paper_id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Votes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            vote_value INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(post_id, user_id),
            FOREIGN KEY (post_id) REFERENCES gallery_posts(post_id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Reports table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT NOT NULL,
            user_id INTEGER,
            reason TEXT NOT NULL,
            notes TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TIMESTAMP,
            reviewed_by INTEGER,
            FOREIGN KEY (post_id) REFERENCES gallery_posts(post_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (reviewed_by) REFERENCES users(id)
        )
    ''')
    
    # Moderation log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS moderation_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            target_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            admin_id INTEGER NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES users(id)
        )
    ''')
    
    # Blocked keywords table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocked_keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')
    
    # Insert default blocked keywords
    default_keywords = ['hate', 'kill', 'murder', 'terrorist', 'bomb']
    for kw in default_keywords:
        cursor.execute('INSERT OR IGNORE INTO blocked_keywords (keyword) VALUES (?)', (kw,))
    
    conn.commit()
    conn.close()

# =============================================================================
# HELPERS
# =============================================================================

from flask import current_app

def get_database():
    """Get database connection"""
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

def login_required(f):
    """Decorator for routes that require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator for routes that require admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        db = get_database()
        user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        if not user or not user['is_admin']:
            flash('Admin access required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def generate_paper_id():
    """Generate a unique paper ID like TMB-8F21C"""
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    suffix = ''.join(secrets.choice(chars) for _ in range(5))
    return f'TMB-{suffix}'

def generate_fingerprint(claim, template, length, voice, tone, chart_count, lock_seed):
    """Generate deterministic fingerprint for paper reuse"""
    normalized_claim = ' '.join(claim.lower().split())
    data = f"{normalized_claim}|{template}|{length}|{voice}|{tone}|{chart_count}|{lock_seed}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]

def check_blocked_keywords(text):
    """Check if text contains blocked keywords"""
    db = get_database()
    keywords = db.execute('SELECT keyword FROM blocked_keywords').fetchall()
    text_lower = text.lower()
    for kw in keywords:
        if kw['keyword'].lower() in text_lower:
            return True, kw['keyword']
    return False, None

def check_auto_hide(post_id):
    """Check if post should be auto-hidden based on reports"""
    db = get_database()
    
    # Count reports in last 60 minutes
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    reports_1h = db.execute('''
        SELECT COUNT(DISTINCT user_id) as count FROM reports 
        WHERE post_id = ? AND created_at > ? AND status = 'pending'
    ''', (post_id, one_hour_ago)).fetchone()['count']
    
    # Count reports in last 24 hours
    one_day_ago = datetime.utcnow() - timedelta(hours=24)
    reports_24h = db.execute('''
        SELECT COUNT(DISTINCT user_id) as count FROM reports 
        WHERE post_id = ? AND created_at > ? AND status = 'pending'
    ''', (post_id, one_day_ago)).fetchone()['count']
    
    # Auto-hide if 5+ reports in 1 hour OR quarantine if 3+ in 1 hour or 6+ in 24 hours
    if reports_1h >= 5:
        db.execute('UPDATE gallery_posts SET is_hidden = 1 WHERE post_id = ?', (post_id,))
        db.commit()
        return 'hidden'
    elif reports_1h >= 3 or reports_24h >= 6:
        return 'quarantine'
    
    return None

# =============================================================================
# ROUTES
# =============================================================================

def register_routes(app):
    
    @app.teardown_appcontext
    def teardown_db(exception):
        close_db()
    
    @app.context_processor
    def inject_user():
        """Inject user info into all templates"""
        user = None
        if 'user_id' in session:
            db = get_database()
            user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        return dict(current_user=user)
    
    # =========================================================================
    # MAIN PAGES
    # =========================================================================
    
    @app.route('/')
    def index():
        """Landing / Generate page"""
        groq_key = session.get('groq_key', '')
        return render_template('index.html', groq_key_set=bool(groq_key))
    
    @app.route('/generate', methods=['POST'])
    def generate():
        """Generate a parody paper"""
        claim = request.form.get('claim', '').strip()
        template = request.form.get('template', 'journal')
        length = request.form.get('length', 'abstract')
        voice = request.form.get('voice', 'naija')
        tone = request.form.get('tone', 'deadpan')
        chart_count = int(request.form.get('chart_count', 1))
        lock_seed = request.form.get('lock_seed') == 'on'
        groq_key = request.form.get('groq_key', '') or session.get('groq_key', '')
        
        # Validate claim
        if not claim:
            flash('Please enter a claim.', 'error')
            return redirect(url_for('index'))
        
        if len(claim) > 500:
            flash('Claim is too long. Maximum 500 characters.', 'error')
            return redirect(url_for('index'))
        
        # Check for blocked keywords
        is_blocked, keyword = check_blocked_keywords(claim)
        if is_blocked:
            flash('Your claim contains content that is not allowed.', 'error')
            return redirect(url_for('index'))
        
        # Check if short/full requires Groq key
        if length in ['short', 'full'] and not groq_key:
            flash('Short and Full papers require a Groq API key.', 'warning')
            return redirect(url_for('index'))
        
        # Save Groq key to session if provided
        if groq_key:
            session['groq_key'] = groq_key
        
        # Generate fingerprint and check for existing paper
        fingerprint = generate_fingerprint(claim, template, length, voice, tone, chart_count, lock_seed)
        
        db = get_database()
        existing = db.execute('SELECT * FROM papers WHERE fingerprint = ?', (fingerprint,)).fetchone()
        
        if existing:
            return redirect(url_for('paper_view', paper_id=existing['paper_id']))
        
        # Generate new paper
        generator = PaperGenerator(groq_key if groq_key else None)
        
        try:
            paper_data = generator.generate(
                claim=claim,
                template=template,
                length=length,
                voice=voice,
                tone=tone,
                chart_count=chart_count,
                lock_seed=lock_seed
            )
        except Exception as e:
            flash(f'Error generating paper: {str(e)}', 'error')
            return redirect(url_for('index'))
        
        # Generate charts
        chart_gen = ChartGenerator()
        chart_files = []
        for i, chart_data in enumerate(paper_data['charts']):
            chart_filename = f"{paper_data['id']}_{i}.png"
            chart_path = os.path.join(app.static_folder, 'charts', chart_filename)
            chart_gen.generate_chart(chart_data, chart_path)
            chart_files.append(chart_filename)
        
        paper_data['chart_files'] = chart_files
        
        # Save to database
        user_id = session.get('user_id')
        
        db.execute('''
            INSERT INTO papers (
                paper_id, fingerprint, claim, template, length, voice, tone, 
                chart_count, lock_seed, title, authors, affiliations, abstract,
                introduction, methods, results, discussion, limitations,
                references_json, chart_data_json, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            paper_data['id'], fingerprint, claim, template, length, voice, tone,
            chart_count, 1 if lock_seed else 0, paper_data['title'],
            json.dumps(paper_data['authors']), json.dumps(paper_data['affiliations']),
            paper_data['abstract'], paper_data.get('introduction'),
            paper_data.get('methods'), paper_data.get('results'),
            paper_data.get('discussion'), paper_data['limitations'],
            json.dumps(paper_data['references']), json.dumps(paper_data['charts']),
            user_id
        ))
        db.commit()
        
        return redirect(url_for('paper_view', paper_id=paper_data['id']))
    
    @app.route('/paper/<paper_id>')
    def paper_view(paper_id):
        """View a generated paper"""
        db = get_database()
        paper = db.execute('SELECT * FROM papers WHERE paper_id = ?', (paper_id,)).fetchone()
        
        if not paper:
            flash('Paper not found.', 'error')
            return redirect(url_for('index'))
        
        # Parse JSON fields
        paper_dict = dict(paper)
        paper_dict['authors'] = json.loads(paper['authors'])
        paper_dict['affiliations'] = json.loads(paper['affiliations'])
        paper_dict['references'] = json.loads(paper['references_json'])
        paper_dict['charts'] = json.loads(paper['chart_data_json'])
        
        # Get chart files
        chart_files = []
        for i in range(paper['chart_count']):
            chart_files.append(f"{paper_id}_{i}.png")
        paper_dict['chart_files'] = chart_files
        
        # Check if user owns this paper
        is_owner = session.get('user_id') == paper['user_id'] if paper['user_id'] else False
        
        # Check if already published
        gallery_post = db.execute(
            'SELECT * FROM gallery_posts WHERE paper_id = ? AND is_deleted = 0', 
            (paper_id,)
        ).fetchone()
        
        return render_template('paper.html', paper=paper_dict, is_owner=is_owner, gallery_post=gallery_post)
    
    @app.route('/share/<token>')
    def share_view(token):
        """View a shared paper via token"""
        db = get_database()
        share = db.execute(
            'SELECT * FROM share_tokens WHERE token = ?', 
            (token,)
        ).fetchone()
        
        if not share:
            return render_template('share_expired.html', reason='not_found')
        
        # Check expiry
        expires_at = datetime.fromisoformat(share['expires_at'])
        if datetime.utcnow() > expires_at:
            return render_template('share_expired.html', reason='expired', expires_at=expires_at)
        
        # Get paper
        paper = db.execute(
            'SELECT * FROM papers WHERE paper_id = ?', 
            (share['paper_id'],)
        ).fetchone()
        
        if not paper:
            return render_template('share_expired.html', reason='not_found')
        
        # Parse JSON fields
        paper_dict = dict(paper)
        paper_dict['authors'] = json.loads(paper['authors'])
        paper_dict['affiliations'] = json.loads(paper['affiliations'])
        paper_dict['references'] = json.loads(paper['references_json'])
        paper_dict['charts'] = json.loads(paper['chart_data_json'])
        
        # Get chart files
        chart_files = []
        for i in range(paper['chart_count']):
            chart_files.append(f"{paper['paper_id']}_{i}.png")
        paper_dict['chart_files'] = chart_files
        
        return render_template('share.html', paper=paper_dict, expires_at=expires_at, token=token)
    
    @app.route('/create_share/<paper_id>', methods=['POST'])
    def create_share(paper_id):
        """Create a share link for a paper"""
        db = get_database()
        paper = db.execute('SELECT * FROM papers WHERE paper_id = ?', (paper_id,)).fetchone()
        
        if not paper:
            return jsonify({'error': 'Paper not found'}), 404
        
        # Generate token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=48)
        
        db.execute(
            'INSERT INTO share_tokens (token, paper_id, expires_at) VALUES (?, ?, ?)',
            (token, paper_id, expires_at.isoformat())
        )
        db.commit()
        
        share_url = url_for('share_view', token=token, _external=True)
        
        return jsonify({
            'url': share_url,
            'expires_at': expires_at.isoformat(),
            'token': token
        })
    
    @app.route('/download_pdf/<paper_id>')
    def download_pdf(paper_id):
        """Download paper as PDF"""
        db = get_database()
        paper = db.execute('SELECT * FROM papers WHERE paper_id = ?', (paper_id,)).fetchone()
        
        if not paper:
            flash('Paper not found.', 'error')
            return redirect(url_for('index'))
        
        # Parse JSON fields
        paper_dict = dict(paper)
        paper_dict['authors'] = json.loads(paper['authors'])
        paper_dict['affiliations'] = json.loads(paper['affiliations'])
        paper_dict['references'] = json.loads(paper['references_json'])
        paper_dict['charts'] = json.loads(paper['chart_data_json'])
        
        # Get chart files
        chart_files = []
        for i in range(paper['chart_count']):
            chart_path = os.path.join(app.static_folder, 'charts', f"{paper_id}_{i}.png")
            chart_files.append(chart_path)
        paper_dict['chart_files'] = chart_files
        
        # Generate PDF
        pdf_gen = PDFGenerator()
        pdf_path = os.path.join(app.instance_path, f'{paper_id}.pdf')
        pdf_gen.generate(paper_dict, pdf_path)
        
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f'TRUSTMEBRO_{paper_id}.pdf',
            mimetype='application/pdf'
        )
    
    @app.route('/download_image/<paper_id>')
    def download_image(paper_id):
        """Download paper preview as PNG for social sharing"""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
        
        db = get_database()
        paper = db.execute('SELECT * FROM papers WHERE paper_id = ?', (paper_id,)).fetchone()
        
        if not paper:
            flash('Paper not found.', 'error')
            return redirect(url_for('index'))
        
        # Create Instagram-friendly square image (1080x1080)
        fig, ax = plt.subplots(figsize=(10.8, 10.8), dpi=100)
        fig.patch.set_facecolor('#FAF8F5')
        ax.set_xlim(0, 10.8)
        ax.set_ylim(0, 10.8)
        ax.axis('off')
        
        # Header stripe
        header = Rectangle((0, 9.3), 10.8, 1.5, color='#C85A28')
        ax.add_patch(header)
        
        # Brand
        ax.text(0.6, 10.3, 'TRUSTMEBRO', fontsize=32, fontweight='bold', color='white', 
                family='serif')
        ax.text(0.6, 9.7, 'Journal of Unverified Claims', fontsize=14, color='white', 
                style='italic', family='serif')
        
        # Parody badge
        ax.text(10.2, 10.0, '[PARODY]', fontsize=12, fontweight='bold', color='white', 
                ha='right')
        
        # Title - word wrap manually
        title = paper['title']
        words = title.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if len(' '.join(current_line)) > 45:
                if len(current_line) > 1:
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(' '.join(current_line))
                    current_line = []
        if current_line:
            lines.append(' '.join(current_line))
        
        title_y = 8.6
        for i, line in enumerate(lines[:3]):  # Max 3 lines
            ax.text(0.6, title_y - i*0.6, line, fontsize=22, fontweight='bold', color='#2C1810',
                    family='serif')
        
        # Authors
        authors = json.loads(paper['authors'])
        ax.text(0.6, 6.8, ', '.join(authors), fontsize=13, color='#666', 
                style='italic', family='serif')
        
        # Fictional Authors badge
        ax.text(0.6, 6.4, 'FICTIONAL AUTHORS', fontsize=10, fontweight='bold', 
                color='#C85A28', family='sans-serif',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF5F0', edgecolor='#C85A28'))
        
        # Abstract box
        abstract_box = Rectangle((0.4, 1.8), 10, 4.2, color='white', ec='#ddd', linewidth=1)
        ax.add_patch(abstract_box)
        
        ax.text(0.6, 5.7, 'Abstract', fontsize=14, fontweight='bold', color='#C85A28',
                family='serif')
        
        # Abstract text - word wrap
        abstract = paper['abstract']
        words = abstract.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if len(' '.join(current_line)) > 70:
                if len(current_line) > 1:
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(' '.join(current_line))
                    current_line = []
        if current_line:
            lines.append(' '.join(current_line))
        
        abstract_y = 5.3
        for i, line in enumerate(lines[:8]):  # Max 8 lines
            ax.text(0.6, abstract_y - i*0.42, line, fontsize=11, color='#444',
                    family='serif')
        if len(lines) > 8:
            ax.text(0.6, abstract_y - 8*0.42, '...', fontsize=11, color='#444', family='serif')
        
        # Study ID at bottom
        ax.text(0.6, 1.0, f'Study ID: {paper_id}', fontsize=11, color='#999',
                family='monospace')
        
        # Fictional notice at bottom right
        ax.text(10.2, 1.0, 'ALL DATA IS FICTIONAL', fontsize=11, fontweight='bold', 
                color='#B22222', ha='right')
        
        # Bottom stripe
        bottom = Rectangle((0, 0), 10.8, 0.6, color='#C85A28')
        ax.add_patch(bottom)
        ax.text(5.4, 0.25, 'THIS IS SATIRE - DO NOT CITE AS REAL RESEARCH', 
                fontsize=10, fontweight='bold', color='white', ha='center', family='sans-serif')
        
        # Watermark
        ax.text(5.4, 4, 'TRUSTMEBRO', fontsize=70, color='#C85A28', alpha=0.04,
                ha='center', va='center', rotation=30, family='serif')
        
        # Save
        img_path = os.path.join(app.instance_path, f'{paper_id}_social.png')
        plt.savefig(img_path, dpi=100, bbox_inches='tight', facecolor='#FAF8F5',
                   edgecolor='none', pad_inches=0)
        plt.close()
        
        return send_file(
            img_path,
            as_attachment=True,
            download_name=f'TRUSTMEBRO_{paper_id}.png',
            mimetype='image/png'
        )
    
    # =========================================================================
    # GALLERY
    # =========================================================================
    
    @app.route('/gallery')
    def gallery():
        """Public gallery"""
        db = get_database()
        
        tab = request.args.get('tab', 'trending')
        voice_filter = request.args.get('voice', 'all')
        template_filter = request.args.get('template', 'all')
        
        # Base query
        query = '''
            SELECT gp.*, p.title, p.claim, p.template, p.voice, p.abstract, p.chart_count, p.paper_id as pid
            FROM gallery_posts gp
            JOIN papers p ON gp.paper_id = p.paper_id
            WHERE gp.is_hidden = 0 AND gp.is_deleted = 0
        '''
        params = []
        
        # Apply filters
        if voice_filter != 'all':
            query += ' AND p.voice = ?'
            params.append(voice_filter)
        
        if template_filter != 'all':
            query += ' AND p.template = ?'
            params.append(template_filter)
        
        # Sort
        if tab == 'trending':
            # Time-decayed scoring: votes / (age_hours + 2)^1.5
            query += '''
                ORDER BY (gp.vote_count + 1.0) / 
                    POWER((julianday('now') - julianday(gp.created_at)) * 24 + 2, 1.5) DESC
            '''
        else:  # new
            query += ' ORDER BY gp.created_at DESC'
        
        query += ' LIMIT 50'
        
        posts = db.execute(query, params).fetchall()
        
        # Get user's votes if logged in
        user_votes = {}
        if 'user_id' in session:
            votes = db.execute(
                'SELECT post_id, vote_value FROM votes WHERE user_id = ?',
                (session['user_id'],)
            ).fetchall()
            user_votes = {v['post_id']: v['vote_value'] for v in votes}
        
        return render_template('gallery.html', 
                               posts=posts, 
                               tab=tab, 
                               voice_filter=voice_filter,
                               template_filter=template_filter,
                               user_votes=user_votes)
    
    @app.route('/g/<post_id>')
    def gallery_post(post_id):
        """View a gallery post"""
        db = get_database()
        
        post = db.execute('''
            SELECT gp.*, p.*, u.username as author_name
            FROM gallery_posts gp
            JOIN papers p ON gp.paper_id = p.paper_id
            JOIN users u ON gp.user_id = u.id
            WHERE gp.post_id = ? AND gp.is_deleted = 0
        ''', (post_id,)).fetchone()
        
        if not post:
            flash('Post not found.', 'error')
            return redirect(url_for('gallery'))
        
        if post['is_hidden'] and session.get('user_id') != post['user_id']:
            # Check if admin
            user = None
            if 'user_id' in session:
                user = db.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],)).fetchone()
            if not user or not user['is_admin']:
                flash('This post is not available.', 'error')
                return redirect(url_for('gallery'))
        
        # Parse JSON fields
        post_dict = dict(post)
        post_dict['authors'] = json.loads(post['authors'])
        post_dict['affiliations'] = json.loads(post['affiliations'])
        post_dict['references'] = json.loads(post['references_json'])
        post_dict['charts'] = json.loads(post['chart_data_json'])
        
        # Get chart files
        chart_files = []
        for i in range(post['chart_count']):
            chart_files.append(f"{post['paper_id']}_{i}.png")
        post_dict['chart_files'] = chart_files
        
        # Get user's vote
        user_vote = None
        if 'user_id' in session:
            vote = db.execute(
                'SELECT vote_value FROM votes WHERE post_id = ? AND user_id = ?',
                (post_id, session['user_id'])
            ).fetchone()
            if vote:
                user_vote = vote['vote_value']
        
        return render_template('gallery_post.html', post=post_dict, user_vote=user_vote)
    
    @app.route('/publish/<paper_id>', methods=['POST'])
    @login_required
    def publish(paper_id):
        """Publish a paper to gallery"""
        db = get_database()
        
        # Check paper exists
        paper = db.execute('SELECT * FROM papers WHERE paper_id = ?', (paper_id,)).fetchone()
        if not paper:
            flash('Paper not found.', 'error')
            return redirect(url_for('index'))
        
        # Check not already published
        existing = db.execute(
            'SELECT * FROM gallery_posts WHERE paper_id = ? AND is_deleted = 0',
            (paper_id,)
        ).fetchone()
        if existing:
            flash('This paper is already published.', 'info')
            return redirect(url_for('gallery_post', post_id=existing['post_id']))
        
        # Check policy agreement
        if not request.form.get('agree_policy'):
            flash('You must agree to the parody policy to publish.', 'warning')
            return redirect(url_for('paper_view', paper_id=paper_id))
        
        # Create gallery post
        post_id = secrets.token_urlsafe(8)
        
        db.execute('''
            INSERT INTO gallery_posts (post_id, paper_id, user_id) 
            VALUES (?, ?, ?)
        ''', (post_id, paper_id, session['user_id']))
        db.commit()
        
        flash('Paper published to gallery!', 'success')
        return redirect(url_for('gallery_post', post_id=post_id))
    
    @app.route('/vote/<post_id>', methods=['POST'])
    @login_required
    def vote(post_id):
        """Vote on a gallery post with rate limiting"""
        # Rate limit: 30 votes per user per minute
        user_id = session.get('user_id')
        if not check_rate_limit(f"vote:{user_id}", max_requests=30, window_seconds=60):
            return jsonify({'error': 'Too many votes. Please slow down.'}), 429
        
        db = get_database()
        
        vote_value = int(request.form.get('vote', 0))
        if vote_value not in [-1, 1]:
            return jsonify({'error': 'Invalid vote'}), 400
        
        # Check post exists
        post = db.execute(
            'SELECT * FROM gallery_posts WHERE post_id = ? AND is_deleted = 0',
            (post_id,)
        ).fetchone()
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        # Check existing vote
        existing = db.execute(
            'SELECT * FROM votes WHERE post_id = ? AND user_id = ?',
            (post_id, session['user_id'])
        ).fetchone()
        
        if existing:
            if existing['vote_value'] == vote_value:
                # Remove vote
                db.execute(
                    'DELETE FROM votes WHERE post_id = ? AND user_id = ?',
                    (post_id, session['user_id'])
                )
                vote_change = -vote_value
            else:
                # Change vote
                db.execute(
                    'UPDATE votes SET vote_value = ? WHERE post_id = ? AND user_id = ?',
                    (vote_value, post_id, session['user_id'])
                )
                vote_change = vote_value * 2
        else:
            # New vote
            db.execute(
                'INSERT INTO votes (post_id, user_id, vote_value) VALUES (?, ?, ?)',
                (post_id, session['user_id'], vote_value)
            )
            vote_change = vote_value
        
        # Update vote count
        db.execute(
            'UPDATE gallery_posts SET vote_count = vote_count + ? WHERE post_id = ?',
            (vote_change, post_id)
        )
        db.commit()
        
        # Get new count
        new_count = db.execute(
            'SELECT vote_count FROM gallery_posts WHERE post_id = ?',
            (post_id,)
        ).fetchone()['vote_count']
        
        return jsonify({'vote_count': new_count, 'user_vote': vote_value if not existing or existing['vote_value'] != vote_value else 0})
    
    @app.route('/report/<post_id>', methods=['POST'])
    def report(post_id):
        """Report a gallery post"""
        db = get_database()
        
        reason = request.form.get('reason', '')
        notes = request.form.get('notes', '')
        
        if not reason:
            flash('Please select a reason.', 'warning')
            return redirect(url_for('gallery_post', post_id=post_id))
        
        user_id = session.get('user_id')
        
        db.execute('''
            INSERT INTO reports (post_id, user_id, reason, notes) 
            VALUES (?, ?, ?, ?)
        ''', (post_id, user_id, reason, notes))
        db.commit()
        
        # Check auto-hide
        check_auto_hide(post_id)
        
        flash('Report submitted. Thank you for helping keep the community safe.', 'success')
        return redirect(url_for('gallery_post', post_id=post_id))
    
    # =========================================================================
    # AUTH
    # =========================================================================
    
    @app.route('/auth')
    def auth():
        """Auth page"""
        next_url = request.args.get('next', '')
        return render_template('auth.html', next_url=next_url)
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Login with rate limiting"""
        if request.method == 'GET':
            return redirect(url_for('auth'))
        
        # Rate limit: 10 login attempts per IP per 15 minutes
        client_ip = request.remote_addr
        if not check_rate_limit(f"login:{client_ip}", max_requests=10, window_seconds=900):
            flash('Too many login attempts. Please try again in 15 minutes.', 'error')
            return redirect(url_for('auth'))
        
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        next_url = request.form.get('next', '')
        
        if not username or not password:
            flash('Please enter username and password.', 'warning')
            return redirect(url_for('auth'))
        
        db = get_database()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if not user or not check_password_hash(user['password_hash'], password):
            flash('Invalid username or password.', 'error')
            return redirect(url_for('auth'))
        
        if user['is_banned']:
            flash('This account has been banned.', 'error')
            return redirect(url_for('auth'))
        
        session['user_id'] = user['id']
        session['username'] = user['username']
        flash(f'Welcome back, {username}!', 'success')
        
        if next_url:
            return redirect(next_url)
        return redirect(url_for('index'))
    
    @app.route('/signup', methods=['POST'])
    def signup():
        """Sign up with rate limiting"""
        # Rate limit: 5 signups per IP per hour
        client_ip = request.remote_addr
        if not check_rate_limit(f"signup:{client_ip}", max_requests=5, window_seconds=3600):
            flash('Too many signup attempts. Please try again later.', 'error')
            return redirect(url_for('auth'))
        
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        next_url = request.form.get('next', '')
        
        if not username or not password:
            flash('Please enter username and password.', 'warning')
            return redirect(url_for('auth'))
        
        if len(username) < 3 or len(username) > 20:
            flash('Username must be 3-20 characters.', 'warning')
            return redirect(url_for('auth'))
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            flash('Username can only contain letters, numbers, and underscores.', 'warning')
            return redirect(url_for('auth'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'warning')
            return redirect(url_for('auth'))
        
        if password != confirm:
            flash('Passwords do not match.', 'warning')
            return redirect(url_for('auth'))
        
        db = get_database()
        existing = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if existing:
            flash('Username already taken.', 'error')
            return redirect(url_for('auth'))
        
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        db.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, password_hash)
        )
        db.commit()
        
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        session['user_id'] = user['id']
        session['username'] = user['username']
        
        flash(f'Welcome to TRUSTMEBRO, {username}!', 'success')
        
        if next_url:
            return redirect(next_url)
        return redirect(url_for('index'))
    
    @app.route('/logout')
    def logout():
        """Logout"""
        session.clear()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))
    
    @app.route('/save_groq_key', methods=['POST'])
    def save_groq_key():
        """Save Groq API key to session"""
        groq_key = request.form.get('groq_key', '').strip()
        if groq_key:
            session['groq_key'] = groq_key
            return jsonify({'success': True})
        return jsonify({'error': 'No key provided'}), 400
    
    # =========================================================================
    # POLICY
    # =========================================================================
    
    @app.route('/policy')
    def policy():
        """Policy page"""
        return render_template('policy.html')
    
    # =========================================================================
    # ADMIN
    # =========================================================================
    
    @app.route('/admin')
    @admin_required
    def admin():
        """Admin dashboard"""
        db = get_database()
        
        # Get pending reports
        reports = db.execute('''
            SELECT r.*, gp.paper_id, p.title, p.claim, u.username as reporter_name
            FROM reports r
            JOIN gallery_posts gp ON r.post_id = gp.post_id
            JOIN papers p ON gp.paper_id = p.paper_id
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.status = 'pending'
            ORDER BY r.created_at DESC
        ''').fetchall()
        
        # Get hidden posts
        hidden = db.execute('''
            SELECT gp.*, p.title, p.claim
            FROM gallery_posts gp
            JOIN papers p ON gp.paper_id = p.paper_id
            WHERE gp.is_hidden = 1 AND gp.is_deleted = 0
        ''').fetchall()
        
        # Get blocked keywords
        keywords = db.execute('SELECT * FROM blocked_keywords ORDER BY keyword').fetchall()
        
        return render_template('admin.html', reports=reports, hidden=hidden, keywords=keywords)
    
    @app.route('/admin/action', methods=['POST'])
    @admin_required
    def admin_action():
        """Process admin action"""
        db = get_database()
        
        action = request.form.get('action')
        target_type = request.form.get('target_type')
        target_id = request.form.get('target_id')
        notes = request.form.get('notes', '')
        
        if action == 'approve':
            db.execute('UPDATE gallery_posts SET is_hidden = 0 WHERE post_id = ?', (target_id,))
            db.execute('UPDATE reports SET status = ? WHERE post_id = ?', ('dismissed', target_id))
        elif action == 'keep_hidden':
            db.execute('UPDATE reports SET status = ? WHERE post_id = ?', ('actioned', target_id))
        elif action == 'remove':
            db.execute('UPDATE gallery_posts SET is_deleted = 1, deleted_at = ? WHERE post_id = ?', 
                       (datetime.utcnow().isoformat(), target_id))
            db.execute('UPDATE reports SET status = ? WHERE post_id = ?', ('actioned', target_id))
        elif action == 'ban_user':
            db.execute('UPDATE users SET is_banned = 1 WHERE id = ?', (target_id,))
        elif action == 'add_keyword':
            keyword = request.form.get('keyword', '').strip().lower()
            if keyword:
                db.execute('INSERT OR IGNORE INTO blocked_keywords (keyword, created_by) VALUES (?, ?)',
                           (keyword, session['user_id']))
        elif action == 'remove_keyword':
            db.execute('DELETE FROM blocked_keywords WHERE id = ?', (target_id,))
        
        # Log action
        db.execute('''
            INSERT INTO moderation_log (action, target_type, target_id, admin_id, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (action, target_type, target_id, session['user_id'], notes))
        
        db.commit()
        flash('Action completed.', 'success')
        return redirect(url_for('admin'))
    
    @app.route('/setup-admin', methods=['GET', 'POST'])
    def setup_admin():
        """Secure first admin setup - only works if no admin exists"""
        db = get_database()
        
        # Check if any admin already exists
        existing_admin = db.execute('SELECT * FROM users WHERE is_admin = 1').fetchone()
        if existing_admin:
            flash('Admin already exists. Contact existing admin for access.', 'error')
            return redirect(url_for('index'))
        
        # Get setup token from environment (required for security)
        setup_token = os.environ.get('TRUSTMEBRO_ADMIN_TOKEN', 'trustmebro-setup-2024')
        
        if request.method == 'GET':
            return render_template('admin_setup.html')
        
        # POST - verify token and create admin
        provided_token = request.form.get('token', '')
        username = request.form.get('username', '').strip()
        
        if provided_token != setup_token:
            flash('Invalid setup token.', 'error')
            return redirect(url_for('setup_admin'))
        
        if not username:
            flash('Please enter a username.', 'error')
            return redirect(url_for('setup_admin'))
        
        # Find user and make admin
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if not user:
            flash(f'User "{username}" not found. Create an account first.', 'error')
            return redirect(url_for('setup_admin'))
        
        db.execute('UPDATE users SET is_admin = 1 WHERE username = ?', (username,))
        db.commit()
        
        print(f"[ADMIN] ✅ First admin created: {username}")
        flash(f'🎉 {username} is now the admin!', 'success')
        return redirect(url_for('admin'))
    
    # =========================================================================
    # SEO ROUTES
    # =========================================================================
    
    @app.route('/robots.txt')
    def robots():
        """Robots.txt for search engines"""
        content = """User-agent: *
Allow: /
Allow: /gallery
Allow: /gallery/
Allow: /policy

Disallow: /admin
Disallow: /setup-admin
Disallow: /logout
Disallow: /api/

Sitemap: {host}sitemap.xml

# TRUSTMEBRO - Parody Research Paper Generator
# All content is satirical and fictional
""".format(host=request.host_url)
        return app.response_class(content, mimetype='text/plain')
    
    @app.route('/sitemap.xml')
    def sitemap():
        """Dynamic sitemap for SEO"""
        db = get_database()
        
        # Get all public gallery posts
        posts = db.execute('''
            SELECT gp.id, gp.created_at, p.title
            FROM gallery_posts gp
            JOIN papers p ON gp.paper_id = p.paper_id
            WHERE gp.is_hidden = 0 AND gp.is_deleted = 0
            ORDER BY gp.created_at DESC
            LIMIT 1000
        ''').fetchall()
        
        # Build sitemap XML
        xml_items = []
        
        # Static pages
        static_pages = [
            ('index', '1.0', 'daily'),
            ('gallery', '0.9', 'hourly'),
            ('policy', '0.5', 'monthly'),
            ('auth', '0.3', 'monthly'),
        ]
        
        for endpoint, priority, freq in static_pages:
            xml_items.append(f'''  <url>
    <loc>{request.host_url.rstrip('/')}{url_for(endpoint)}</loc>
    <changefreq>{freq}</changefreq>
    <priority>{priority}</priority>
  </url>''')
        
        # Gallery posts (dynamic)
        for post in posts:
            created = post['created_at'] if post['created_at'] else '2024-01-01'
            xml_items.append(f'''  <url>
    <loc>{request.host_url.rstrip('/')}{url_for('gallery_post', post_id=post['id'])}</loc>
    <lastmod>{created[:10]}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>''')
        
        xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(xml_items)}
</urlset>'''
        
        return app.response_class(xml_content, mimetype='application/xml')
    
    @app.route('/manifest.json')
    def manifest():
        """PWA Manifest"""
        manifest_data = {
            "name": "TRUSTMEBRO - Journal of Unverified Claims",
            "short_name": "TRUSTMEBRO",
            "description": "Generate hilarious parody academic papers for any ridiculous claim",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#FAF8F5",
            "theme_color": "#C85A28",
            "icons": [
                {
                    "src": "/static/icon-192.png",
                    "sizes": "192x192",
                    "type": "image/png"
                },
                {
                    "src": "/static/icon-512.png",
                    "sizes": "512x512",
                    "type": "image/png"
                }
            ]
        }
        return jsonify(manifest_data)
