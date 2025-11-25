"""
Unified Redeem Database - Supports both SQLite and PostgreSQL
Automatically detects database type from connection string
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from urllib.parse import urlparse

class RedeemDatabase:
    def __init__(self, db_connection: str = None):
        """
        Initialize database connection
        
        Args:
            db_connection: Either a file path (SQLite) or postgresql:// URL (PostgreSQL)
                          If None, defaults to SQLite in data/redeem_codes.db
        """
        if db_connection is None:
            # Default to SQLite
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_connection = os.path.join(base_dir, 'data', 'redeem_codes.db')
        
        self.db_connection = db_connection
        self.db_type = self._detect_db_type(db_connection)
        
        # For SQLite, store the file path
        if self.db_type == 'sqlite':
            self.db_path = db_connection
        
        # Import appropriate library
        if self.db_type == 'postgresql':
            try:
                import psycopg2
                import psycopg2.extras
                self.psycopg2 = psycopg2
            except ImportError:
                raise ImportError("psycopg2-binary is required for PostgreSQL. Install with: pip install psycopg2-binary")
        else:
            import sqlite3
            self.sqlite3 = sqlite3
        
        self.init_database()
    
    def _detect_db_type(self, connection_string: str) -> str:
        """Detect if connection string is PostgreSQL or SQLite"""
        if connection_string.startswith('postgresql://') or connection_string.startswith('postgres://'):
            return 'postgresql'
        return 'sqlite'
    
    def _get_connection(self):
        """Get database connection based on type"""
        if self.db_type == 'postgresql':
            return self.psycopg2.connect(self.db_connection)
        else:
            return self.sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if self.db_type == 'postgresql':
            # PostgreSQL schema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS codes (
                    code TEXT PRIMARY KEY,
                    service_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    platform TEXT NOT NULL,
                    service_type TEXT NOT NULL,
                    requirements TEXT,
                    status TEXT DEFAULT 'unused',
                    created_date TIMESTAMP NOT NULL,
                    used_date TIMESTAMP,
                    used_by_user_id TEXT,
                    order_id INTEGER,
                    expiry_days INTEGER DEFAULT 30,
                    has_refill BOOLEAN DEFAULT FALSE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS redemption_history (
                    id SERIAL PRIMARY KEY,
                    code TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    service_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    link TEXT NOT NULL,
                    order_id INTEGER,
                    redeemed_date TIMESTAMP NOT NULL,
                    FOREIGN KEY (code) REFERENCES codes(code)
                )
            ''')
        else:
            # SQLite schema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS codes (
                    code TEXT PRIMARY KEY,
                    service_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    platform TEXT NOT NULL,
                    service_type TEXT NOT NULL,
                    requirements TEXT,
                    status TEXT DEFAULT 'unused',
                    created_date TEXT NOT NULL,
                    used_date TEXT,
                    used_by_user_id TEXT,
                    order_id INTEGER,
                    expiry_days INTEGER DEFAULT 30,
                    has_refill INTEGER DEFAULT 0
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS redemption_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    service_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    link TEXT NOT NULL,
                    order_id INTEGER,
                    redeemed_date TEXT NOT NULL,
                    FOREIGN KEY (code) REFERENCES codes(code)
                )
            ''')
        
        conn.commit()
        conn.close()
    
    def add_code(self, code: str, service_id: int, quantity: int, platform: str, 
                 service_type: str, requirements: str = "", expiry_days: int = 30, has_refill: bool = False) -> bool:
        """Add a new redemption code"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if self.db_type == 'postgresql':
                cursor.execute('''
                    INSERT INTO codes (code, service_id, quantity, platform, service_type, 
                                     requirements, created_date, expiry_days, has_refill)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (code, service_id, quantity, platform, service_type, requirements, 
                      datetime.utcnow(), expiry_days, has_refill))
            else:
                cursor.execute('''
                    INSERT INTO codes (code, service_id, quantity, platform, service_type, 
                                     requirements, created_date, expiry_days, has_refill)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (code, service_id, quantity, platform, service_type, requirements, 
                      datetime.utcnow().isoformat(), expiry_days, 1 if has_refill else 0))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            # Code already exists or other error
            return False
    
    def get_code(self, code: str) -> Optional[Dict]:
        """Get code details"""
        conn = self._get_connection()
        
        if self.db_type == 'postgresql':
            cursor = conn.cursor(cursor_factory=self.psycopg2.extras.RealDictCursor)
            cursor.execute('SELECT * FROM codes WHERE code = %s', (code,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            return dict(row)
        else:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM codes WHERE code = ?', (code,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            return {
                'code': row[0],
                'service_id': row[1],
                'quantity': row[2],
                'platform': row[3],
                'service_type': row[4],
                'requirements': row[5],
                'status': row[6],
                'created_date': row[7],
                'used_date': row[8],
                'used_by_user_id': row[9],
                'order_id': row[10],
                'expiry_days': row[11],
                'has_refill': bool(row[12])
            }
    
    def is_code_valid(self, code: str) -> bool:
        """Check if code exists and is unused"""
        code_data = self.get_code(code)
        if not code_data:
            return False
        
        if code_data['status'] != 'unused':
            return False
        
        # Check expiry
        created_date = datetime.fromisoformat(str(code_data['created_date']).replace('Z', '+00:00'))
        expiry_date = created_date + timedelta(days=code_data['expiry_days'])
        
        if datetime.utcnow() > expiry_date:
            return False
        
        return True
    
    def mark_code_used(self, code: str, user_id: str, order_id: int = None) -> bool:
        """Mark a code as used"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if self.db_type == 'postgresql':
                cursor.execute('''
                    UPDATE codes 
                    SET status = 'used', used_date = %s, used_by_user_id = %s, order_id = %s
                    WHERE code = %s
                ''', (datetime.utcnow(), user_id, order_id, code))
            else:
                cursor.execute('''
                    UPDATE codes 
                    SET status = 'used', used_date = ?, used_by_user_id = ?, order_id = ?
                    WHERE code = ?
                ''', (datetime.utcnow().isoformat(), user_id, order_id, code))
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def add_redemption_history(self, code: str, user_id: str, username: str, 
                               service_id: int, quantity: int, link: str, order_id: int = None) -> bool:
        """Add redemption to history"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if self.db_type == 'postgresql':
                cursor.execute('''
                    INSERT INTO redemption_history 
                    (code, user_id, username, service_id, quantity, link, order_id, redeemed_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''', (code, user_id, username, service_id, quantity, link, order_id, datetime.utcnow()))
            else:
                cursor.execute('''
                    INSERT INTO redemption_history 
                    (code, user_id, username, service_id, quantity, link, order_id, redeemed_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (code, user_id, username, service_id, quantity, link, order_id, datetime.utcnow().isoformat()))
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def get_user_redemptions(self, user_id: str) -> List[Dict]:
        """Get all redemptions for a user"""
        conn = self._get_connection()
        
        if self.db_type == 'postgresql':
            cursor = conn.cursor(cursor_factory=self.psycopg2.extras.RealDictCursor)
            cursor.execute('''
                SELECT * FROM redemption_history 
                WHERE user_id = %s 
                ORDER BY redeemed_date DESC
            ''', (user_id,))
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        else:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM redemption_history 
                WHERE user_id = ? 
                ORDER BY redeemed_date DESC
            ''', (user_id,))
            rows = cursor.fetchall()
            conn.close()
            
            return [{
                'id': row[0],
                'code': row[1],
                'user_id': row[2],
                'username': row[3],
                'service_id': row[4],
                'quantity': row[5],
                'link': row[6],
                'order_id': row[7],
                'redeemed_date': row[8]
            } for row in rows]
    
    def get_all_codes(self, status: str = None) -> List[Dict]:
        """Get all codes, optionally filtered by status"""
        conn = self._get_connection()
        
        if self.db_type == 'postgresql':
            cursor = conn.cursor(cursor_factory=self.psycopg2.extras.RealDictCursor)
            if status:
                cursor.execute('SELECT * FROM codes WHERE status = %s ORDER BY created_date DESC', (status,))
            else:
                cursor.execute('SELECT * FROM codes ORDER BY created_date DESC')
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        else:
            cursor = conn.cursor()
            if status:
                cursor.execute('SELECT * FROM codes WHERE status = ? ORDER BY created_date DESC', (status,))
            else:
                cursor.execute('SELECT * FROM codes ORDER BY created_date DESC')
            rows = cursor.fetchall()
            conn.close()
            
            return [{
                'code': row[0],
                'service_id': row[1],
                'quantity': row[2],
                'platform': row[3],
                'service_type': row[4],
                'requirements': row[5],
                'status': row[6],
                'created_date': row[7],
                'used_date': row[8],
                'used_by_user_id': row[9],
                'order_id': row[10],
                'expiry_days': row[11],
                'has_refill': bool(row[12])
            } for row in rows]
    
    def get_all_redemptions(self) -> List[Dict]:
        """Get all redemption history"""
        conn = self._get_connection()
        
        if self.db_type == 'postgresql':
            cursor = conn.cursor(cursor_factory=self.psycopg2.extras.RealDictCursor)
            cursor.execute('SELECT * FROM redemption_history ORDER BY redeemed_date DESC')
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        else:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM redemption_history ORDER BY redeemed_date DESC')
            rows = cursor.fetchall()
            conn.close()
            
            return [{
                'id': row[0],
                'code': row[1],
                'user_id': row[2],
                'username': row[3],
                'service_id': row[4],
                'quantity': row[5],
                'link': row[6],
                'order_id': row[7],
                'redeemed_date': row[8]
            } for row in rows]
