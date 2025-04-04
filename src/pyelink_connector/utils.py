import pylink
from typing import NamedTuple

# COLORS
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (128, 128, 128)

# Keys
SPACE_KEY = ord(' ')
TAB_KEY = ord('\t')
ENTER_KEY = pylink.ENTER_KEY
ESC_KEY = pylink.ESC_KEY
DELETE_KEY = int('5300', 16) # DELETE_KEY = 0x5300 according to Eyelink Programmers guide
BACKSPACE_KEY = ord('\b')
C_KEY = ord('c')
V_KEY = ord('v')
D_KEY = ord('d')
B_KEY = ord('b')
L_KEY = ord('l')
R_KEY = ord('r')

# STATUS CODES
STATUS_MSGS = {
    1000: "",
    0: "succss",
    27: "aborted",
    1: "failed (poor result)",
    -1: "failed",
    2: "2 - unknown"
}

# CLASSES
class Sample(NamedTuple):
    gaze: tuple
    href: tuple
    pupil_raw: tuple
    pupil: float