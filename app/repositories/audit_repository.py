# app/repositories/audit_repository.py
from typing import List, Optional, Dict
from app.repositories.db_connection import DatabaseConnection

class AuditRepository:
    def create_log(self, user_id: Optional[int], action: str, reason: str, ip_address: Optional[str] = None) -> int:
        """Records a security or emergency action into the audit trail."""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            sql = """
                INSERT INTO audit_logs (user_id, action, reason, ip_address)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (user_id, action, reason, ip_address))
            conn.commit()
            return cursor.lastrowid
        finally:
            cursor.close()
            conn.close()

    def list_logs(self, limit: int = 50) -> List[Dict]:
        """Retrieves recent audit logs ordered from newest to oldest."""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            safe_limit = int(limit) if limit and limit > 0 else 50
            sql = f"""
                SELECT a.id, a.user_id, a.action, a.reason, a.ip_address,
                       DATE_FORMAT(a.created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                       COALESCE(u.username, 'System / Root') as username
                FROM audit_logs a
                LEFT JOIN users u ON a.user_id = u.id
                ORDER BY a.id DESC
                LIMIT {safe_limit}
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()
