"""
CareerTrack — Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Database
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "careertrack")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    
    # JWT
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "careertrack-local-practice-secret-key-change-in-production-min-32"
    )
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )
    
    @classmethod
    def db_config(cls) -> dict:
        return {
            "host": cls.DB_HOST,
            "port": cls.DB_PORT,
            "dbname": cls.DB_NAME,
            "user": cls.DB_USER,
            "password": cls.DB_PASSWORD,
        }


settings = Settings()