from utils.components import Resource, Handler, FutureEventsList, Event
from collections import namedtuple
from queue import Queue
import random

def switch_phase():

    Crossroad.phase = not Crossroad.phase
    Crossroad.switch_time = list.time + Crossroad.phase_time
    list.put(Crossroad.phase_time, Event('Phase switch', phase_switch_handler))
    
    if Crossroad.phase == Crossroad.GREEN:
        list.put(0, Event('Car go', car_go_handler))
        log_event('Фаза переключилась на зеленый\n')
    else:
        log_event('Фаза переключилась на красный\n')
    
def new_car():

    list.put(exp_time(Handler.intensity), Event('New car', new_car_handler))
    
    if first_car.busy:
        Handler.queue += 1
        log_event('Машина встала в очередь')
    else:
        if Crossroad.phase == Crossroad.RED:
            if first_car.busy:
                Handler.queue += 1
                log_event('Машина встала в очередь на красный')
            else:
                first_car.act(Handler.TAKE)
                log_event('Машина встала на красный')
        else:
            log_event('Машина проехала свободно')

def car_go():

    t = Crossroad.switch_time - list.time
    
    if t < Car.acceleration_time:
        acceleration_distance = ((Car.speed/Car.acceleration_time) * (t ** 2))/ 2
    else:
        acceleration_distance = ((Car.speed * Car.acceleration_time)/ 2) + (Car.speed * (t - Car.acceleration_time))
        
    if acceleration_distance < Car.distance_from_cross:
        Car.distance_from_cross = 0
        log_event('Машина не успела выехать')
        return

    if Handler.queue > 0:
        Handler.queue -= 1
        
        if Car.delay < (Crossroad.switch_time - list.time):
            Car.distance_from_cross += Car.length
            list.put(Car.delay, Event('Car go', car_go_handler))
        else:
            Car.distance_from_cross = 0
            
        log_event('Машина выехала. Сзади еще')
    else:
        first_car.act(Handler.FREE)
        log_event('Машина выехала. Сзади свободно')
  
def log_event(text):
    log.write(str(int(list.time)) + ': ' + text + '\n')
    
def exp_time(avg):
    return random.expovariate(1.0/avg)
    
class Crossroad:
    GREEN = True
    RED = False
    phase = RED
    phase_time = 20
    switch_time = phase_time
    
class Car:
    delay = 2
    length = 4
    speed = 17 #m/s
    acceleration_time = 5 #s
    distance_from_cross = 0
    
    def __init__(self, time):
        self.time = time

Handler.intensity = 4
Handler.queue = 0

first_car = Resource('First car')

log = open('log.txt', 'w')

phase_switch_handler = Handler(switch_phase)
new_car_handler = Handler(new_car)
car_go_handler = Handler(car_go)

list = FutureEventsList((Crossroad.switch_time, Event('Phase switch', phase_switch_handler)))
list.put(exp_time(Handler.intensity), Event('New car', new_car_handler))


while list.time < 1000:
    list.get().handler._function()

log.close