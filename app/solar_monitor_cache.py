from sqlalchemy import Boolean, Column, Integer, String, BLOB
from sqlalchemy.orm import relationship

from database import Base


class SolarMonitorCache(Base):
    __tablename__ = "solar_monitor_cache"

    id = Column(Integer, primary_key=True)
    json_data = Column(String)
    date = Column(String, index=True, unique=True)
    image = Column(BLOB)
