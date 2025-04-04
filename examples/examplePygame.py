import pygame as pygame
import abc
import numpy as np

from pyelink_connector.pygame.connector import EyeConnector
from pyelink_connector.pygame.utils import Target
from pyelink_connector.utils import *


# STAGES
class Stage():
    def __init__(self):
        _dispInfo = pygame.display.Info()
        self._displayWidth = _dispInfo.current_w
        self._displayHeight = _dispInfo.current_h
        self._displayCenter = (self._displayWidth/2, self._displayHeight/2)
        self.bgColor = GREY

    def update(self, dt:float|None=None):
        return
    def run(self):
        return
    def render(self, canvas:pygame.Surface):
        canvas.fill(self.bgColor)

class TextStage(Stage):
    def __init__(self, canvas:pygame.Surface, clock:pygame.time.Clock, settings:dict,
                 header:str|None=None, body:str|None=None, footer:str|None=None,
                 header_pos:float=0.2, body_pos:float=0.3, footer_pos:float=0.5,
                 antialias:bool=True):
        """_summary_

        Args:
            canvas (pygame.Surface): _description_
            clock (pygame.time.Clock): _description_
            settings (dict): Required keys: font_name, render_fps
            header (str | None, optional): _description_. Defaults to None.
            body (str | None, optional): _description_. Defaults to None.
            footer (str | None, optional): _description_. Defaults to None.
            header_pos (float, optional): _description_. Defaults to 0.2.
            body_pos (float, optional): _description_. Defaults to 0.3.
            footer_pos (float, optional): _description_. Defaults to 0.5.
            antialias (bool, optional): _description_. Defaults to True.
        """
        assert(not (header is None) or not (body is None) or not (footer is None))
        super().__init__()

        self.canvas = canvas
        self.clock = clock
        self.renderFPS = settings["render_fps"]

        self.font = pygame.font.SysFont(settings["font_name"], size=settings["font_size"])

        self.header_image = None
        self.body_images = []
        self.footer_images = []

        if header is not None:
            header_font = pygame.font.SysFont(settings["font_name"], size=settings["font_size"]+5)
            self.header_image = header_font.render(header, antialias, BLACK)
            self.header_rect = self.header_image.get_rect()
            self.header_rect.x = self._displayCenter[0] - self.header_image.get_width() / 2
            self.header_rect.y = self._displayHeight * header_pos
        if body is not None:
            for i, b in enumerate(body.split("\n")):
                bi = self.font.render(b.strip(), antialias, BLACK)
                bi_rect = bi.get_rect()
                bi_rect.x = self._displayCenter[0] - bi.get_width() / 2
                bi_rect.y = self._displayHeight * body_pos + i * self.font.get_height() * 1.1
                self.body_images.append((bi, bi_rect))
        if footer is not None:
            for i, f in enumerate(footer.split("\n")):
                fi = self.font.render(f.strip(), antialias, BLACK)
                fi_rect = fi.get_rect()
                fi_rect.x = self._displayCenter[0] - fi.get_width() / 2
                fi_rect.y = self._displayHeight * footer_pos + i * self.font.get_height() * 1.1
                self.body_images.append((fi, fi_rect))

    def render(self, canvas:pygame.Surface):
        # draw background
        super().render(canvas)
        # draw text
        if self.header_image is not None:
            canvas.blit(self.header_image, self.header_rect)
        for bi, bi_rect in self.body_images:
            canvas.blit(bi, bi_rect)
        for fi, fi_rect in self.footer_images:
            canvas.blit(fi, fi_rect)

    def run(self, min_duration:float=0):
        """Run the text screen until a continue button is pressed.
        Args:
            min_duration (float | None, optional): If provided, do not react to button presses for this amount of seconds. Defaults to None.
        """
        done = False
        _startTime = pygame.time.get_ticks()
        _checkEvents = False

        while not done:
            if (not _checkEvents) and (pygame.time.get_ticks() > _startTime + min_duration * 1000):
                _checkEvents = True
                pygame.event.clear()
            if _checkEvents:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            done = True

            # draw objects on canvas
            self.render(self.canvas)
            pygame.display.get_surface().blit(self.canvas, self.canvas.get_rect())
            pygame.event.pump()
            pygame.display.update()
            self.clock.tick(self.renderFPS)

