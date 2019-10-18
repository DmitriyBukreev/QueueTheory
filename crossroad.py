from utils.components import Resource, Handler, FutureEventsList, Event
from collections import namedtuple
from queue import Queue
import random

def switch_phase():

    Crossroad.phase = not Crossroad.phase
    Crossroad.switch_time = events_list.time + Crossroad.phase_time()
    events_list.put(Crossroad.phase_time(), Event('Phase switch', phase_switch_handler))
    
    if Crossroad.is_green():
        events_list.put(0, Event('Car go', car_go_handler))
        log_event('Фаза переключилась на зеленый\n')
    else:
        log_event('Фаза переключилась на красный\n')
    
def new_car():

    events_list.put(exp_time(Handler.intensity), Event('New car', new_car_handler))
    
    if first_car.busy:
        first_car.queue.put(Car(events_list.time))
        log_event('Машина встала в очередь')
    else:
        if not Crossroad.is_green():
            if first_car.busy:
                first_car.queue.put(Car(events_list.time))
                log_event('Машина встала в очередь на красный')
            else:
                first_car.act(Handler.TAKE)
                first_car.car = Car(events_list.time)
                log_event('Машина встала на красный')
        else:
            stats.count_green_car()
            log_event('Машина проехала свободно')

def car_go():

    if not first_car.busy:
        return

    t = Crossroad.switch_time - events_list.time
    
    if t < Car.acceleration_time:
        acceleration_distance = ((Car.speed/Car.acceleration_time) * (t ** 2))/ 2
    else:
        acceleration_distance = ((Car.speed * Car.acceleration_time)/ 2) + (Car.speed * (t - Car.acceleration_time))
        
    if acceleration_distance < first_car.distance_from_cross:
        first_car.distance_from_cross = 0
        log_event('Машина не успела выехать до красного')
        return

    stats.count_car(first_car.car)

    if not first_car.queue.empty():
        first_car.car = first_car.queue.get()
        
        if Car.delay < (Crossroad.switch_time - events_list.time):
            first_car.distance_from_cross += Car.length
            events_list.put(Car.delay, Event('Car go', car_go_handler))
        else:
            first_car.distance_from_cross = 0
            
        log_event('Машина выехала. Есть еще')
    else:
        first_car.act(Handler.FREE)
        log_event('Последняя машина выехала. Свободно')
  
def log_event(text):
    log.write(f'Время {int(events_list.time):4} - машин стоит {how_many_cars():2} - событие: {text}\n')
    
def how_many_cars():
    if first_car.busy:
        return first_car.queue.qsize() + 1
    else:
        return 0
    
def exp_time(avg):
    return random.expovariate(1.0/avg)
    
def write_simulation_parameters(file, direction):
    file.write(f'{direction} новая машина в среднем раз в {Handler.intensity} c.\n')
    file.write(f'Длительность зеленой фазы светофора - {Crossroad.green_phase_time} с.\n')
    file.write(f'Длительность красной фазы светофора - {Crossroad.red_phase_time} c.\n')
    if Crossroad.is_green():
        file.write(f'Светофор начинает c зеленой фазы\n\n')
    else:
        file.write(f'Светофор начинает c красной фазы\n\n')
        
    
class Crossroad:
    GREEN = True
    RED = False
    phase = RED
    red_phase_time = 10
    green_phase_time = 20
    switch_time = red_phase_time
    
    def is_green():
        return Crossroad.phase
        
    def phase_time():
        if Crossroad.phase:
            return Crossroad.green_phase_time
        else:
            return Crossroad.red_phase_time
            
    def swap_phases():
        Crossroad.phase = not Crossroad.phase
        
        buffer = Crossroad.green_phase_time
        Crossroad.green_phase_time = Crossroad.red_phase_time
        Crossroad.red_phase_time = buffer
    
    
class Car:
    delay = 1
    length = 4
    speed = 17 #m/s
    acceleration_time = 5 #s
    
    def __init__(self, time):
        self.time = time

        
class Stats:
    def __init__(self):
        self.counter = 0
        self.green_counter = 0
        self.sum_time = 0
    
    def count_green_car(self):
        self.green_counter += 1
        
    def count_car(self, car):
        self.sum_time += (events_list.time - car.time)
        self.counter += 1
        
    def get_avg_queue_time(self):
        return self.sum_time/self.counter
        
    def get_avg_time_with_greens(self):
        return self.sum_time/(self.counter + self.green_counter)
    
    def get_avg_time_with_acceleration(self):
        return (self.sum_time + (2 * Car.acceleration_time * self.counter))/(self.counter + self.green_counter)
        
    def write_stats(self, file, direction):
        file.write(f'{direction} проехало машин: {self.counter}\n')
        file.write(f'Среднее время нахождения машины в очереди равно {self.get_avg_queue_time()}\n')
        file.write(f'С учетом проехавших свободно {self.get_avg_time_with_greens()}\n')
        file.write(f'Средние затраты на проезд перекрестка (торможение, очередь и разгон) {self.get_avg_time_with_acceleration()}\n\n')

intensities = [('С севера', 1),('C запада', 2),('С юга', 3),('С востока', 4)]
all_stats = []

log = open('log.txt', 'w')
results = open('results.txt', 'w')

for intensity in intensities:

    Handler.intensity = intensity[1]
    stats = Stats()
    
    write_simulation_parameters(log, intensity[0])
    write_simulation_parameters(results, intensity[0])

    for i in range(250):

        first_car = Resource('First car')
        first_car.distance_from_cross = 0
        first_car.queue = Queue()

        phase_switch_handler = Handler(switch_phase)
        new_car_handler = Handler(new_car)
        car_go_handler = Handler(car_go)

        events_list = FutureEventsList((Crossroad.switch_time, Event('Phase switch', phase_switch_handler)))
        events_list.put(exp_time(Handler.intensity), Event('New car', new_car_handler))

        while True:
            event = events_list.get()
            if events_list.time <= 1000:
                event.handler._function()
            else:
                break

        log.write('\n')
        stats.write_stats(log, intensity[0])
        
        Crossroad.switch_time = Crossroad.phase_time()
        
    Crossroad.swap_phases()
    stats.write_stats(results, intensity[0])
    all_stats.append(stats)
    
result_stats = Stats()
for stats in all_stats:
    result_stats.counter += stats.counter
    result_stats.green_counter += stats.green_counter
    result_stats.sum_time += stats.sum_time

result_stats.write_stats(log, 'Всего через перекресток')
result_stats.write_stats(results, 'Всего через перекресток')

results.close()
log.close()