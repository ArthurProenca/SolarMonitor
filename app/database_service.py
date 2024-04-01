from solar_monitor_cache import SolarMonitorCache
from database import SessionManager


def save_data(json_data, date: str, image_data: bytes):
    with SessionManager() as db:
        db.add(SolarMonitorCache(json_data=json_data, date=date, image=image_data))
        db.commit() 

def get_by_date(date: str):
    with SessionManager() as db:
        return db.query(SolarMonitorCache).filter_by(date=date).first()