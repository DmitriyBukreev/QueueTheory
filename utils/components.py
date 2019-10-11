import heapq
from queue import Queue

class FutureEventsList:
    def __init__(self, first=None):
        self._events = [first]

    def put(self, time: int, event):
        heapq.heappush(self._events, (time, event))

    def get(self):
        return heapq.heappop(self._events)


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

    def __init__(self, action, resource: Resource, queue: Queue = None):
        self._action = action
        self._resource = resource
        self._queue = queue

    def _take_resource(self):
        if self._resource.busy and self._queue:
            pass

    def _free_resource(self):
        if self._resource.busy and self._queue:
            self._queue.put()

    def __call__(self):
        if self._action == self.TAKE:
            self._take_resource()
        else:
            self._free_resource()


class Event:
    def __init__(self, name: str, handler: Handler):
        self.name = name
        self.handler = handler


class Model:
    pass


