from utils.components import Resource, Handler, FutureEventsList, Event, exp_time
from collections import namedtuple
from queue import Queue

def arrival(arrival_where):
    type = 0 if arrival_where[-1] == 'e' else 1;
    qsize = q_size(type)

    if(resource_one.queues[0].empty() and resource_one.queues[1].empty()):
        resource_one.which = type
        events_list.put(exp_time(intensities[1]), Event('Release one', release_one_handler))
        log_event(f'Заявка типа {type + 1} заходит на устройство 1, занимая его', 0)
        resource_one.queues[type].put(Transact(events_list.time, type))
    else:
        log_event(f'Заявка типа {type + 1} пришла на устройство 1, а оно занято', qsize)
        if (qsize < 4):
            resource_one.queues[type].put(Transact(events_list.time, type))
            log_note('в очереди есть место, заявка встает в очередь', qsize + 1)
        else:
            log_note('в очереди нету места, заявка сбрасывается', -1)

    events_list.put(exp_time(intensities[type]), Event(arrival_where, arrival_handler))

def release_one(release_what):
    transact = resource_one.queues[resource_one.which].get()
    log_event(f'Заявка типа {resource_one.which + 1} покинула устройство 1', resource_one.queues[resource_one.which].qsize())

    if(not resource_one.queues[0].empty()):
        resource_one.which = 0
        events_list.put(exp_time(intensities[2]), Event('Release one', release_one_handler))
        log_note('заявка из очереди 1 занимает устройство 1', resource_one.queues[0].qsize() - 1)
    elif(not resource_one.queues[1].empty()):
        resource_one.which = 1
        events_list.put(exp_time(intensities[2]), Event('Release one', release_one_handler))
        log_note('заявка из очереди 2 занимает устройство 1', resource_one.queues[1].qsize() - 1)
    else:
        log_note('обе очереди пусты, устройство 1 никто не занимает', -1)

    if(not queue_three.empty()):
        log_note('заявка пришла на устройство 2, а оно занято', queue_three.qsize() - 1)
        if(queue_three.qsize() <= 6):
            queue_three.put(transact)
            log_note('в очереди есть место, заявка встает в очередь', queue_three.qsize() - 1)
        else:
            log_note('в очереди нету места, заявка сбрасывается', -1)
    else:
        events_list.put(exp_time(intensities[3]), Event('Release two', release_two_handler))
        log_note('покинувшая заявка заходит на устройство 2, занимая его', 0)
        queue_three.put(transact)

def release_two(release_what):
    queue_three.get()

    if(not queue_three.empty()):
        events_list.put(exp_time(intensities[3]), Event('Release two', release_two_handler))
        log_event('Заявка уходит с устройства 2, ee место занимает следующая', queue_three.qsize() - 1)
    else:
        log_event('Заявка уходит с устройства 2 и покидает модель', 0)

class Stats:
    def __init__(self):
        pass

class Transact:
    def __init__(self, time, type):
        self.time = time
        self.type = type

    def write_stats(self, file):
        pass

def log_event(text, q_size):
    log.write(f'Время {int(events_list.time):3} - событие: {text:60}')
    log.write('\n' if (q_size < 0) else f' - заявок в этой очереди {q_size}\n')

def log_note(text, q_size):
    log.write(f'\tПри этом {text:45}')
    log.write('\n' if (q_size < 0) else f' - заявок в этой очереди {q_size}\n')

def q_size(which):
    if (resource_one.queues[which].empty()):
        return 0
    elif (resource_one.which == which):
        return resource_one.queues[which].qsize() - 1
    else:
        return resource_one.queues[which].qsize()

log = open('log1.txt', 'w')
results = open('results1.txt', 'w')

stats = Stats()
resource_one = Resource('First resource')
resource_one.which = 0
resource_one.queues = (Queue(), Queue())

queue_three = Queue()

arrival_handler = Handler(arrival)
release_one_handler = Handler(release_one)
release_two_handler = Handler(release_two)

intensities = (10, 3, 1.8, 2)

events_list = FutureEventsList((exp_time(intensities[0]), Event('Arrival one', arrival_handler)))
events_list.put(exp_time(intensities[1]), Event('Arrival two', arrival_handler))

while True:
    event = events_list.get()
    if events_list.time <= 180:
        event.handler._function(event.name)
    else:
        break

log.close()
results.close()
