from utils.components import Resource, Handler, FutureEventsList, Event
import random

def switch_phase():

    global phase, switch_time

    phase = not phase
    switch_time = time + 20
    list.put(switch_time, Event('Phase switch', phase_switch_handler))
    if phase == GREEN:
        list.put(time, Event('Car go', car_go_handler))
        log_event('Фаза переключилась на зеленый')
    else:
        log_event('Фаза переключилась на красный')
    
def new_car():

    global queue

    list.put(time + random.expovariate(1.0/intensity), Event('New car', new_car_handler))
    if first_car.busy:
        queue += 1
        log_event('Машина встала в очередь')
    else:
        if phase == RED:
            if first_car.busy:
                queue += 1
                log_event('Машина встала в очередь на красный')
            else:
                first_car.act(Handler.TAKE)
                log_event('Машина встала на красный')
        else:
            log_event('Машина проехала свободно')

def car_go():

    global length, queue

    if (length/car_speed) > (switch_time - time):
        length = 0
        log_event('Машина не успела выехать')
        return

    if queue > 0:
        queue -= 1
        if car_delay < (switch_time - time):
            length += car_length
            list.put(time + car_delay, Event('Car go', car_go_handler))
        else:
            length = 0
        log_event('Машина выехала. Сзади еще')
    else:
        first_car.act(Handler.FREE)
        log_event('Машина выехала. Сзади свободно')
  
def log_event(text):
    log.write(str(int(time)) + ': ' + text + '\n')

GREEN = True
RED = False
phase = RED

time = 0
switch_time = 20
length = 0

intensity = 4
car_delay = 2
car_length = 3
car_speed = 10 #m/s

first_car = Resource('First car')
queue = 0

log = open('log.txt', 'w')

phase_switch_handler = Handler(switch_phase)
new_car_handler = Handler(new_car)
car_go_handler = Handler(car_go)

list = FutureEventsList((switch_time, Event('Phase switch', phase_switch_handler)))
list.put(random.expovariate(1.0/intensity), Event('New car', new_car_handler))


while time < 100:
    event = list.get()
    time = event[0]
    event[1].handler._function()

log.close