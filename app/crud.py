from sqlalchemy.orm import Session
from solar_monitor_cache import SolarMonitorCache

def save_data(db: Session, json_data: str, date: str, image_data: bytes):
    new_data = SolarMonitorCache(json_data=json_data, date=date, image=image_data)
    db.add(new_data)
    db.commit()

def get_by_date(db: Session, date: str):
    return db.query(SolarMonitorCache).filter_by(date=date).first()

# Exemplo de uso:
# if __name__ == "__main__":
#     db = SessionLocal()
#     data = get_by_date(db, "2024-03-16")
#     print(data.json_data)
#     db.close()
