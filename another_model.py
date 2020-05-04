from utils.components import Resource, FutureEventsList, ExponentialDistribution, Component
from queue import Queue


class ResourceTwo(Resource):
    def __init__(self, queue_three, distribution_law):
        super().__init__('Устройство 2', distribution_law)
        self._queue_three = queue_three

    def __call__(self, events_list):
        stats.count_load(1)
        transaction = self._transaction

        if not self._queue_three.empty():
            events_list.put(*self.generate_event())
            self.setBusy(self._queue_three.get())
            log_event('Заявка уходит с устройства 2, ee место занимает следующая', self._queue_three.qsize())
            stats.start_load(1)
        else:
            self.setBusy(None)
            log_event('Заявка уходит с устройства 2 и покидает модель', 0)

        stats.count_passed(transaction.type, transaction.time)


class ResourceOne(Resource):
    def __init__(self, queue_one, queue_two, queue_three, resource_two, distribution_law):
        super().__init__('Устройство 1', distribution_law)
        self._queue_one = queue_one
        self._queue_two = queue_two
        self._queue_three = queue_three
        self._resource_two = resource_two
        self._transaction = None

    def __call__(self, events_list):
        stats.count_load(0)
        transaction = self._transaction
        queue = self._queue_one if transaction.type == 0 else self._queue_two
        log_event(f'Заявка типа {transaction.type + 1} покинула устройство 1',
                  queue.qsize())

        if not self._queue_one.empty():
            self.setBusy(self._queue_one.get())
            events_list.put(*self.generate_event())
            log_note('заявка из очереди 1 занимает устройство 1', self._queue_one.qsize())
            stats.start_load(0)
        elif not self._queue_two.empty():
            self.setBusy(self._queue_two.get())
            events_list.put(*self.generate_event())
            log_note('заявка из очереди 2 занимает устройство 1', self._queue_one.qsize())
        else:
            self.setBusy(None)
            log_note('обе очереди пусты, устройство 1 никто не занимает', -1)

        if self._resource_two.busy():
            log_note('заявка пришла на устройство 2, а оно занято', self._queue_three.qsize())
            if self._queue_three.qsize() < 6:
                self._queue_three.put(transaction)
                log_note('в очереди есть место, заявка встает в очередь', self._queue_three.qsize())
            else:
                stats.count_dropped(2, transaction.type, transaction.time)
                log_note('в очереди нету места, заявка сбрасывается', -1)
        else:
            self._resource_two.setBusy(transaction)
            events_list.put(*self._resource_two.generate_event())
            log_note('покинувшая заявка заходит на устройство 2, занимая его', 0)
            stats.start_load(1)


class Generator(Component):
    def __init__(self, type, queue, resource: ResourceOne, distribution_law):
        super().__init__(f"Поток {type + 1}", distribution_law)
        self._type = type
        self._queue = queue
        self._resource = resource

    def __call__(self, events_list):
        stats.count_arrived(self._type)

        if not self._resource.busy():
            self._resource.setBusy(Transact(events_list.time, self._type))
            events_list.put(*self._resource.generate_event())
            log_event(f'Заявка типа {self._type + 1} заходит на устройство 1, занимая его', 0)
            stats.start_load(0)
        else:
            size = self._queue.qsize()
            log_event(f'Заявка типа {self._type + 1} пришла на устройство 1, а оно занято', size)
            if size < 4:
                self._queue.put(Transact(events_list.time, self._type))
                log_note('в очереди есть место, заявка встает в очередь', size + 1)
            else:
                stats.count_dropped(self._type, self._type, events_list.time)
                log_note('в очереди нету места, заявка сбрасывается', -1)

        events_list.put(*self.generate_event())


