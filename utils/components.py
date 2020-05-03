import heapq
from queue import Queue
import random

class FutureEventsList:
    def __init__(self, first=None):
        self._events = [first]
        self._time = 0

    @property
    def time(self):
        return self._time

    def put(self, time: int, event):
        heapq.heappush(self._events, (self._time + time, event))

    def get(self):
        event = heapq.heappop(self._events)
        self._time = event[0]
        return event[1]


class ResourceException(Exception):
    def __init__(self, res):
        message = f"Resource {res.name} is already {'busy' if res.busy else 'free'}"
        super().__init__(message)


class Resource:
    def __init__(self, name: str, busy: bool = False):
        self._name = name
        self._busy = busy

    @property
    def name(self):
        return self._name

    @property
    def busy(self):
        return self._busy

    def act(self, action):
        """ :param action: Handler.FREE or Handler.TAKE """
        if action == self.busy:
            raise ResourceException(self)
        self._busy = action


class Handler:
    TAKE = True
    FREE = False

    def __init__(self, func, args_list = []):
        self._function = func
        self._args_list = args_list

    def _take_resource(resource, transact, queue = None):
        if resource.busy:
            if queue:
                queue.put(transact)
            else:
                return transact
        else:
            resource.act(TAKE)

    def __call__(self, future_events_list):
        self._function(future_events_list, self._args_list)


class Event:
    def __init__(self, name: str, handler: Handler):
        self.name = name
        self.handler = handler


class Model:
    def __init__(self, queues, resources, handlers, parameters, first_event, finish_func):
        self._queues = queues
        self._resources = resources
        self._handlers = handlers
        self._parameters = parameters
        self._future_events_list = FutureEventsList(first_event)
        self._finish_func = None

    def step():
        self._future_events_list.get()[1].handler.call(future_events_list)

    def iteration():
        while self.finish_func() == True:
            self.step()

def exp_time(avg):
    return random.expovariate(1.0/avg)
