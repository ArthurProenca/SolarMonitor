from database import SessionLocal
from solar_monitor_cache import SolarMonitorCache
from database import SessionLocal
from solar_monitor_cache import SolarMonitorCache

db = SessionLocal()


def save_data(json_data: str, date: str, image_data: bytes):
    new_data = SolarMonitorCache(json_data=json_data, date=date, image=image_data)
    db.add(new_data)
    db.commit()

def get_by_date(date: str):
    return db.query(SolarMonitorCache).filter_by(date=date).first()
