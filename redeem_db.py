import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List

class RedeemDatabase:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to data folder
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, 'data', 'redeem_codes.db')
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create codes table
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
        
        # Create redemption history table
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
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO codes (code, service_id, quantity, platform, service_type, 
                                 requirements, created_date, expiry_days, has_refill)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (code, service_id, quantity, platform, service_type, requirements, 
                  datetime.utcnow().isoformat(), expiry_days, 1 if has_refill else 0))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False  # Code already exists
    
    def get_code(self, code: str) -> Optional[Dict]:
        """Get code details"""
        conn = sqlite3.connect(self.db_path)
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
            'has_refill': bool(row[12]) if len(row) > 12 else False
        }
    
    def is_code_valid(self, code: str) -> tuple[bool, str]:
        """Check if code is valid and unused"""
        code_data = self.get_code(code)
        
        if not code_data:
            return False, "Invalid code"
        
        if code_data['status'] == 'used':
            return False, "Code already used"
        
        # Check expiry
        created = datetime.fromisoformat(code_data['created_date'])
        expiry = created + timedelta(days=code_data['expiry_days'])
        
        if datetime.utcnow() > expiry:
            return False, "Code expired"
        
        return True, "Valid"
    
    def mark_code_used(self, code: str, user_id: str, order_id: int) -> bool:
        """Mark code as used"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE codes 
                SET status = 'used', used_date = ?, used_by_user_id = ?, order_id = ?
                WHERE code = ?
            ''', (datetime.utcnow().isoformat(), user_id, order_id, code))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def add_redemption_history(self, code: str, user_id: str, username: str, 
                               service_id: int, quantity: int, link: str, order_id: int) -> bool:
        """Add redemption to history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO redemption_history 
                (code, user_id, username, service_id, quantity, link, order_id, redeemed_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (code, user_id, username, service_id, quantity, link, order_id, 
                  datetime.utcnow().isoformat()))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def get_user_redemptions(self, user_id: str) -> List[Dict]:
        """Get all redemptions by a user"""
        conn = sqlite3.connect(self.db_path)
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
    
    def get_all_codes(self, status: Optional[str] = None) -> List[Dict]:
        """Get all codes, optionally filtered by status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status:
            cursor.execute('SELECT * FROM codes WHERE status = ?', (status,))
        else:
            cursor.execute('SELECT * FROM codes')
        
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
            'expiry_days': row[11]
        } for row in rows]
    
    def delete_code(self, code: str) -> bool:
        """Delete a code"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM codes WHERE code = ?', (code,))
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def get_all_redemptions(self) -> List[Dict]:
        """Get all redemptions"""
        conn = sqlite3.connect(self.db_path)
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
