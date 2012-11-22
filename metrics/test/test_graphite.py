from gevent import monkey
monkey.patch_all()
from metrics import Metric, metric, timing
from mock_server import Server
import gevent
import logging
import unittest
import sys

logging.basicConfig(stream=sys.stdout)
logging.root.setLevel(logging.DEBUG)
logger = logging.getLogger("metrics_test")

NUM_PRIMES = 1000000

lines_for_add = lambda x : x
lines_for_timing = lambda x : x * 5


def get_prime_list(n):
    """ Returns a list of prime numbers from 2 to < n using a sieve algorithm"""
    if n < 2: return []
    if n == 2: return [2]
    s = range(3, n + 1, 2)
    mroot = n ** 0.5
    half = len(s)
    i = 0
    m = 3
    while m <= mroot:
        if s[i]:
            j = (m * m - 3) // 2
            s[j] = 0
            while j < half:
                s[j] = 0
                j += m
        i = i + 1
        m = 2 * i + 3
    return [2] + [x for x in s if x]

@metric("test.add.decorator")
def get_prime_list_with_add(n):
    return get_prime_list(n)

@timing("test.timing.decorator")
def get_prime_list_with_timing(n):
    return get_prime_list(n)

@metric("test.add.decorator.combined")
@timing("test.timing.decorator.combined")
def get_prime_list_with_add_and_timing(n):
    return get_prime_list(n)


class MetricsTest(unittest.TestCase):

    def wait_buf(self, num_entries, timeout=10):
        def wait_loop():
            while True:
                if len(self.buf) == num_entries:
                    return
                gevent.sleep(0.1)

        greenlet = gevent.spawn(wait_loop)
        greenlet.join(timeout)

        if len(self.buf) != num_entries:
            raise Exception("Expected buffer size %d, got %d" % (num_entries, len(self.buf)))

    def setUp(self):
        """
        Starts a mock server for every test.
        """
        self.buf = []
        def save_to_buf(msg):
            self.buf.extend([line.strip() for line in msg.split("\n") if line.strip()])
        self.server = Server(save_to_buf)
        gevent.spawn(self.server.serve)
        gevent.sleep(1)

    def tearDown(self):
        """
        Shuts down mock server.
        """
        self.server.stop()
        gevent.sleep(1)

    def test_add(self):
        logger.info("test_add")
        for x in xrange(10):
            Metric.add("test.add")
        self.wait_buf(lines_for_add(10))
        for line in self.buf:
            self.assertTrue(line.startswith("stats.test.add 1.0"))

    def test_timing(self):
        logger.info("test_timing")
        for x in xrange(10):
            timer = Metric.start_timing("test.timing")
            primes = get_prime_list(NUM_PRIMES)
            timer.done()
            logger.debug("Got %d primes", len(primes))
        self.wait_buf(lines_for_timing(10))
        for line in self.buf:
            self.assertTrue(line.startswith("stats.timers.test.timing"))

    def test_timing_exact(self):
        Metric.timing("exact.time", 1.337)
        self.wait_buf(lines_for_timing(1))
        stripped_timestamps = [" ".join(line.split(" ")[:-1]) for line in self.buf]
        self.assertTrue("stats.timers.exact.time.lower 1337.0" in stripped_timestamps)
        self.assertTrue("stats.timers.exact.time.count 1" in stripped_timestamps)
        self.assertTrue("stats.timers.exact.time.mean 1337.0" in stripped_timestamps)
        self.assertTrue("stats.timers.exact.time.upper 1337.0" in stripped_timestamps)
        self.assertTrue("stats.timers.exact.time.upper_100 1337.0" in stripped_timestamps)

    def test_add_decorator(self):
        logger.info("test_add_decorator")
        for x in xrange(10):
            primes = get_prime_list_with_add(NUM_PRIMES)
            logger.debug("Got %d primes", len(primes))
        self.wait_buf(lines_for_add(10))
        for line in self.buf:
            self.assertTrue(line.startswith("stats.test.add.decorator 1.0"))

    def test_timing_decorator(self):
        logger.info("test_timing_decorator")
        for x in xrange(0, 10):
            primes = get_prime_list_with_timing(NUM_PRIMES)
            logger.debug("Got %d primes", len(primes))
        self.wait_buf(lines_for_timing(10))
        for line in self.buf:
            self.assertTrue(line.startswith("stats.timers.test.timing.decorator"))

    def test_nested_decorators(self):
        logger.info("test_nested_decorators")
        for x in xrange(0, 10):
            primes = get_prime_list_with_add_and_timing(NUM_PRIMES)
            logger.debug("Got %d primes", len(primes))
        self.wait_buf(lines_for_add(10) + lines_for_timing(10))
        for line in self.buf:
            self.assertTrue(line.startswith("stats.test.add.decorator.combined 1.0") or
                            line.startswith("stats.timers.test.timing.decorator.combined"))

if __name__ == "__main__":
    unittest.main()
