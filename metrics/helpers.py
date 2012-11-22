import os
import time


def get_time():
    if os.name == "posix":
        return time.time()
    else:
        return time.clock()
