import psychopy
from psychopy.visual import Circle, TextStim, Window
from ..utils import *

# Need to overwrite colors for psychopy
BLACK = (-1, -1, -1)
WHITE = (1, 1, 1)
GREY = (0, 0, 0)

class Target():
    def __init__(self, win:Window, x=0, y=0, outer_color=WHITE, inner_color=BLACK):
        self.inner = Circle(win, pos=[x, y], radius=5, fillColor=inner_color, fillColorSpace="rgb")
        self.outer = Circle(win, pos=[x, y], radius=10, fillColor=outer_color, fillColorSpace="rgb")

        self.hidden = False

    @property
    def x(self):
        return self.inner.pos[0]
    
    @property
    def y(self):
        return self.inner.pos[1]
    
    def hide(self):
        self.hidden = True

    def show(self):
        self.hidden = False
    
    def set_x(self, x):
        self.inner.pos = (x, self.inner.pos[1])
        self.outer.pos = (x, self.outer.pos[1])

    def set_y(self, y):
        self.inner.pos = (self.inner.pos[0], y)
        self.outer.pos = (self.outer.pos[0], y)

    def set_pos(self, pos:tuple):
        self.inner.pos = pos
        self.outer.pos = pos

    def get_pos(self):
        return self.inner.pos

    def render(self):
        if not self.hidden:
            self.outer.draw()
            self.inner.draw()

    def update(self, dt):
        pass
    
class MultiLineText(TextStim):
    def __init__(self, win, text="Hello World", pos=(0.0, 0.0),
                 font="", depth=0, rgb=None, color=(1.0, 1.0, 1.0), colorSpace='rgb', opacity=1.0,
                 contrast=1.0, units="", ori=0.0, height=None, antialias=True, bold=False, italic=False, alignHoriz=None,
                 alignVert=None, alignText='center', anchorHoriz='center', anchorVert='center', fontFiles=(), wrapWidth=None,
                 flipHoriz=False, flipVert=False, languageStyle='LTR', draggable=False, name=None, autoLog=None, autoDraw=False):
        # strip unnecessary whitespace around newlines
        lines =[l.strip() for l in text.split("\n")]
        text = "\n".join(lines)

        super().__init__(win, text, font, pos, depth, rgb, color, colorSpace, opacity, contrast, units,
                         ori, height, antialias, bold, italic, alignHoriz, alignVert, alignText, anchorHoriz, anchorVert, 
                         fontFiles, wrapWidth, flipHoriz, flipVert, languageStyle, draggable, name, autoLog, autoDraw)
        
    def render(self):
        self.draw()
