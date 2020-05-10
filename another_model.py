from utils.components import Resource, Handler, FutureEventsList, Event, exp_time
from queue import Queue

class Generator():
    def __init__(self, type, queue, resource):
        self._type = type
        self._queue = queue
        self._resource = resource

    def arrival(self):
        stats.count_arrived(self._type)

        if not self._resource.busy:
            log_event(f'Заявка типа {self._type + 1} заходит на устройство 1, занимая его', 0)
            self._resource.sieze(Transact(events_list.time, self._type))
        else:
            qsize = self._queue.qsize()
            log_event(f'Заявка типа {self._type + 1} пришла на устройство 1, а оно занято', qsize)
            if qsize < 4:
                self._queue.put(Transact(events_list.time, self._type))
                log_note('в очереди есть место, заявка встает в очередь', qsize + 1)
            else:
                stats.count_dropped(self._type, self._type, events_list.time)
                log_note('в очереди нету места, заявка сбрасывается', -1)

        events_list.put(exp_time(intensities[self._type]), self.arrival)

class ResourceOne:
    def __init__(self, queues, queue_three, resource_two):
        self._queues = queues
        self._queue_three = queue_three
        self._resource_two = resource_two
        self._transact = None

    @property
    def busy(self):
        return True if self._transact != None else False

    def sieze(self, transact):
        self._transact = transact
        events_list.put(exp_time(intensities[2]), self.release_one)
        stats.start_load(0)

    def release_one(self):
        transact = self._transact
        self._transact = None
        stats.count_load(0)
        log_event(f'Заявка типа {transact.type + 1} покинула устройство 1', self._queues[transact.type].qsize())

        if not self._queues[0].empty():
            self.sieze(self._queues[0].get())
            log_note('заявка из очереди 1 занимает устройство 1', self._queues[0].qsize())
        elif not self._queues[1].empty():
            self.sieze(self._queues[1].get())
            log_note('заявка из очереди 2 занимает устройство 1', self._queues[1].qsize())
        else:
            log_note('обе очереди пусты, устройство 1 никто не занимает', -1)

        if not self._queue_three.empty():
            log_note('заявка пришла на устройство 2, а оно занято', self._queue_three.qsize() - 1)
            if self._queue_three.qsize() <= 6:
                self._queue_three.put(transact)
                log_note('в очереди есть место, заявка встает в очередь', self._queue_three.qsize() - 1)
            else:
                stats.count_dropped(2, transact.type, transact.time)
                log_note('в очереди нету места, заявка сбрасывается', -1)
        else:
            events_list.put(exp_time(intensities[3]), self._resource_two.release_two)
            log_note('покинувшая заявка заходит на устройство 2, занимая его', 0)
            stats.start_load(1)
            self._queue_three.put(transact)

class ResourceTwo():
    def __init__(self, queue_three):
        self._queue = queue_three
        self._passed = 0

    def release_two(self):
        transact = self._queue.get()
        stats.count_load(1)

        if not self._queue.empty():
            events_list.put(exp_time(intensities[3]), self.release_two)
            log_event('Заявка уходит с устройства 2, ee место занимает следующая', self._queue.qsize() - 1)
            stats.start_load(1)
        else:
            log_event('Заявка уходит с устройства 2 и покидает модель', 0)

        stats.count_passed(transact.type, transact.time)

