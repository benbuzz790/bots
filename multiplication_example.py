import copy
import threading
import time


class MultiplicableObject:

    def __init__(self, value):
        self.value = value

    def __mul__(self, other):
        if isinstance(other, int):
            references = [self for _ in range(other)]
            import copy
            copies = [copy.deepcopy(self) for _ in range(other)]
            return references

    def __rmul__(self, other):
        return self.__mul__(other)

    def __repr__(self):
        return f'MultiplicableObject(value={self.value})'


class PointerLikeObject:

    def __init__(self, value):
        self.value = value

    def __mul__(self, other):
        if isinstance(other, int):
            return [copy.deepcopy(self) for _ in range(other)]
        return NotImplemented

    def __pow__(self, other):
        if isinstance(other, int):
            return [self for _ in range(other)]
        return NotImplemented

    def __repr__(self):
        return f'PointerLikeObject(value={self.value})'


class ThreadSafePointerLike:

    def __init__(self, value):
        self.value = value
        self._lock = threading.Lock()

    def __mul__(self, other):
        if isinstance(other, int):
            with self._lock:
                return [copy.deepcopy(self) for _ in range(other)]
        return NotImplemented

    def __pow__(self, other):
        if isinstance(other, int):
            with self._lock:
                return [self for _ in range(other)]
        return NotImplemented

    def modify_value(self, new_value):
        with self._lock:
            time.sleep(0.1)
            self.value = new_value

    def __repr__(self):
        with self._lock:
            return f'ThreadSafePointerLike(value={self.value})'


def demonstrate_threading():
    print('Without thread safety:')
    unsafe_obj = PointerLikeObject(0)
    refs = unsafe_obj ** 3

    def modify_unsafe(obj, val):
        time.sleep(0.1)
        obj.value = val
    threads = [threading.Thread(target=modify_unsafe, args=(refs[0], i)) for
        i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f'Final unsafe value: {refs[0].value}')
    print('\nWith thread safety:')
    safe_obj = ThreadSafePointerLike(0)
    safe_refs = safe_obj ** 3
    threads = [threading.Thread(target=safe_refs[0].modify_value, args=(i,)
        ) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f'Final safe value: {safe_refs[0].value}')

if __name__ == '__main__':
    demonstrate_threading()