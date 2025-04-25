import psychopy
from psychopy import visual, core, event
from psychopy.hardware import keyboard
from psychopy.visual import Window, GratingStim


# from src.pyelink_connector.psychopy.connector import EyeConnector
from src.pyelink_connector.psychopy.utils import Target
from src.pyelink_connector.utils import *


def main(settings:dict):
    win = Window(settings["resolution"], screen=settings["display"], fullscr=True, monitor=None, units="pix")
    kb = keyboard.Keyboard()
    clock = core.Clock()

    # eyeConnector = EyeConnector(win=win, prefix="TEST", eye=settings["eye"])
    # open file on host
    # eyeConnector.openFile(file_name="psp")
    
    # hide mouse
    win.setMouseVisible(False)

    # Welcome
    msg_header = visual.TextStim(win, pos=[0, +150], text="Psychopy Pylink EyeLink Connector")
    msg_body = visual.TextStim(win, pos=[0, +50], text="1. Setup by calibrating (and optionally validating)\n2. Testing communication with simple tracking task.")
    msg_footer = visual.TextStim(win, pos=[0, -50], text="Start setup [SPACE]")
    msg_header.draw()
    msg_body.draw()
    msg_footer.draw()

    win.flip()
    kb.clearEvents()
    event.waitKeys(keyList=["space"])

    # Setup/ Calibration
    # eyeConnector.runSetup(settings=settings)

    # Test/ Trial
    msg_header = visual.TextStim(win, pos=[0, +150], text="Setup complete")
    msg_footer = visual.TextStim(win, pos=[0, -50], text="Start Test Trial [SPACE]")
    msg_header.draw()
    msg_footer.draw()

    win.flip()
    kb.clearEvents()
    event.waitKeys(keyList=["space"])

    done = False
    target_left = Target(win=win, color=(0, 1, 0))
    target_right = Target(win=win, color=(0, 0, 1))
    kb.clearEvents()
    while not done:
        keys = kb.getKeys()
        for _k in keys:
            if _k == 'esc':
                core.quit()
            elif _k == 'space':
                done = True
        
        # udpate objects
        target_left.set_pos((target_left.x + 1, target_left.y + 1))

        # render
        target_left.render()

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
        "display": 0,
        "resolution": [2048, 1152],
        "render_fps": 60,
        "font_name": "Times new Roman",
        "font_size": 22,
        "font_color": BLACK,
        "bg_color": GREY,
        }
    
    main(settings=settings)