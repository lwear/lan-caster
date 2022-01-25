import time

DELTA = 0


def set(serverTime):
    global DELTA
    DELTA = serverTime - time.perf_counter()


def perf_counter():
    global DELTA
    return time.perf_counter() + DELTA


def sleep(sec):
    time.sleep(sec)
