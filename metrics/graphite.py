from pystatsd import Client, Server
from helpers import get_time
import logging
import gevent

logger = logging.getLogger("metrics")

# Configuration attributes:
# * host: the host where graphite/carbon is listening
# * port: the port where graphite/carbon is listening
# * namespace (optional): the prefix for all stat keys
# * debug (optional): for debugging
_config = {}
_statsd = None


def start_graphite_proxy(config):
    global _config
    _config.clear()
    _config.update(config)
    host = _config.get("host")
    port = _config.get("port")
    if host and port:
        global _statsd
        _statsd = Server(pct_threshold=100, debug=_config.get("debug", False))

        def _start():
            try:
                _statsd.serve(graphite_host=host, graphite_port=port)
                logger.info("Metrics server started, emitting stats to graphite at %s:%s" % (host, port))
            except:
                logger.warn("Unable to start metrics UDP server at port 8125 - perhaps one is already running?")
        gevent.spawn(_start)
    else:
        logger.warn("Graphite is not configured, metrics will not be collected")


def stop_graphite_proxy():
    global _statsd
    if _statsd:
        _statsd.stop()
        _statsd = None


def metric(name, delta=1):
    """
    Convenience decorator used for incrementing an arbitrary stats key when a function is invoked.

    >>> from metrics import metric
    >>>
    >>> @metric("get_toplist")
    >>> def get_toplist():
    >>>     return

    @param name: the stats key
    @type name: str
    @param delta: the value to update
    @type delta: int
    """
    def _metric(func):
        def _wrapper(*args, **kwargs):
            res = func(*args, **kwargs)
            Metric.add(name, delta)
            return res

        return _wrapper

    return _metric


def timing(name):
    """
    Convenience decorator used for timing a function, i.e. track and store the execution time.

    >>> from metrics import timing
    >>>
    >>> @timing("execution_time.get_toplist")
    >>> def get_toplist():
    >>>     return

    @param name: the stats key
    @type name: str
    """
    def _timing(func):
        def _wrapper(*args, **kwargs):
            start = get_time()
            res = func(*args, **kwargs)
            elapsed_time = get_time() - start
            Metric.timing(name, elapsed_time)
            return res

        return _wrapper

    return _timing


class _Timing(object):
    def __init__(self, name):
        self.name = name
        self.start = get_time()

    def done(self):
        if not self.start:
            return # already submitted once
        elapsed_time = get_time() - self.start
        Metric.timing(self.name, elapsed_time)
        self.start = None  # prevent further submitting


class Metric(object):
    """
    The metrics client that communicates with graphite via local pystatsd.

    >>> from metrics import Metric
    >>> Metric.add("foo.bar.baz")
    >>> Metric.timing("foo.bar.millis", 123)
    """

    _client = Client()

    @classmethod
    def _add_namespace(cls, name):
        namespace = _config.get("namespace")
        return "%s.%s" % (namespace, name) if namespace else name


    @classmethod
    def add(cls, name, delta=1):
        """
        Updates a stats counter by arbitrary value (increments by one by default).

        >>> Metric.add("foo.bar.baz")      # increments by one
        >>> Metric.add("baz.bar.foo", 10)  # adds 10 to the stats counter

        @param name: the stats key
        @type name: str
        @param delta: the value to update
        @type delta: int
        """
        if not cls._client:
            return
        if not name:
            return
        if not delta:
            return

        cls._client.update_stats(cls._add_namespace(name), delta)

    @classmethod
    def timing(cls, name, time):
        """
        Submits time value for a given stats key.

        >>> Metric.timing("execution.time.baz", 123)

        @param name: the stats key
        @type name: str
        @param time: the time value to submit (in seconds)
        @type time: int or float
        """
        if not cls._client:
            return
        if not name:
            return
        if time:
            time = float(time)
        if not time:
            return

        millis = int(time * 1000 + .5)
        cls._client.timing(cls._add_namespace(name), millis)

    @classmethod
    def start_timing(cls, name):
        """
        Starts and returns a timing instance that tracks time for a given stats key. The stats
        will be updated once done() is invoked on the returned timing instance.

        >>> timer = Metric.start_timing("execution.time.baz")
        >>> # do stuff here...
        >>> timer.done()  # submits stats

        @param name: the stats key
        @type name: str
        @rtype: _Timing
        """
        return _Timing(name)
