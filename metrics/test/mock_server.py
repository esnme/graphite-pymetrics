from socket import AF_INET, SOCK_DGRAM, socket
import re
import time

#
# A stripped copy of pystatsd.Server used for integration tests. The server dows not
# send any data to graphite, instead it takes a callback function that will receive
# the stats lines for verification (lines with empty stats and lines with "numStats" are pruned).
#

TIMER_MSG = '''stats.timers.%(key)s.lower %(min)s %(ts)s
stats.timers.%(key)s.count %(count)s %(ts)s
stats.timers.%(key)s.mean %(mean)s %(ts)s
stats.timers.%(key)s.upper %(max)s %(ts)s
stats.timers.%(key)s.upper_%(pct_threshold)s %(max_threshold)s %(ts)s
'''


class Server(object):
    def __init__(self, callback):
        self.callback = callback
        self.buf = 1024
        self.pct_threshold = 100
        self.counters = {}
        self.timers = {}

    def process(self, data):
        key, val = data.split(':')

        sample_rate = 1
        fields = val.split('|')
        if None == fields[1]:
            return

        if fields[1] == 'ms':
            if key not in self.timers:
                self.timers[key] = []
            self.timers[key].append(float(fields[0] or 0))
        else:
            if len(fields) == 3:
                sample_rate = float(re.match('^@([\d\.]+)', fields[2]).groups()[0])
            if key not in self.counters:
                self.counters[key] = 0
            self.counters[key] += float(fields[0] or 1) * (1 / sample_rate)

    def flush(self):
        ts = int(time.time())
        stat_string = ''
        for k, v in self.counters.items():
            v = float(v)
            if not v:
                continue
            msg = 'stats.%s %s %s\n' % (k, v, ts)
            stat_string += msg

            self.counters[k] = 0

        for k, v in self.timers.items():
            if len(v) > 0:
                v.sort()
                count = len(v)
                min = v[0]
                max = v[-1]

                mean = min
                max_threshold = max

                if count > 1:
                    thresh_index = int((self.pct_threshold / 100.0) * count)
                    max_threshold = v[thresh_index - 1]
                    total = sum(v[:thresh_index - 1])
                    mean = total / thresh_index

                self.timers[k] = []

                stat_string += TIMER_MSG % {
                    'key': k,
                    'mean': mean,
                    'max': max,
                    'min': min,
                    'count': count,
                    'max_threshold': max_threshold,
                    'pct_threshold': self.pct_threshold,
                    'ts': ts,
                }

        self.callback(stat_string)

    def serve(self):
        addr = ("localhost", 8125)
        self._sock = socket(AF_INET, SOCK_DGRAM)
        self._sock.bind(addr)

        try:
            while True:
                data, addr = self._sock.recvfrom(self.buf)
                if data:
                    self.process(data)
                    self.flush()
        except:
            pass  # hide greenlet errors

    def stop(self):
        self._sock.close()
