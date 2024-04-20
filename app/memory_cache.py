import time
from typing import Generic, TypeVar, Optional
from threading import Thread
 
T = TypeVar('T')

class SimpleMemoryCache(Generic[T]):
    def __init__(self, timeout: int):
        self.cache = {}
        self.timeout = timeout
        self.cleaner_thread = Thread(target=self._clean_expired_items)
        self.cleaner_thread.daemon = True 
        self.cleaner_thread.start()

    def _clean_expired_items(self):
        while True:
            current_time = time.time()
            expired_keys = [key for key, item in self.cache.items() if item.expiry_time <= current_time]
            for key in expired_keys:
                print(f"Deleting {key} from memory!")
                del self.cache[key]
            time.sleep(30)  # Verifica itens expirados a cada 10 segundos

    def put(self, key: str, value: T) -> None:
        print(f"put key: {key} on cache")
        expiry_time = time.time() + self.timeout
        self.cache[key] = CacheObject(value, expiry_time)

    def get(self, key: str) -> Optional[T]:
        cache_object = self.cache.get(key)
        if cache_object is None:
            print(f"The {key} is not in cache")
            return None
        elif cache_object.is_expired():
            del self.cache[key]
            print(f"The {key} is expired")
            return None
        else:
            print(f"The {key} is on cache")
            return cache_object.value


class CacheObject(Generic[T]):
    def __init__(self, value: T, expiry_time: float):
        self.value = value
        self.expiry_time = expiry_time

    def is_expired(self) -> bool:
        return time.time() >= self.expiry_time