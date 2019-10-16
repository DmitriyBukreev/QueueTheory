import heapq
from queue import Queue
from collections import namedtuple
from typing import Union, Callable, Iterable, Type, Tuple, TypeVar
from abc import ABC, abstractmethod

Transaction = namedtuple('Transaction', 'name')


class Event:
    __slots__ = 'transaction', 'src', 'dst'

    def __init__(self, transaction: 'Transaction', src: Callable = None, dst: Callable = None):
        self.transaction = transaction
        self.src = src
        self.dst = dst

    def __lt__(self, other):
        return self


class FutureEventsList:
    def __init__(self):
        self._events = []

    def put(self, time: int, event):
        heapq.heappush(self._events, (time, event))

    def get(self):
        return heapq.heappop(self._events)

# TODO update this code
# class QueueSet:
#     def __init__(self, queues: Iterable[Queue]):
#         self._queues = queues
#
#     def put(self, item):
#         """ Puts transaction in queue with minimal number of transactions """
#         chosen_queue = min(self._queues, key=lambda x: x.qsize())
#         chosen_queue.put(item)
#
#     def get(self):
#         """ Gets transaction from queue with maximal number of transactions """
#         chosen_queue = max(self._queues, key=lambda x: x.qsize())
#         return chosen_queue.get()
#
#     def empty(self):
#         return all([queue.empty() for queue in self._queues])
#
#     def full(self):
#         return all([queue.full() for queue in self._queues])


class QueueWithStats(ABC):
    def __init__(self):
        pass


AnyComponent = TypeVar('AnyComponent', 'Component', 'Generator', 'Resource')


class Component(ABC):
    def __init__(self, release_law: Callable, dst: AnyComponent = None):
        self._dst = dst
        self._release_law = release_law

    @abstractmethod
    def get_event(self) -> Tuple[int, Event]:
        pass

    @abstractmethod
    def incoming(self, transaction: Transaction) -> Tuple[int, Event]:
        pass

    @abstractmethod
    def outgoing(self) -> Union[Tuple[int, Event], None]:
        pass


class Generator(Component):
    def __init__(self, name: str, tr_name: str, release_law: Callable, dst: AnyComponent = None):
        super().__init__(release_law, dst)
        self._tr_name = tr_name
        self._name = name
        self._counter = 0

    @property
    def transaction_name(self):
        """ STATS: Name of released transactions """
        return self._tr_name

    @property
    def name(self):
        """ STATS: Generator name """
        return self._name

    @property
    def counter(self):
        """ STATS: Number of released transactions """
        # Counter gets increased each time the event is put into future events list
        # So the real number of released transactions is _counter - 1
        return self._counter - 1 if self._counter > 0 else 0

    def get_event(self):
        self._counter += 1
        return self._release_law(), Event(Transaction(self._tr_name), self.outgoing,
                                          self._dst.incoming if self._dst else None)

    def outgoing(self) -> Union[Tuple[int, Event], None]:
        return self.get_event()

    def incoming(self, transaction: Transaction) -> Tuple[int, Event]:
        pass


# TODO Set of Resources as next
class Resource(Component):
    def __init__(self, name: str, queue: Union[Type[Queue], None],
                 release_law: Callable, dst: AnyComponent = None):
        super().__init__(release_law, dst)
        self._name = name
        self._queue = queue
        self._transaction = None
        self._counter = 0
        self._prev_time = 0
        self._time = 0
        self._busy_time = 0

    @property
    def name(self):
        """ STATS: Name of resource """
        return self._name

    @property
    def counter(self):
        """ STATS: Number of released transactions """
        return self._counter - 1 if self._counter > 0 else 0

    @property
    def busy_time(self):
        """ STATS: Total time of processing """
        return self._busy_time

    @property
    def state(self):
        """ STATS: Current state of resource """
        return 'Busy' if self._transaction else 'Free'

    def get_event(self) -> Tuple[int, Event]:
        self._counter += 1
        self._prev_time = self._time
        self._busy_time += self._prev_time
        self._time = self._release_law()
        return self._time, Event(self._transaction, self.outgoing,
                                 self._dst.incoming if self._dst else None)

    def incoming(self, transaction: Transaction) -> Tuple[int, Event]:
        if self._transaction is None:                    # Resource is free
            if self._queue and not self._queue.empty():  # TODO Should I even check that?
                self._transaction = self._queue.get()
                if not self._queue.full():
                    self._queue.put(transaction)
            else:
                self._transaction = transaction
            return self.get_event()
        elif self._queue and not self._queue.full():
            self._queue.put(transaction)

    def outgoing(self) -> Union[Tuple[int, Event], None]:
        if self._queue and not self._queue.empty():
            self._transaction = self._queue.get()
            return self.get_event()
        else:
            self._transaction = None
            return None


class Model:
    def __init__(self, generators: Iterable[Generator], resources: Iterable[Resource], maxtime: int = 100):
        self._generators = generators
        self._resources = resources
        self._felist = FutureEventsList()
        self._time = 0
        self._maxtime = maxtime

    def run(self):
        for generator in self._generators:
            time_and_event = generator.outgoing()
            self._felist.put(*time_and_event)

        while True:
            time, event = self._felist.get()
            if time > self._maxtime:
                break
            self._time = time
            if event.src:
                time_and_event = event.src()
                if time_and_event:
                    o_time, o_event = time_and_event
                    self._felist.put(self._time + o_time, o_event)
            if event.dst:
                time_and_event = event.dst(event.transaction)
                if time_and_event:
                    i_time, i_event = time_and_event
                    self._felist.put(self._time + i_time, i_event)
