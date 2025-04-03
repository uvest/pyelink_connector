import pyglet
import screeninfo

from pyelink_connector.pyglet.connector import EyeConnector
from pyelink_connector.pyglet.utils import Target

# to create a dummy trial
import random
import numpy as np

### STAGES

class TextStage():
    def __init__(self, win, batch, msg:str, name="") -> None:
        self.win = win
        self.batch = batch
        self.msg = msg
        self.name = name

        self.terminated = False
        
    def start(self):
        self.text = pyglet.text.Label(text=self.msg, 
                                      font_size=26,
                                      x=self.win.width//2, y=self.win.height//2,
                                      anchor_x="center", anchor_y="bottom", 
                                      width=self.win.width//2, batch=batch, multiline=True)
        self.win.push_handlers(on_key_press=self._on_key_press)

    def _on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.SPACE:
            self.win.pop_handlers()
            self.terminated = True

class CalibrationStage():
    def __init__(self, win, batch, eyeConnector, name="") -> None:
        self.win = win
        self.batch = batch
        self.eyeConnector = eyeConnector
        self.name = name

        self.terminated = False

    def start(self):
        self.eyeConnector.calibrate(callback = self.stop)

    def stop(self, status):
        self.terminated = True

class SetupStage():
    def __init__(self, win, batch, eyeConnector, name="") -> None:
        self.win = win
        self.batch = batch
        self.eyeConnector = eyeConnector
        self.name = name

        self.terminated = False

    def start(self):
        self.eyeConnector.startSetup(callback = self.stop)

    def stop(self, status):
        self.terminated = True

class TrialStage():
    def __init__(self, win, batch, eyeConnector, name="") -> None:
        self.win = win
        self.batch = batch
        self.eyeConnector = eyeConnector
        self.name = name

        self.terminated = False

        self.v = 400
        self.v_angle = np.deg2rad(20)

    def start(self):
        self.target = Target(x=self.win.width//2, y=self.win.height//2, outer_color=(200, 40, 40), batch=self.batch)
        self.cursor_left = Target(x=self.win.width//2, y=self.win.height//2, outer_color=(40, 200, 40), batch=self.batch)
        self.cursor_right = Target(x=self.win.width//2, y=self.win.height//2, outer_color=(40, 40, 200), batch=self.batch)

        # start recording
        self.eyeConnector.startRecording(msg="test trial start")

        # start running
        pyglet.clock.schedule(self.run)
        self.win.push_handlers(on_key_press=self._on_key_press)

    def _on_key_press(self, symbol, modifiers):
        if (symbol == pyglet.window.key.ENTER) or (symbol == pyglet.window.key.ESCAPE):
            self.win.pop_handlers()
            self.end()


    def run(self, dt):
        # random move on target
        # self.v_angle += np.random.normal(0, 0.2)

        # linear move on target
        if (self.target.y >= self.win.height * 0.8) or (self.target.y <= self.win.height * 0.2) or \
            (self.target.x >= self.win.width * 0.8) or (self.target.x <= self.win.width * 0.2):
            self.v_angle = (np.pi + self.v_angle) % (2*np.pi)
            # print(np.rad2deg(self.v_angle))
        
        vx = np.cos(self.v_angle) * self.v
        vy = np.sin(self.v_angle) * self.v
        self.target.set_x(self.target.x + vx * dt)
        self.target.set_y(self.target.y + vy * dt)

        # move cursor according to eye-gaze
        left_sample, right_sample = self.eyeConnector.getEyeSample()
        self.cursor_left.set_x(left_sample.gaze[0])
        self.cursor_left.set_y(left_sample.gaze[1])
        self.cursor_right.set_x(right_sample.gaze[0])
        self.cursor_right.set_y(right_sample.gaze[1])


    def end(self):
        pyglet.clock.unschedule(self.run)
        del(self.target)
        del(self.cursor_left)
        del(self.cursor_right)

        # stop recording
        self.eyeConnector.stopRecording()

        # download edf file
        self.eyeConnector.downloadFile()

        self.terminated = True


class Handler():
    def __init__(self, win, batch, eyeConnector) -> None:
        self.win = win
        self.batch = batch
        self.eyeConnector = eyeConnector

        self.stage = TextStage(self.win, self.batch, "Welcome.\n\
                               This script will first setup the EyeLink 1000 + (calibration, validation, drift correction).\n\
                               Then you'll be presented a moving target in red. Your tracked eye-positions will be displayed in green (left eye) and blue (right eye).\
                               \n\nPress SPACE to start the setup, then follow the instructions provided there.", name="start")

    def start(self):
        # open file on eyelink host
        self.eyeConnector.openFile(file_name="pgl")

        pyglet.clock.schedule(self.run)
        self.stage.start()

    def run(self, dt):
        if self.stage.terminated:
            self.switch()

    def switch(self):
        if self.stage.name == "start":
            # self.stage = CalibrationStage(self.win, self.batch, self.eyeConnector, name="calibration")
            self.stage = SetupStage(self.win, self.batch, self.eyeConnector, name="calibration")
            self.stage.start()
        elif self.stage.name == "calibration":
            self.stage = TrialStage(self.win, self.batch, self.eyeConnector, name="trial")
            self.stage.start()
        elif self.stage.name == "trial":
            self.stage = TextStage(self.win, self.batch, "Done.\n\
                               The edf file should have been downloaded.\n\
                               Press SPACE to quit.", name="end")
            self.stage.start()
        elif self.stage.name == "end":
            self.eyeConnector.close()
            pyglet.app.exit()


### ENTRY POINT
if __name__ == "__main__":
    settings = {
        "render_fps": 60,
        "resolution": None, # (width, height)
        "resolution_scaling": 1.5, # scaling as found in the display settings (windows)
    }

    # use default resolutions if not provided
    if settings["resolution"] is None:
        _monitor = screeninfo.get_monitors()[0]
        settings["resolution"] = _monitor.width, _monitor.height
    # scale resolution according to manual settings
    if settings["resolution_scaling"] is not None:
        settings["resolution"] = int(settings["resolution"][0] / settings["resolution_scaling"]), \
            int(settings["resolution"][1] / settings["resolution_scaling"])
    

    win = pyglet.window.Window(settings["resolution"][0], settings["resolution"][1], fullscreen=True, caption="Testing pylink_connector")
    win.set_mouse_visible(False)

    batch = pyglet.graphics.Batch()
    bg = pyglet.shapes.Rectangle(0, 0, win.width, win.height, color=(122, 122, 122))

    # global draw method
    def on_draw():
        win.clear()
        bg.draw()
        batch.draw()
    win.push_handlers(on_draw=on_draw)

    # EyeLink Connector
    eyeConnector = EyeConnector(win, prefix="TEST")


    handler = Handler(win, batch, eyeConnector)
    handler.start()

    pyglet.app.run(1/settings["render_fps"])
