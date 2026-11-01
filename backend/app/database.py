"""
CareerTrack — Database Connection with Pooling
"""
import psycopg
import atexit
from psycopg_pool import ConnectionPool
from contextlib import contextmanager
from .config import settings

# 1. Connection Pool toiri koro
# min_size=2: Surute 2 ta connection ready thakbe
# max_size=10: Maximum 10 ta connection ekhone khulte parbe
pool = ConnectionPool(
    conninfo=f"dbname={settings.DB_NAME} user={settings.DB_USER} password={settings.DB_PASSWORD} host={settings.DB_HOST} port={settings.DB_PORT}",
    min_size=2,
    max_size=10,
    open=True
)

# 2. Program shesh howar age pool ta jeno thik moto close hoy, seta nishchit koro
atexit.register(pool.close)


@contextmanager
def get_cursor():
    """
    Pool theke connection niye cursor dey.
    Kaj sesh hole connection abar pool e ferot jay.
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            yield cur


def test_connection() -> bool:
    try:
        with get_cursor() as cur:
            cur.execute("SELECT version()")
            print(f"✅ Connected to: {cur.fetchone()[0][:50]}...")
            return True
    except psycopg.Error as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    test_connection()