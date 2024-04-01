from sqlalchemy import Boolean, Column, Integer, String, BLOB, JSON
from sqlalchemy.orm import relationship

from database import Base


class SolarMonitorCache(Base):
    __tablename__ = "solar_monitor_cache"

    id = Column(Integer, primary_key=True)
    json_data = Column(JSON)
    date = Column(String, index=True, unique=True)
    image = Column(BLOB)
