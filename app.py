from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
import secrets
from datetime import datetime, timedelta

load_dotenv()  # Load environment variables from .env file
from utils.ai_matcher import AIMatchmaker
from utils.replit_analyzer import ReplAnalyzer
from utils.database import Database

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Set session lifetime
app.config['SESSION_COOKIE_SECURE'] = True  # Only send cookie over HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
app.config['UPLOAD_FOLDER'] = 'static/uploads/profile_photos'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize utilities
db = Database()
matcher = AIMatchmaker()
analyzer = ReplAnalyzer()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # Check if user exists
        if db.get_user(username):
            return jsonify({'error': 'Username already exists'}), 400
        
        # Create new user
        hashed_password = generate_password_hash(password)
        user_id = db.create_user(username, email, hashed_password)
        
        session['user_id'] = user_id
        session['username'] = username
        
        return jsonify({'success': True, 'redirect': '/profile'})
    
    return render_template('signup.html')

@app.route('/login', methods=['POST'])
def login():
    """User login"""
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    try:
        user = db.get_user(username)
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        if not check_password_hash(user['password'], password):
            return jsonify({'error': 'Invalid password'}), 401
        
        session.permanent = True  # Use permanent session
        session['user_id'] = user['id']
        session['username'] = username
        return jsonify({'success': True, 'redirect': '/dashboard'})
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'error': 'An error occurred during login'}), 500

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    """User profile setup"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        user_id = session['user_id']
        
        # Check if it's a file upload or JSON data
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Handle form data with file upload
            profile_photo_path = None
            if 'profile_photo' in request.files:
                file = request.files['profile_photo']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{user_id}_{datetime.now().timestamp()}_{file.filename}")
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    profile_photo_path = f"uploads/profile_photos/{filename}"
            
            # Parse form data
            skills = request.form.get('skills', '').split(',') if request.form.get('skills') else []
            interests = request.form.get('interests', '').split(',') if request.form.get('interests') else []
            
            profile_data = {
                'skills': [s.strip() for s in skills if s.strip()],
                'interests': [i.strip() for i in interests if i.strip()],
                'tech_stack': [s.strip() for s in skills if s.strip()],
                'project_types': [i.strip() for i in interests if i.strip()],
                'replit_username': request.form.get('replit_username', ''),
                'bio': request.form.get('bio', ''),
                'profile_photo': profile_photo_path
            }
        else:
            # Handle JSON data (backward compatibility)
            data = request.json
            profile_data = {
                'skills': data.get('skills', []),
                'interests': data.get('interests', []),
                'tech_stack': data.get('tech_stack', []),
                'project_types': data.get('project_types', []),
                'replit_username': data.get('replit_username'),
                'bio': data.get('bio', ''),
                'profile_photo': data.get('profile_photo')
            }
        
        db.update_profile(user_id, profile_data)
        
        # Analyze user's Repls
        if profile_data['replit_username']:
            try:
                repl_data = analyzer.analyze_user_repls(profile_data['replit_username'])
                db.update_repl_data(user_id, repl_data)
            except Exception as e:
                print(f"Error analyzing Repls: {str(e)}")
        
        if request.content_type and 'multipart/form-data' in request.content_type:
            return redirect(url_for('dashboard'))
        else:
            return jsonify({'success': True, 'redirect': '/dashboard'})
    
    user_id = session['user_id']
    user_data = db.get_user_profile(user_id)
    return render_template('profile.html', user=user_data)

@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    user_data = db.get_user_profile(user_id)
    
    return render_template('dashboard.html', user=user_data)

@app.route('/find-matches', methods=['POST'])
def find_matches():
    """Find potential collaborators using AI"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    user_profile = db.get_user_profile(user_id)
    
    # Get all other users
    all_users = db.get_all_users(exclude_id=user_id)
    
    # Use AI to find best matches
    matches = matcher.find_matches(user_profile, all_users)
    
    # Save matches to database
    db.save_matches(user_id, matches)
    
    return jsonify({'success': True, 'matches': matches[:10]})

@app.route('/matches')
def matches():
    """Display user matches"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    user_matches = db.get_user_matches(user_id)
    
    return render_template('matches.html', matches=user_matches)

@app.route('/start-collaboration/<int:match_id>', methods=['POST'])
def start_collaboration(match_id):
    """Start a collaboration with a matched user"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    
    # Create a shared Repl (in production, use Replit API)
    collab_data = {
        'user1_id': user_id,
        'user2_id': match_id,
        'created_at': datetime.now(),
        'repl_url': f'https://replit.com/@shared/collab-{user_id}-{match_id}'
    }
    
    collab_id = db.create_collaboration(collab_data)
    
    return jsonify({
        'success': True,
        'collaboration_id': collab_id,
        'repl_url': collab_data['repl_url']
    })

@app.route('/chat/<int:collab_id>')
def chat(collab_id):
    """Chat and collaboration interface"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    collaboration = db.get_collaboration(collab_id)
    
    if not collaboration:
        return redirect(url_for('dashboard'))
    
    return render_template('chat.html', collaboration=collaboration)

@app.route('/api/analyze-repo', methods=['POST'])
def analyze_repo():
    """Analyze a GitHub/Replit repository"""
    data = request.json
    repo_url = data.get('repo_url')
    
    if not repo_url:
        return jsonify({'error': 'Repository URL required'}), 400
    
    analysis = analyzer.analyze_repository(repo_url)
    
    return jsonify(analysis)

@app.route('/search-users', methods=['GET', 'POST'])
def search_users():
    """Search users by skills"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if request.method == 'POST':
        data = request.json
        search_skills = data.get('skills', [])
        
        if not search_skills:
            return jsonify({'error': 'No skills provided'}), 400
        
        user_id = session['user_id']
        all_users = db.get_all_users(exclude_id=user_id)
        
        # Filter users by matching skills
        matching_users = []
        for user in all_users:
            user_skills = set(user.get('skills', []))
            search_skills_set = set(search_skills)
            
            # Calculate match percentage
            if user_skills:
                common_skills = user_skills.intersection(search_skills_set)
                if common_skills:
                    match_percentage = len(common_skills) / len(search_skills_set) * 100
                    matching_users.append({
                        'user_id': user['id'],
                        'username': user.get('username', 'Unknown'),
                        'skills': list(user_skills),
                        'common_skills': list(common_skills),
                        'interests': user.get('interests', []),
                        'bio': user.get('bio', ''),
                        'profile_photo': user.get('profile_photo'),
                        'match_percentage': round(match_percentage, 1)
                    })
        
        # Sort by match percentage
        matching_users.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        return jsonify({'success': True, 'users': matching_users})
    
    return render_template('search.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4040, debug=True)
