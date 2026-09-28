# app/repositories/user_repository.py
from typing import List, Optional, Dict
from app.models.user import User
from app.repositories.db_connection import DatabaseConnection

class UserRepository:
    def get_by_username(self, username: str) -> Optional[User]:
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id, username, email, password_hash, is_active FROM users WHERE username = %s"
            cursor.execute(query, (username,))
            row = cursor.fetchone()
            if not row:
                return None

            user = User(**row)
            user.roles = self.get_user_roles(user.id, conn)
            user.permissions = self.get_user_permissions(user.id, conn)
            return user
        finally:
            cursor.close()
            conn.close()

    def get_by_email(self, email: str) -> Optional[User]:
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id, username, email, password_hash, is_active FROM users WHERE email = %s"
            cursor.execute(query, (email.strip().lower(),))
            row = cursor.fetchone()
            if not row:
                return None

            user = User(**row)
            user.roles = self.get_user_roles(user.id, conn)
            user.permissions = self.get_user_permissions(user.id, conn)
            return user
        finally:
            cursor.close()
            conn.close()

    def get_by_id(self, user_id: int) -> Optional[User]:
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id, username, email, password_hash, is_active FROM users WHERE id = %s"
            cursor.execute(query, (user_id,))
            row = cursor.fetchone()
            if not row:
                return None

            user = User(**row)
            user.roles = self.get_user_roles(user.id, conn)
            user.permissions = self.get_user_permissions(user.id, conn)
            return user
        finally:
            cursor.close()
            conn.close()

    def get_user_roles(self, user_id: int, conn=None) -> List[str]:
        """Fetch role names assigned to the user via user_roles bridge table."""
        close_conn = False
        if conn is None:
            conn = DatabaseConnection.get_connection()
            close_conn = True

        cursor = conn.cursor()
        try:
            sql = """
                SELECT r.name 
                FROM roles r
                INNER JOIN user_roles ur ON r.id = ur.role_id
                WHERE ur.user_id = %s
            """
            cursor.execute(sql, (user_id,))
            return [row[0] for row in cursor.fetchall()]
        finally:
            cursor.close()
            if close_conn:
                conn.close()

    def get_user_permissions(self, user_id: int, conn=None) -> List[str]:
        """
        Traverses user_roles -> role_permissions -> permissions
        to fetch all distinct permission strings for the user.
        """
        close_conn = False
        if conn is None:
            conn = DatabaseConnection.get_connection()
            close_conn = True

        cursor = conn.cursor()
        try:
            sql = """
                SELECT DISTINCT p.name
                FROM permissions p
                INNER JOIN role_permissions rp ON p.id = rp.permission_id
                INNER JOIN user_roles ur ON rp.role_id = ur.role_id
                WHERE ur.user_id = %s
            """
            cursor.execute(sql, (user_id,))
            return [row[0] for row in cursor.fetchall()]
        finally:
            cursor.close()
            if close_conn:
                conn.close()

    def list_all(self) -> List[User]:
        """
        Return all registered users in deterministic ascending sequence (ORDER BY id ASC)
        with their associated roles and permissions hydrated.
        """
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            sql = "SELECT id, username, email, password_hash, is_active FROM users ORDER BY id ASC;"
            cursor.execute(sql)
            rows = cursor.fetchall()
            users = []
            for row in rows:
                user = User(**row)
                user.roles = self.get_user_roles(user.id, conn)
                user.permissions = self.get_user_permissions(user.id, conn)
                users.append(user)
            return users
        finally:
            cursor.close()
            conn.close()

    def create(self, user: User, role_name: str = "Student") -> int:
        """Create a user and assign their role inside an atomic transaction."""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            # 1. Insert user
            insert_user_sql = """
                INSERT INTO users (username, email, password_hash, is_active)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_user_sql, (user.username, user.email, user.password_hash, user.is_active))
            user_id = cursor.lastrowid

            # 2. Lookup role ID
            cursor.execute("SELECT id FROM roles WHERE name = %s", (role_name,))
            role_row = cursor.fetchone()
            if not role_row:
                raise ValueError(f"Role '{role_name}' does not exist.")
            role_id = role_row[0]

            # 3. Insert user_roles mapping
            cursor.execute("INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)", (user_id, role_id))

            conn.commit()
            return user_id
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def register(self, user: User, role_name: str = "Student") -> int:
        """
        Atomically register a new user and assign them to an RBAC role.
        Rolls back on error.
        """
        return self.create(user, role_name=role_name)

    def update_role(self, user_id: int, new_role_name: str) -> bool:
        """Reassign user to a new role inside an atomic transaction."""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM roles WHERE name = %s", (new_role_name,))
            role_row = cursor.fetchone()
            if not role_row:
                raise ValueError(f"Role '{new_role_name}' does not exist.")
            role_id = role_row[0]

            cursor.execute("DELETE FROM user_roles WHERE user_id = %s", (user_id,))
            cursor.execute("INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)", (user_id, role_id))
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def toggle_active(self, user_id: int, is_active: bool) -> bool:
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET is_active = %s WHERE id = %s", (is_active, user_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()
            conn.close()

    def delete(self, user_id: int) -> bool:
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()
            conn.close()

    def list_roles(self) -> List[Dict]:
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id, name, description FROM roles ORDER BY id ASC")
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()