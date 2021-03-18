import threading
import time

from Entities.exceptions import SCHCTimeoutError


class SCHCTimer:
    timeout = None

    def __init__(self, timeout):
        self.timeout = timeout

    def set_timeout(self, new_timeout):
        self.timeout = new_timeout

    def wait(self, raise_exception=False):
        t_i = time.perf_counter()
        while True:
            t_f = time.perf_counter()
            if t_f - t_i >= self.timeout:
                if raise_exception:
                    raise SCHCTimeoutError
                return

    def run(self):
        thread = threading.Thread(target=self.wait, args=(True,))
        thread.start()
