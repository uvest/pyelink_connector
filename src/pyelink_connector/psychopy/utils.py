import psychopy
from psychopy.visual import GratingStim, Circle
from ..utils import *

# Need to overwrite colors for psychopy
BLACK = (-1, -1, -1)
WHITE = (1, 1, 1)
GREY = (0, 0, 0)

class Target():
    def __init__(self, win, color=None):
        # self.inner = GratingStim(win, color=-1, colorSpace="rgb", tex=None, mask="circle", size=10)
        # self.outer = GratingStim(win, color=1, colorSpace="rgb", tex=None, mask="circle", size=20)
        self.inner = Circle(win, radius=5, fillColor=BLACK, fillColorSpace="rgb")

        if color is None:
            color = WHITE
        self.outer = Circle(win, radius=10, fillColor=color, fillColorSpace="rgb")

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
    

# class MultiLineText():
#     def __init__(self, text:str, 
#                  pos:tuple|None=(0,0), screen_size:tuple|None=None, placement:str="center",
#                  settings:dict={}):
#         # default values
#         _defaultFontName = "Times New Roman"
#         _defaultFontSize = 22
#         _defaultFontColor = BLACK

#         try:
#             fn = settings["font_name"]
#         except KeyError:
#             fn = _defaultFontName
#         try:
#             fs = settings["font_size"]
#         except KeyError:
#             fs = _defaultFontSize
#         try:
#             fc = settings["font_color"]
#         except:
#             fc = _defaultFontColor

#         # calculate postion
#         if ((pos is None) and (screen_size is None)):
#             raise AssertionError("Either pos or screen_size must be set.")
        
#         self.font = pygame.font.SysFont(fn, size=fs)
#         self.images = []
#         self.rects = []
#         for i, line in enumerate(text.split("\n")):
#             lineImage = self.font.render(line.strip(), antialias=True, color=fc)
#             self.images.append(lineImage)

#         # If screen_size is set, overwrite pos parameter according to placement
#         if screen_size is not None:
#             _max_img_width = max([x.get_width() for x in self.images])

#             # Horizontal position
#             if placement.lower() in ["center", "centre"]:
#                 _pos0 = screen_size[0] / 2 - _max_img_width / 2
#             elif placement.lower() == "left":
#                 _pos0 = 0.
#             elif placement.lower() == "right":
#                 _pos0 = screen_size[0] - _max_img_width

#             # Always center vertically
#             _pos1 = screen_size[1] / 2 - ((len(self.images)/2) * self.font.get_height() * 1.1)

#             pos = (_pos0, _pos1)

#         for i, img in enumerate(self.images):
#             imgRect = img.get_rect()
#             imgRect.x = pos[0]
#             imgRect.y = pos[1] + i * self.font.get_height() * 1.1
#             self.rects.append(imgRect)
        
    
#     def render(self, canvas:pygame.Surface):
#         for image, rect in zip(self.images, self.rects):
#             canvas.blit(image, rect)