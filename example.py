from utils.components import Model, Resource, Generator
from queue import LifoQueue

if __name__ == '__main__':
    q = LifoQueue()
    r = Resource('Crossroad', queue=q, release_law=lambda: 3)
    g = Generator('Simple Generator', 'Car', dst=r, release_law=lambda: 1)
    m = Model(generators=(g, ), resources=(r, ), maxtime=4)
    m.run()
