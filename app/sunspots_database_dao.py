import sqlite3
import json

class SunspotsDatabaseDao:
    def __init__(self, db_name: str = 'sunspots_database_sqlite.db'):
        self.db_name = db_name
        self.create_table()

    def _create_connection(self):
        """Cria uma nova conexão com o banco de dados."""
        return sqlite3.connect(self.db_name)

    def create_table(self):
        with self._create_connection() as conn:
            query = '''
            CREATE TABLE IF NOT EXISTS sunspots_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sunspot_date VARCHAR(10) NOT NULL,
                sunspot_info JSON NOT NULL
            )
            '''
            conn.cursor().execute(query)
            conn.commit()

    def fetch_data_by_date(self, date: str):
        """Busca o JSON e a imagem da tabela 'sunspots_data' pelo campo sunspot_date."""
        query = 'SELECT sunspot_info FROM sunspots_data WHERE sunspot_date = ?'
        with self._create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (date,))
            result = cursor.fetchone()
            if result:
                json_data = json.loads(result[0])  # Converte o JSON string de volta para dicionário
                return json_data
        return None

    def insert_data(self, sunspot_date: str, sunspot_info: dict):
        """Insere dados na tabela 'sunspots_data'."""
        query = 'INSERT INTO sunspots_data (sunspot_date, sunspot_info) VALUES (?, ?)'
        json_info = json.dumps(sunspot_info)  # Converte o dicionário em string JSON
        with self._create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (sunspot_date, json_info))
            conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()

    def __enter__(self):
        self._create_connection()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
