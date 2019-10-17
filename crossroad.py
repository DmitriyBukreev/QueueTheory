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
            Car.count_green_car()
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
        log_event('Машина не успела выехать')
        return

    first_car.car.count_car()

    if not first_car.queue.empty():
        first_car.car = first_car.queue.get()
        
        if Car.delay < (Crossroad.switch_time - events_list.time):
            first_car.distance_from_cross += Car.length
            events_list.put(Car.delay, Event('Car go', car_go_handler))
        else:
            first_car.distance_from_cross = 0
            
        log_event('Машина выехала. Сзади еще')
    else:
        first_car.act(Handler.FREE)
        log_event('Машина выехала. Сзади свободно')
  
def log_event(text):
    log.write(str(int(events_list.time)) + ': ' + text + '\n')
    
def exp_time(avg):
    return random.expovariate(1.0/avg)
    
class Crossroad:
    GREEN = True
    RED = False
    phase = RED
    red_phase_time = 20
    green_phase_time = 20
    switch_time = red_phase_time
    
    def is_green():
        return Crossroad.phase
        
    def phase_time():
        if Crossroad.phase:
            return Crossroad.green_phase_time
        else:
            return Crossroad.red_phase_time
    
class Car:
    delay = 1
    length = 4
    speed = 17 #m/s
    acceleration_time = 5 #s
    
    counter = 0
    green_counter = 0
    sum_time = 0
    
    def __init__(self, time):
        self.time = time
        
    def count_green_car():
        Car.green_counter += 1
        
    def count_car(self):
        Car.sum_time += (events_list.time - self.time)
        Car.counter += 1
        
    def get_avg_queue_time():
        return Car.sum_time/Car.counter
        
    def get_avg_time_with_greens():
        return Car.sum_time/(Car.counter + Car.green_counter)
    
    def get_avg_time_with_acceleration():
        return (Car.sum_time + (2 * Car.acceleration_time * Car.counter))/(Car.counter + Car.green_counter)
        

Handler.intensity = 4

log = open('log.txt', 'w')

for i in range(1000):

    first_car = Resource('First car')
    first_car.distance_from_cross = 0
    first_car.queue = Queue()

    phase_switch_handler = Handler(switch_phase)
    new_car_handler = Handler(new_car)
    car_go_handler = Handler(car_go)

    events_list = FutureEventsList((Crossroad.switch_time, Event('Phase switch', phase_switch_handler)))
    events_list.put(exp_time(Handler.intensity), Event('New car', new_car_handler))

    while events_list.time < 1000:
        events_list.get().handler._function()

    log.write('\nМашин:' + str(Car.counter) + '\n')
    log.write('Среднее время нахождения машины в очереди равно ' + str(Car.get_avg_queue_time()) + '\n')
    log.write('С учетом проехавших свободно ' + str(Car.get_avg_time_with_greens()) + '\n')
    log.write('С учетом разгона и торможения ' + str(Car.get_avg_time_with_acceleration()) + '\n\n')
    
    Crossroad.switch_time = Crossroad.phase_time()

log.close