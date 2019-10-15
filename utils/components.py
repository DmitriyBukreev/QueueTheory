import heapq
from queue import Queue
from collections import namedtuple
from typing import Union, Callable, Iterable, Type

Transaction = namedtuple('Transaction', 'name')

Event = namedtuple('Event', ('transaction', 'outgoing', 'incoming'))


class FutureEventsList:
    def __init__(self, first=None):
        self._events = [first]

    def put(self, time: int, event):
        heapq.heappush(self._events, (time, event))

    def get(self):
        return heapq.heappop(self._events)


class Generator:
    def __init__(self, tr_name: str, next, release_law: Callable):
        self._tr_name = tr_name
        self._release_law = release_law
        self._next = next

    def outgoing(self):
        return self._release_law(), Event(Transaction(self._tr_name), self.outgoing, self._next.incoming)


class QueueSet:
    def __init__(self, queues: Iterable[Queue]):
        self._queues = queues

    def put(self, item):
        """ Puts transaction in queue with minimal number of transactions """
        chosen_queue = min(self._queues, key=lambda x: x.qsize())
        chosen_queue.put(item)

    def get(self):
        """ Gets transaction from queue with maximal number of transactions """
        chosen_queue = max(self._queues, key=lambda x: x.qsize())
        return chosen_queue.get()

    def empty(self):
        return all([queue.empty() for queue in self._queues])

    def full(self):
        return all([queue.full() for queue in self._queues])


# TODO Set of Resources as next
class Resource:
    def __init__(self, name: str, queue: Union[Type[Queue], QueueSet, None], next, release_law: Callable):
        self._name = name
        self._queue = queue
        self._next = next
        self._release_law = release_law
        self._transaction = None

    @property
    def name(self):
        return self._name

    def _time_and_event(self):
        return self._release_law(), Event(self._transaction, self.outgoing, self._next.incoming)

    def incoming(self, transaction: Transaction):
        if self._transaction is None:  # Resource is free
            if self._queue and not self._queue.empty():  # TODO Should I even check that?
                self._transaction = self._queue.get()
                if not self._queue.full():
                    self._queue.put(transaction)
            else:
                self._transaction = transaction
            return self._time_and_event()
        elif self._queue and not self._queue.full():
            self._queue.put(transaction)

    def outgoing(self):
        if self._queue and not self._queue.empty():
            self._transaction = self._queue.get()
            return self._time_and_event()
        else:
            self._transaction = None
            return None


class Model:
    def __init__(self, generators: Iterable[Generator], resources: Iterable[Resource], maxtime: int = 100):
        self._generators = generators
        self._resources = resources
        self._fte = FutureEventsList()
        self._time = 0
        self._maxtime = maxtime

    def run(self):
        for generator in self._generators:
            time_and_event = generator.outgoing()
            self._fte.put(*time_and_event)

        while self._time < self._maxtime:
            self._time, event = self._fte.get()
            time_and_event = event.outgoing()
            if time_and_event:
                o_time, o_event = time_and_event
                self._fte.put(self._time + o_time, o_event)
            i_time, i_event = event.incoming(event.transaction)
            self._fte.put(self._time + i_time, i_event)