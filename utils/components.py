import heapq
import random
from typing import Callable


class FutureEventsList:
    def __init__(self, first=None):
        self._events = []
        if first is not None:
            self._events.append(first)
        self._time = 0

    @property
    def time(self):
        return self._time

    def put(self, time: float, event):
        heapq.heappush(self._events, (self._time + time, event))

    def get(self):
        event = heapq.heappop(self._events)
        self._time = event[0]
        return event[1]


class Component:
    def __init__(self, name: str, distribution_law):
        self._name = name
        self._distribution_law = distribution_law
        self.stats = {}

    @property
    def name(self):
        return self._name

    def generate_event(self):
        return self._distribution_law(), Event(f'От {self._name}', self)

    def __call__(self, events_list):
        pass


class Resource(Component):
    def __init__(self, name: str, distribution_law):
        super().__init__(name, distribution_law)
        self._name = name
        self._transaction = None
        self.stats['load'] = 0.0
        self.stats['load_start'] = -1.0

    @property
    def name(self):
        return self._name

    def busy(self):
        return self._transaction is not None

    def setBusy(self, transaction):
        self._transaction = transaction


class Event:
    def __init__(self, name: str, handler: Callable):
        self.name = name
        self.handler = handler


class ExponentialDistribution:
    def __init__(self, avg):
        self._avg = avg

    def __call__(self):
        return random.expovariate(1.0/self._avg)