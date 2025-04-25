from psychopy import visual, core, event
from psychopy.hardware import keyboard
from psychopy.visual import Window


from src.pyelink_connector.psychopy.connector import EyeConnector
from src.pyelink_connector.psychopy.utils import Target, MultiLineText
from src.pyelink_connector.utils import *


def main(settings:dict):
    win = Window(settings["resolution"], screen=settings["display"], fullscr=True, monitor=None, units="pix")
    kb = keyboard.Keyboard()

    eyeConnector = EyeConnector(win=win, prefix="TEST", eye=settings["eye"])
    # open file on host
    eyeConnector.openFile(file_name="psp")

    width, height = win.size
    
    # hide mouse
    win.setMouseVisible(False)

    # Welcome
    msg_header = visual.TextStim(win, pos=[0, +150], text="Psychopy Pylink EyeLink Connector")
    msg_body = MultiLineText(win, pos=[0, 50], text="1. Setup by calibrating (and optionally validating)\n\
                                                     2. Testing communication with simple tracking task.")
    msg_footer = visual.TextStim(win, pos=[0, -50], text="Start setup [SPACE]")
    msg_header.draw()
    msg_body.draw()
    msg_footer.draw()

    win.flip()
    kb.clearEvents()
    event.waitKeys(keyList=["space"])

    # Setup/ Calibration
    eyeConnector.runSetup(settings=settings)

    # Test/ Trial
    msg_header = visual.TextStim(win, pos=[0, +150], text="Setup complete")
    msg_footer = visual.TextStim(win, pos=[0, -50], text="Start Test Trial [SPACE]")
    msg_header.draw()
    msg_footer.draw()

    win.flip()
    kb.clearEvents()
    event.waitKeys(keyList=["space"])

    done = False
    cursor_eye_left = Target(win=win, outer_color=(0, 1, 0))
    cursor_eye_right = Target(win=win, outer_color=(0, 0, 1))
    target = Target(win=win, outer_color=(1, 0, 0))
    kb.clearEvents()

    # variable for target movement
    speed = 2
    x_dir = 1 # x direction: start towards the right
    y_dir = 1 # y direction: start towards the top
    
    while not done:
        keys = kb.getKeys()
        for _k in keys:
            if _k == 'esc':
                core.quit()
            elif _k == 'space':
                done = True
        
        # udpate objects
        if target.x > 0.5 * 0.8 * width:
            x_dir = -1
        if target.x < -0.5 * 0.8 * width:
            x_dir = 1
        if target.y > 0.5 * 0.8 * height:
            y_dir = -1
        if target.y < -0.5 * 0.8 * height:
            y_dir = 1
        target.set_pos((target.x + x_dir * speed, target.y + y_dir * speed))

        # move cursor according to eye-gaze
        samples = eyeConnector.getEyeSample()
        if (settings["eye"] == "both"):
            left_sample, right_sample = eyeConnector.getEyeSample()
        elif (settings["eye"] == "left"):
            left_sample = samples
        elif (settings["eye"] == "right"):
            right_sample = samples

        if (settings["eye"] == "left") or (settings["eye"] == "both"):
            cursor_eye_left.set_pos(left_sample.gaze)
        if (settings["eye"] == "right") or (settings["eye"] == "both"):
            cursor_eye_right.set_pos(right_sample.gaze)

        # render
        target.render()
        cursor_eye_left.render()
        cursor_eye_right.render()

        # update screen
        win.flip()
    
    msg_header = visual.TextStim(win, pos=[0, +150], text="Test Done")
    msg_footer = visual.TextStim(win, pos=[0, -50], text="End [SPACE]")
    msg_header.draw()
    msg_footer.draw()

    win.flip()
    event.waitKeys(keyList=["space"])

    print("by")

if __name__ == "__main__":
    settings = {
        "eye": "both",
        "resolution": [2048, 1152],
        "display": 0,
        }
    
    main(settings=settings)