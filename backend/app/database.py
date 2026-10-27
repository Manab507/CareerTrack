"""
CareerTrack — Database Connection (psycopg v3)
"""
import psycopg
from contextlib import contextmanager
from .config import settings


def get_connection():
    """Get a new database connection"""
    return psycopg.connect(**settings.db_config())


@contextmanager
def get_cursor():
    """
    Context manager for cursor.
    Auto commit/rollback/close.
    
    Usage:
        with get_cursor() as cur:
            cur.execute("SELECT ...")
            rows = cur.fetchall()
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    finally:
        conn.close()


def test_connection() -> bool:
    """Test DB connection"""
    try:
        with get_cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]
            print(f"✅ Connected: {version[:50]}...")
            return True
    except psycopg.Error as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    test_connection()