class Stats:
    def __init__(self):
        self.arrived = [0,0]
        self.dropped = [0,0,0]
        self.load_starts = [0.0, 0.0]
        self.load = [0.0, 0.0]
        self.time_counter = [0.0, 0.0]
        self.dropped_time_counter = [0.0, 0.0]
        self.count_in_model = [0,0]
        self.count_counter = [0.0, 0.0]
        self.last_count_change_time = [0,0]

    def add(self, some):
        self.arrived[0] += some.arrived[0]
        self.arrived[1] += some.arrived[1]
        self.dropped[0] += some.self.dropped[0]
        self.dropped[1] += some.self.dropped[1]
        self.dropped[2] += some.self.dropped[2]
        self.load[0] += some.load[0]
        self.load[1] += some.load[1]
        self.time_counter[0] += some.time_counter[0]
        self.time_counter[1] += some.time_counter[1]
        self.dropped_time_counter[0] += some.dropped_time_counter[0]
        self.dropped_time_counter[1] += some.dropped_time_counter[1]
        self.count_counter[0] += some.count_counter[0]
        self.count_counter[1] += some.count_counter[1]

    def count_arrived(self, type):
        self.count_count(type, 1)
        self.arrived[type] += 1

    def count_dropped(self, queue_number, type, time):
        self.count_count(type, -1)
        self.dropped[queue_number] += 1
        self.dropped_time_counter[type] += events_list.time - time

    def count_passed(self, type, time):
        self.count_count(type, -1)
        self.time_counter[type] += events_list.time - time

    def start_load(self, res_number):
        self.load_starts[res_number] = events_list.time

    def count_load(self, res_number):
        self.load[res_number] += events_list.time - self.load_starts[res_number]

    def count_count(self, type, change):
        self.count_counter[type] += self.count_in_model[type] * (events_list.time - self.last_count_change_time[type])
        self.count_in_model[type] += change
        self.last_count_change_time[type] = events_list.time

    def get_time(self, time, iterations):
        return time * iterations

    def write_stats(self, file, iterations):
        file.write(f'\nЗа {iterations} итераций в модель поступило:\n')
        file.write(f'\t- {self.arrived[0]} заявок типа 1\n')
        file.write(f'\t- {self.arrived[1]} заявок типа 2\n')
        file.write(f'\t- {self.arrived[0] + self.arrived[1]} заявок всего\n')
        file.write(f'\nБыло потеряно:\n')
        file.write(f'\t- {self.dropped[0]} заявок на входе очереди 1\n')
        file.write(f'\t- {self.dropped[1]} заявок на входе очереди 2\n')
        file.write(f'\t- {self.dropped[2]} заявок на входе очереди 3\n')
        file.write(f'\t- {self.dropped[0] + self.dropped[1] + self.dropped[2]} заявок всего\n')
        file.write(f'\nБыло загружено:\n')
        file.write(f'\t- На {((self.load[0] / self.get_time(180, iterations)) * 100):2.2f}% устройство 1\n')
        file.write(f'\t- На {((self.load[1] / self.get_time(180, iterations)) * 100):2.2f}% устройство 2\n')
        file.write(f'\nСреднее время обслуживания составило:\n')
        file.write(f'\t- {self.time_counter[0]/(self.arrived[0] - self.dropped[0]):2.2f} для заявок типа 1, {(self.time_counter[0] + self.dropped_time_counter[0])/self.arrived[0]:2.2f} c учетом сброшенных\n')
        file.write(f'\t- {self.time_counter[1]/(self.arrived[1] - self.dropped[1]):2.2f} для заявок типа 2, {(self.time_counter[1] + self.dropped_time_counter[1])/self.arrived[1]:2.2f} c учетом сброшенных\n')
        file.write(f'\t- {(self.time_counter[0] + self.time_counter[1])/(self.arrived[0] - self.dropped[0] + self.arrived[1] - self.dropped[1]):2.2f} для всех заявок, {(self.time_counter[0] + self.time_counter[1] + self.dropped_time_counter[0] + self.dropped_time_counter[1])/(self.arrived[0] + self.arrived[1]):2.2f} с учетом сброшенных\n')
        file.write(f'\nВ среднем в модели одновременно находилось:\n')
        file.write(f'\t- {self.count_counter[0]/self.get_time(180, iterations):2.2f} заявок типа 1\n')
        file.write(f'\t- {self.count_counter[1]/self.get_time(180, iterations):2.2f} заявок типа 2\n')
        file.write(f'\t- {(self.count_counter[0] + self.count_counter[1])/self.get_time(180, iterations):2.2f} заявок всего\n\n')

class Transact:
    def __init__(self, time, type):
        self.time = time
        self.type = type

def log_event(text, q_size):
    log.write(f'Время {events_list.time:3.2f} - событие: {text:60}')
    log.write('\n' if q_size < 0 else f' - заявок в этой очереди {q_size}\n')

def log_note(text, q_size):
    log.write(f'\tПри этом {text:45}')
    log.write('\n' if q_size < 0 else f' - заявок в этой очереди {q_size}\n')

log = open('log1.txt', 'w')
results = open('results1.txt', 'w')

stats = Stats()

for i in range(10000):
    log.write(f'Итерация {i + 1}:\n')

    queues = (Queue(), Queue(), Queue())

    resource_two = ResourceTwo(queues[2])
    resource_one = ResourceOne(queues[:2], queues[2], resource_two)
    generator_one = Generator(0, queues[0], resource_one)
    generator_two = Generator(1, queues[1], resource_one)

    intensities = (10, 3, 1.8, 2)

    events_list = FutureEventsList((exp_time(intensities[0]), generator_one.arrival))
    events_list.put(exp_time(intensities[1]), generator_two.arrival)

    while True:
        event = events_list.get()
        if events_list.time <= 180:
            event()
        else:
            break

    stats.write_stats(log, i + 1)
stats.write_stats(results, i + 1)

log.close()
results.close()