# def arrival(arrival_where):
#     type = 0 if arrival_where[-1] == 'e' else 1
#     stats.count_arrived(type)
#     qsize = q_size(type)
#
#     if resource_one.queues[0].empty() and resource_one.queues[1].empty():
#         resource_one.which = type
#         events_list.put(exp_time(intensities[1]), Event('Release one', release_one_handler))
#         log_event(f'Заявка типа {type + 1} заходит на устройство 1, занимая его', 0)
#         resource_one.queues[type].put(Transact(events_list.time, type))
#         stats.start_load(0)
#     else:
#         log_event(f'Заявка типа {type + 1} пришла на устройство 1, а оно занято', qsize)
#         if qsize < 4:
#             resource_one.queues[type].put(Transact(events_list.time, type))
#             log_note('в очереди есть место, заявка встает в очередь', qsize + 1)
#         else:
#             stats.count_dropped(type, type, events_list.time)
#             log_note('в очереди нету места, заявка сбрасывается', -1)
#
#     events_list.put(exp_time(intensities[type]), Event(arrival_where, arrival_handler))
#
#
# def release_one(release_what):
#     transact = resource_one.queues[resource_one.which].get()
#     stats.count_load(0)
#     log_event(f'Заявка типа {resource_one.which + 1} покинула устройство 1', resource_one.queues[resource_one.which].qsize())
#
#     if not resource_one.queues[0].empty():
#         resource_one.which = 0
#         events_list.put(exp_time(intensities[2]), Event('Release one', release_one_handler))
#         log_note('заявка из очереди 1 занимает устройство 1', resource_one.queues[0].qsize() - 1)
#         stats.start_load(0)
#     elif not resource_one.queues[1].empty():
#         resource_one.which = 1
#         events_list.put(exp_time(intensities[2]), Event('Release one', release_one_handler))
#         log_note('заявка из очереди 2 занимает устройство 1', resource_one.queues[1].qsize() - 1)
#         stats.start_load(0)
#     else:
#         log_note('обе очереди пусты, устройство 1 никто не занимает', -1)
#
#     if not queue_three.empty():
#         log_note('заявка пришла на устройство 2, а оно занято', queue_three.qsize() - 1)
#         if queue_three.qsize() <= 6:
#             queue_three.put(transact)
#             log_note('в очереди есть место, заявка встает в очередь', queue_three.qsize() - 1)
#         else:
#             stats.count_dropped(2, transact.type, transact.time)
#             log_note('в очереди нету места, заявка сбрасывается', -1)
#     else:
#         events_list.put(exp_time(intensities[3]), Event('Release two', release_two_handler))
#         log_note('покинувшая заявка заходит на устройство 2, занимая его', 0)
#         stats.start_load(1)
#         queue_three.put(transact)
#
#
# def release_two(release_what):
#     transact = queue_three.get()
#     stats.count_load(1)
#
#     if not queue_three.empty():
#         events_list.put(exp_time(intensities[3]), Event('Release two', release_two_handler))
#         log_event('Заявка уходит с устройства 2, ee место занимает следующая', queue_three.qsize() - 1)
#         stats.start_load(1)
#     else:
#         log_event('Заявка уходит с устройства 2 и покидает модель', 0)
#
#     stats.count_passed(transact.type, transact.time)


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
        self.count_count(type)
        self.arrived[type] += 1
        self.count_in_model[type] += 1
        self.last_count_change_time[type] = events_list.time

    def count_dropped(self, queue_number, type, time):
        self.count_count(type)
        self.dropped[queue_number] += 1
        self.dropped_time_counter[type] += events_list.time - time
        self.count_in_model[type] -= 1
        self.last_count_change_time[type] = events_list.time

    def count_passed(self, type, time):
        self.count_count(type)
        self.time_counter[type] += events_list.time - time
        self.count_in_model[type] -= 1
        self.last_count_change_time[type] = events_list.time

    def start_load(self, res_number):
        self.load_starts[res_number] = events_list.time

    def count_load(self, res_number):
        self.load[res_number] += events_list.time - self.load_starts[res_number]

    def count_count(self, type):
        self.count_counter[type] += self.count_in_model[type] * (events_list.time - self.last_count_change_time[type])

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

    def write_stats(self, file):
        pass


def log_event(text, q_size):
    log.write(f'Время {events_list.time:3.2f} - событие: {text:60}')
    log.write('\n' if (q_size < 0) else f' - заявок в этой очереди {q_size}\n')


def log_note(text, q_size):
    log.write(f'\tПри этом {text:45}')
    log.write('\n' if (q_size < 0) else f' - заявок в этой очереди {q_size}\n')


log = open('log1.txt', 'w')
results = open('results1.txt', 'w')

stats = Stats()


for i in range(1000):
    log.write(f'Итерация {i + 1}:\n')

    queue_one, queue_two, queue_three = Queue(), Queue(), Queue()
    resource_two = ResourceTwo(queue_three, ExponentialDistribution(2))
    resource_one = ResourceOne(queue_one, queue_two, queue_three, resource_two, ExponentialDistribution(1.8))
    generator_one = Generator(0, queue_one, resource_one, ExponentialDistribution(10))
    generator_two = Generator(1, queue_two, resource_one, ExponentialDistribution(3))

    events_list = FutureEventsList()
    events_list.put(*generator_one.generate_event())
    events_list.put(*generator_two.generate_event())

    while True:
        event = events_list.get()
        if events_list.time <= 180:
            event.handler(events_list)
        else:
            break

    stats.write_stats(log, i + 1)
stats.write_stats(results, i + 1)


log.close()
results.close()
