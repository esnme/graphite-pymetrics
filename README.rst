graphite-pymetrics
==================
graphite-pymetrics is a lightweight Python framework which makes it super simple to add application metrics
that is sent to a remote graphite/carbon server.

All that is needed is this package (which also includes pystatsd) and access to a remote graphite server.

To install it just run Pip as usual::

    $ pip install graphite-pymetrics

Package requirements:
  - pystatsd==0.1.6
  - gevent

=====
Usage
=====
Make sure there is a local graphite proxy running - start it at an early point in your application:


    from metrics.graphite import start_graphite_proxy
    start_graphite_proxy({"host": "graphite.mycompany.com", "port": 2003})


The proxy is pystatsd, a local server that receives UDP packets from the metrics client and periodically
emits data to graphite over TCP.

~~~~~~~~
Counters
~~~~~~~~
To add a counter for anything anywhere in your code, use Metric.add:


    from metrics import Metric

    Metric.add("foo.bar")


Use the @metric decorator to count specific method invocations:


    from metrics import metric

    @metric("bar.baz")
    def foo():
        # do stuff here


~~~~~~
Timing
~~~~~~
There are several ways to log timing. The most naive way is to first measure time manually and then submit it:


    from metrics import Metric
    import time

    start = time.time()
    # do stuff
    elapsed = time.time() - start
    Metric.timing("do.stuff", elapsed)


An easier way is to to let the metric client keep track of time with Metric.start_timing and call done() on the
returned timing instance. Following is an example for measuring time consumed for every endpoint individually
in a Flask webapp:


    from metrics import Metric
    from flask import Blueprint, current_app, request, g

    app = Blueprint("myapp", __name__)

    @app.before_request
    def before_request():
        try:
            g.timing = Metric.start_timing(str(request.endpoint))  # start timing
        except:
            current_app.logger.error("Unable to time call for 'request.endpoint'")

    @app.teardown_request
    def teardown_request(exc):
        try:
            g.timing.done()                                        # stop timing
        except:
            current_app.logger.error("Timing not available")


Similar to the @metric decorator there is a @timing decorator which is used to measure time for specific methods:


    from metrics import timing

    @timing("heavy.task")
    def heavy_task(x, y, z):
        # do heavy stuff here

