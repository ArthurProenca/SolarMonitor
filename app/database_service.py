from database import SessionLocal
from solar_monitor_cache import SolarMonitorCache
from database import SessionLocal
from solar_monitor_cache import SolarMonitorCache

db = SessionLocal()


def save_data(json_data, date: str, image_data: bytes):
    try:
        new_data = SolarMonitorCache(json_data=json_data, date=date, image=image_data)
        db.add(new_data)
        db.commit()
    finally:
        close_connection()

def get_by_date(date: str):
    try:
        obj = db.query(SolarMonitorCache).filter_by(date=date).first()
        return obj
    finally:
        close_connection()


def close_connection():
    print("Closing database connection")
    db.close()