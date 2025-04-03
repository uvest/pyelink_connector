import pyglet
from ..utils import *

class Target():
    def __init__(self, x=0, y=0, outer_color=WHITE, inner_color=BLACK, batch=None) -> None:
        self.outer = pyglet.shapes.Circle(x, y, 10, color=outer_color, batch=batch)
        self.inner = pyglet.shapes.Circle(x, y, 5, color=inner_color, batch=batch)

        self.vx = 0
        self.vy = 0
        self.sigma = 1

        self.hidden = False

    @property
    def x(self):
        return self.outer.x
    
    @property
    def y(self):
        return self.outer.y
    
    def hide(self):
        self.hidden = True

    def show(self):
        self.hidden = False
    
    def set_x(self, x):
        self.outer.x = x
        self.inner.x = x

    def set_y(self, y):
        self.outer.y = y
        self.inner.y = y

    def draw(self):
        if not self.hidden:
            self.outer.draw()
            self.inner.draw()

    def update(self, dt):
        pass