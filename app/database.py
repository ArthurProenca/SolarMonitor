import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


username = os.getenv('DB_USERNAME', 'postgres')
password = os.getenv('DB_PASSWORD', '1234')
host = os.getenv('DB_HOST', 'localhost')
port = os.getenv('DB_PORT', '5432')
database = os.getenv('DB_NAME', 'postgres')

# Montando a URL de conexão
SQLALCHEMY_DATABASE_URL = f"postgresql://{username}:{password}@{host}:{port}/{database}"

Base = declarative_base()

# Definindo um gerenciador de contexto para a sessão
class SessionManager:
    def __enter__(self):
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=True)
        self.session = SessionLocal()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()