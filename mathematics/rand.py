import time


class Rand:
    a = 1664525
    b = 1013904223
    n = 2**32
    xn = None

    def __init__(self, seed: int = None):
        if seed is None:
            seed = time.time()

        self.xn = seed

    def next_int(self):
        self.xn = (self.a*self.xn + self.b) % self.n
        return self.xn

    def next_int_in_range(self, min: int = 0, max: int = 2**16) -> int:
        r = self.next_int()
        return int(r % (max-min) + min)
