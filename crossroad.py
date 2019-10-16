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
        log_event('Фаза переключилась на зеленый')
    else:
        log_event('Фаза переключилась на красный')
    
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

    if (Car.queue_length/Car.speed) > (Crossroad.switch_time - list.time):
        Car.queue_length = 0
        log_event('Машина не успела выехать')
        return

    if Handler.queue > 0:
        Handler.queue -= 1
        
        if Car.delay < (Crossroad.switch_time - list.time):
            Car.queue_length += Car.length
            list.put(Car.delay, Event('Car go', car_go_handler))
        else:
            Car.queue_length = 0
            
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
    length = 3
    speed = 10 #m/s
    queue_length = 0

Handler.intensity = 4
Handler.queue = 0

first_car = Resource('First car')

log = open('log.txt', 'w')

phase_switch_handler = Handler(switch_phase)
new_car_handler = Handler(new_car)
car_go_handler = Handler(car_go)

list = FutureEventsList((Crossroad.switch_time, Event('Phase switch', phase_switch_handler)))
list.put(exp_time(Handler.intensity), Event('New car', new_car_handler))


while list.time < 100:
    list.get().handler._function()

log.close