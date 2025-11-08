import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self, db_name='replimatch.db'):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                skills TEXT,
                interests TEXT,
                tech_stack TEXT,
                project_types TEXT,
                replit_username TEXT,
                bio TEXT,
                repl_data TEXT,
                profile_photo TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Matches table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                matched_user_id INTEGER,
                match_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (matched_user_id) REFERENCES users (id)
            )
        ''')
        
        # Collaborations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collaborations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER,
                user2_id INTEGER,
                repl_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user1_id) REFERENCES users (id),
                FOREIGN KEY (user2_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self, username, email, password):
        """Create a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
            (username, email, password)
        )
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    
    def get_user(self, username):
        """Get user by username"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    def update_profile(self, user_id, profile_data):
        """Update or create user profile"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM profiles WHERE user_id = ?', (user_id,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('''
                UPDATE profiles SET
                skills = ?, interests = ?, tech_stack = ?,
                project_types = ?, replit_username = ?, bio = ?, profile_photo = ?
                WHERE user_id = ?
            ''', (
                json.dumps(profile_data['skills']),
                json.dumps(profile_data['interests']),
                json.dumps(profile_data['tech_stack']),
                json.dumps(profile_data['project_types']),
                profile_data['replit_username'],
                profile_data['bio'],
                profile_data.get('profile_photo'),
                user_id
            ))
        else:
            cursor.execute('''
                INSERT INTO profiles (user_id, skills, interests, tech_stack,
                project_types, replit_username, bio, profile_photo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                json.dumps(profile_data['skills']),
                json.dumps(profile_data['interests']),
                json.dumps(profile_data['tech_stack']),
                json.dumps(profile_data['project_types']),
                profile_data['replit_username'],
                profile_data['bio'],
                profile_data.get('profile_photo')
            ))
        
        conn.commit()
        conn.close()
    
    def update_repl_data(self, user_id, repl_data):
        """Update user's Repl analysis data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE profiles SET repl_data = ? WHERE user_id = ?',
            (json.dumps(repl_data), user_id)
        )
        conn.commit()
        conn.close()
    
    def get_user_profile(self, user_id):
        """Get complete user profile"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.*, p.*
            FROM users u
            LEFT JOIN profiles p ON u.id = p.user_id
            WHERE u.id = ?
        ''', (user_id,))
        profile = cursor.fetchone()
        conn.close()
        
        if profile:
            data = dict(profile)
            # Parse JSON fields
            for field in ['skills', 'interests', 'tech_stack', 'project_types', 'repl_data']:
                if data.get(field):
                    data[field] = json.loads(data[field])
            return data
        return None
    
    def get_all_users(self, exclude_id=None):
        """Get all users except specified ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if exclude_id:
            cursor.execute('''
                SELECT u.*, p.*
                FROM users u
                LEFT JOIN profiles p ON u.id = p.user_id
                WHERE u.id != ?
            ''', (exclude_id,))
        else:
            cursor.execute('''
                SELECT u.*, p.*
                FROM users u
                LEFT JOIN profiles p ON u.id = p.user_id
            ''')
        
        users = cursor.fetchall()
        conn.close()
        
        result = []
        for user in users:
            data = dict(user)
            for field in ['skills', 'interests', 'tech_stack', 'project_types', 'repl_data']:
                if data.get(field):
                    data[field] = json.loads(data[field])
            result.append(data)
        return result
    
    def save_matches(self, user_id, matches):
        """Save user matches"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Clear old matches
        cursor.execute('DELETE FROM matches WHERE user_id = ?', (user_id,))
        
        # Insert new matches
        for match in matches:
            cursor.execute('''
                INSERT INTO matches (user_id, matched_user_id, match_score)
                VALUES (?, ?, ?)
            ''', (user_id, match['user_id'], match['score']))
        
        conn.commit()
        conn.close()
    
    def get_user_matches(self, user_id):
        """Get user's matches"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.*, u.username, p.*
            FROM matches m
            JOIN users u ON m.matched_user_id = u.id
            LEFT JOIN profiles p ON u.id = p.user_id
            WHERE m.user_id = ?
            ORDER BY m.match_score DESC
        ''', (user_id,))
        
        matches = cursor.fetchall()
        conn.close()
        
        result = []
        for match in matches:
            data = dict(match)
            for field in ['skills', 'interests', 'tech_stack', 'project_types']:
                if data.get(field):
                    data[field] = json.loads(data[field])
            result.append(data)
        return result
    
    def create_collaboration(self, collab_data):
        """Create a new collaboration"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO collaborations (user1_id, user2_id, repl_url)
            VALUES (?, ?, ?)
        ''', (collab_data['user1_id'], collab_data['user2_id'], collab_data['repl_url']))
        collab_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return collab_id
    
    def get_collaboration(self, collab_id):
        """Get collaboration details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM collaborations WHERE id = ?', (collab_id,))
        collab = cursor.fetchone()
        conn.close()
        return dict(collab) if collab else None