class TrialStage(Stage):
    def __init__(self, canvas:pygame.Surface, clock:pygame.time.Clock, settings:dict,
                  eyeConnector:EyeConnector) -> None:
        super().__init__()
        self.canvas = canvas
        self.clock = clock
        self.eyeConnector = eyeConnector
        self.renderFPS = settings["render_fps"]

        self.terminated = False

        self.v = 400
        self.v_angle = np.deg2rad(20)

        self.target = Target(x=self._displayCenter[0], y=self._displayCenter[1], outer_color=(200, 40, 40))
        if (settings["eye"] == "left") or (settings["eye"] == "both"):
            self.cursor_left = Target(x=self._displayCenter[0], y=self._displayCenter[1], outer_color=(40, 200, 40))
        if (settings["eye"] == "right") or (settings["eye"] == "both"):
            self.cursor_right = Target(x=self._displayCenter[0], y=self._displayCenter[1], outer_color=(40, 40, 200))

    def render(self, canvas):
        # draw background
        super().render(canvas)
        # draw objects
        self.target.render(canvas)
        if (settings["eye"] == "left") or (settings["eye"] == "both"):
            self.cursor_left.render(canvas)
        if (settings["eye"] == "right") or (settings["eye"] == "both"):
            self.cursor_right.render(canvas)

    def update(self, dt):
        # random move on target
        # self.v_angle += np.random.normal(0, 0.2)

        # linear move on target
        if (self.target.y >= self._displayHeight * 0.8) or (self.target.y <= self._displayHeight * 0.2) or \
            (self.target.x >= self._displayWidth * 0.8) or (self.target.x <= self._displayWidth * 0.2):
            self.v_angle = (np.pi + self.v_angle) % (2*np.pi)
            # print(np.rad2deg(self.v_angle))
        
        vx = np.cos(self.v_angle) * self.v
        vy = np.sin(self.v_angle) * self.v
        self.target.set_x(self.target.x + vx * dt)
        self.target.set_y(self.target.y + vy * dt)

        # move cursor according to eye-gaze
        samples = self.eyeConnector.getEyeSample()
        
        if (settings["eye"] == "both"):
            left_sample, right_sample = self.eyeConnector.getEyeSample()
        elif (settings["eye"] == "left"):
            left_sample = samples
        elif (settings["eye"] == "right"):
            right_sample = samples

        if (settings["eye"] == "left") or (settings["eye"] == "both"):
            self.cursor_left.set_x(left_sample.gaze[0])
            self.cursor_left.set_y(left_sample.gaze[1])
        if (settings["eye"] == "right") or (settings["eye"] == "both"):
            self.cursor_right.set_x(right_sample.gaze[0])
            self.cursor_right.set_y(right_sample.gaze[1])

    def run(self):
        # start recording
        self.eyeConnector.startRecording(msg="test trial start")

        # start running
        dt = 1 / self.renderFPS
        t = pygame.time.get_ticks()
        done = False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN:
                    if (event.key == pygame.K_RETURN) or (event.key == pygame.K_ESCAPE):
                        done = True

            # update
            self.update(dt)

            # draw objects on canvas
            self.render(self.canvas)
            pygame.display.get_surface().blit(self.canvas, self.canvas.get_rect())
            pygame.event.pump()
            pygame.display.update()
            self.clock.tick(self.renderFPS)

            # update dt
            _tNew = pygame.time.get_ticks()
            dt = (_tNew - t) / 1000
            t = _tNew

        # stop recording
        self.eyeConnector.stopRecording()

        # download edf file
        self.eyeConnector.downloadFile()



def main(settings:dict):
    pygame.init()
    surface = pygame.display.set_mode(depth=0, display=settings["display"], vsync=1, flags=pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()
    eyeConnector = EyeConnector(win=surface, prefix="TEST", eye=settings["eye"])

    # open file on host
    eyeConnector.openFile(file_name="pga")

    # Welcome
    startScreen = TextStage(surface, clock, settings=settings,
                            header="Pygame Pylink EyeLink Connector",
                            body="1. Setup by calibrating (and optionally validating)\n\
                                2. Testing communication with simple tracking task.",
                            footer="Start setup [SPACE]", )
    startScreen.run()

    # Setup/ Calibration
    eyeConnector.runSetup(settings=settings)

    # Test/ Trial
    trial = TrialStage(surface, clock, settings, eyeConnector)
    trial.run()

    # End
    endScreen = TextStage(surface, clock, settings=settings,
                            header="Test End",
                            body="The edf file should have been downloaded.",
                            footer="End Script [SPACE]")
    endScreen.run()

    eyeConnector.close()

    pygame.quit()


if __name__ == "__main__":
    settings = {
        "eye": "both",
        "display": 0,
        "render_fps": 60,
        "font_name": "Times new Roman",
        "font_size": 22,
        "font_color": BLACK,
        "bg_color": GREY,
        }
    
    main(settings=settings)