import pygame
from ..utils import *

class MultiLineText():
    def __init__(self, text:str, 
                 pos:tuple|None=(0,0), screen_size:tuple|None=None, placement:str="center",
                 settings:dict={}):
        # default values
        _defaultFontName = "Times New Roman"
        _defaultFontSize = 22
        _defaultFontColor = BLACK

        try:
            fn = settings["font_name"]
        except KeyError:
            fn = _defaultFontName
        try:
            fs = settings["font_size"]
        except KeyError:
            fs = _defaultFontSize
        try:
            fc = settings["font_color"]
        except:
            fc = _defaultFontColor

        # calculate postion
        if ((pos is None) and (screen_size is None)):
            raise AssertionError("Either pos or screen_size must be set.")
        
        self.font = pygame.font.SysFont(fn, size=fs)
        self.images = []
        self.rects = []
        for i, line in enumerate(text.split("\n")):
            lineImage = self.font.render(line.strip(), antialias=True, color=fc)
            self.images.append(lineImage)

        # If screen_size is set, overwrite pos parameter according to placement
        if screen_size is not None:
            _max_img_width = max([x.get_width() for x in self.images])

            # Horizontal position
            if placement.lower() in ["center", "centre"]:
                _pos0 = screen_size[0] / 2 - _max_img_width / 2
            elif placement.lower() == "left":
                _pos0 = 0.
            elif placement.lower() == "right":
                _pos0 = screen_size[0] - _max_img_width

            # Always center vertically
            _pos1 = screen_size[1] / 2 - ((len(self.images)/2) * self.font.get_height() * 1.1)

            pos = (_pos0, _pos1)

        for i, img in enumerate(self.images):
            imgRect = img.get_rect()
            imgRect.x = pos[0]
            imgRect.y = pos[1] + i * self.font.get_height() * 1.1
            self.rects.append(imgRect)
        
    
    def render(self, canvas:pygame.Surface):
        for image, rect in zip(self.images, self.rects):
            canvas.blit(image, rect)


class Target():
    def __init__(self, x=0, y=0, outer_color=WHITE, inner_color=BLACK) -> None:
        _outerCircleRadius = 10
        _innerCircleRadius = 5
    
        # appearance
        self.image = pygame.Surface([_outerCircleRadius*2, _outerCircleRadius*2], pygame.SRCALPHA)
        # outer circle
        pygame.draw.circle(
            surface=self.image,
            color=outer_color,
            center=(_outerCircleRadius, _outerCircleRadius),
            radius=_outerCircleRadius
        )
        # inner circle
        pygame.draw.circle(
            surface=self.image,
            color=inner_color,
            center=(_outerCircleRadius, _outerCircleRadius),
            radius=_innerCircleRadius
        )

        # position
        self.rect = self.image.get_rect()
        self.rect.x = x - self.image.get_width()
        self.rect.y = y - self.image.get_height()

        self.hidden = False

    @property
    def x(self):
        return self.rect.x
    
    @property
    def y(self):
        return self.rect.y
    
    def hide(self):
        self.hidden = True

    def show(self):
        self.hidden = False
    
    def set_x(self, x):
        self.rect.x = x

    def set_y(self, y):
        self.rect.y = y

    def render(self, canvas:pygame.Surface):
        if not self.hidden:
            canvas.blit(self.image, self.rect)

    def update(self, dt):
        pass