import pylink
import pyglet
from pyglet.window import Window
import screeninfo
import datetime
import os

from typing import Tuple

from .utils import Target
from ..utils import *


class EyeConnector():
    def __init__(self, win:Window, host:str="100.1.1.1", eye:str="both", prefix:str="", download_directory:str="./eye_tracking/",
                 sample_rate:int=1000) -> None:
        """Create connector object to communicate with an EyeLink 1000+.
        Args:
            win (pyglet.window.Window): window to draw to during setup.
            host (str, optional): IP of the EyeLink Host PC. Defaults to "100.1.1.1".
            eye (str, optional): Choose which eye to track. Options: ["both", "right", "left"]. Defaults to "both".
            prefix (str, optional): Session prefix. Will be added to all files handled by this connection. 
                                    Could, e.g., combine experiment and participant ID. Defaults to "".
            download_directory (str, optional): Local directory to store downloaded EDF files to. Defaults to "./eye_tracking/".
            sample_rate (int, optional): Sampling rate. Should not exceed 1000 for tracking both eyes. Defaults to 1000.
        """
        self.host = host
        self.eyelink = self.connect(host)
        self.win = win

        assert(eye.lower() in ["both", "right", "left"])
        self.eye = eye.lower()
        # set eye on host
        self.eyelink.startSetup()
        if self.eye == "both":
            _eyeKey = B_KEY
        elif self.eye == "right":
            _eyeKey = R_KEY
        elif self.eye == "left":
            _eyeKey = L_KEY
        self.eyelink.sendKeybutton(_eyeKey, 0, pylink.KB_PRESS)
        self.eyelink.sendKeybutton(_eyeKey, 0, pylink.KB_RELEASE)

        # Flags and behavioural atributes
        self.c_status = 1000 # calibration status. success = 0
        self.v_status = 1000 # validation status: success = 0
        self.d_status = 1000 # drift correction status: success = 0
        self.callback = None

        # for the more fanciful interface
        self.v_error = None
        self._v_msg = ""
        self._drift_correct_direct_return = True

        # housekeeping
        self.prefix = prefix
        self.download_directory = download_directory
        self.edf_file_name = ""
        self.sample_rate = sample_rate

        os.makedirs(self.download_directory, exist_ok=True)

        # assume the whole monitor is used. Get resolution from system.
        _monitor = screeninfo.get_monitors()[0]
        self._w = _monitor.width
        self._h = _monitor.height

        # objects
        self.bg = pyglet.shapes.Rectangle(0, 0, self._w, self._h, color=(122, 122, 122))
        self.target = Target(x=self._w//2, y=self._h//2)
        self.text = pyglet.text.Label(text="", font_name='Times New Roman', font_size=22,
                             x=self._w//2, y=self._h//2, anchor_x='center', anchor_y='bottom',
                             width=self.win.width//2, multiline=True)
        
        # for handling the eye gaze
        self.dummy_sample = Sample((self.win.width, self.win.height), (self.win.width, self.win.height), (self.win.width, self.win.height), 0.)


    ### PROPERTIES
    @property
    def calibrated(self):
        """True, if the EyeLink has been calibrated in this session"""
        return self.c_status == 0
    
    @property
    def validated(self):
        """True, if a calibration has been validated in this session"""
        return self.v_status == 0


    ### CONNECTION
    def connect(self, host:str):
        """opens a connection to the EyeLink 100+ Host PC. Make sure to close an open connection."""
        return pylink.EyeLink(host)

    def close(self):
        """Closes connection to EyeLink. Closes the edf datafile if still open.
        Returns:
            int: 0 on success. Oterhwise link error returned by device.
        """
        if self.eyelink.isConnected():
            self.closeFile()
            self.eyelink.setOfflineMode()
            return self.eyelink.close()
        else:
            return 0
    

    ### FILE HANDLING
    def openFile(self, file_name:str) -> None:
        """Opens an edf file on the EyeLink. 
        Args:
            file_name (str): The edf file name is self.prefix + "_" + file_name, if self.prefix is specified. Otherwise it is just file_name.
        """
        _pf = self.prefix + "_" if self.prefix != "" else ""
        self.edf_file_name = _pf + file_name
        if not self.edf_file_name.endswith(".edf"):
            self.edf_file_name += ".edf"
        if len(self.edf_file_name.split(".")[0]) > 8:
            print("ERROR (EyeLinkConnector): edf file name is too long. Must be shorter or equal 8 characters.")
            return False

        self.eyelink.openDataFile(self.edf_file_name)

        # set header information
        self.eyelink.sendCommand(f"add_file_preamble_text 'RECORDED BY Pylink-Pyglet Connector tagged {self.prefix}'")

        # define coordinate system. Inverted for pyglet!
        self.eyelink.sendMessage(f"DISPLAY_COORDS 0 {self._h - 1} {self._w - 1} 0")
        self.eyelink.sendCommand(f"screen_pixel_coords = 0 {self._h - 1} {self._w - 1} 0")

        # track all eye events in the file ...
        # track all eye events in the file
        _eye_identifier = ''
        if self.eye == "both":
            _eye_identifier += 'LEFT,RIGHT,'
        elif self.eye == "right":
            _eye_identifier += 'RIGHT,'
        elif self.eye == "left":
            _eye_identifier += 'LEFT,'
        else:
            raise AssertionError("eye must be one of 'both', 'right' or 'left'.")

        file_event_flags = _eye_identifier + 'FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT'
        file_sample_flags = _eye_identifier + 'GAZE,HREF,RAW,AREA,HTARGET,GAZERES,BUTTON,STATUS,INPUT'
        self.eyelink.setFileEventFilter(file_event_flags) # command file_event_filter
        self.eyelink.setFileSampleFilter(file_sample_flags) # command file_sample_data

        # ... and make them available via link
        link_event_flags = _eye_identifier + 'FIXATION,SACCADE,BLINK,BUTTON,FIXUPDATE,INPUT'
        link_sample_flags = _eye_identifier + 'GAZE,GAZERES,AREA,HTARGET,STATUS,INPUT'
        self.eyelink.sendCommand(f"link_event_filter = {link_event_flags}")
        self.eyelink.sendCommand(f"link_sample_data = {link_sample_flags}")
        
        self.eyelink.sendCommand(f"sample_rate {self.sample_rate}")

    def closeFile(self) -> None:
        """Sets the tracker to offline mode and closes the currently opened edf file"""
        self.eyelink.setOfflineMode()
        self.eyelink.closeDataFile()

    def downloadFile(self) -> None:
        """Closes open file and downloads it to self.download_directory."""
        self.closeFile()
        self.eyelink.receiveDataFile(self.edf_file_name, self.download_directory + self.edf_file_name)


    ### GENERAL SETUP ENTRY
    def startSetup(self, callback) -> None:
        """Possible entry point. Shows the status screen from which other functions can be called.
        Args:
            callback (function): Callable that is called when setup is completed.
        """
        self.callback = callback

        # enter setup mode
        self.eyelink.startSetup()

        self._showStatusScreen()


    ### CALIBRATION
    def calibrate(self, callback):
        """Possible entry point. Immediately starts the calibration. Shows the stastus screen afterwards.
        Args:
            callback (function): Callable that is called when setup is completed.
        """
        # store callback and behaviour
        self.callback = callback

        # enter setup mode
        self.eyelink.startSetup()

        # configure calibration
        self.eyelink.setCalibrationType("HV9")
        self.eyelink.sendCommand("calibration_area_proportion = 0.5 0.5")
        self.eyelink.sendCommand("validation_area_proportion = 0.5 0.5")

        # start calibration on host
        self.eyelink.sendKeybutton(C_KEY, 0, pylink.KB_PRESS)
        self.eyelink.sendKeybutton(C_KEY, 0, pylink.KB_RELEASE)
        self.eyelink.setAcceptTargetFixationButton(SPACE_KEY)

        # push calibration draw and key_press handlers to window
        self.win.push_handlers(on_draw=self._on_draw_target, on_key_press=self._on_key_press_calibration)

        # schedule calibration update
        pyglet.clock.schedule(self._update_calibration)

    def _on_draw_target(self):
        self.win.clear()
        self.bg.draw()
        self.target.draw()

        return pyglet.event.EVENT_HANDLED # stop propagating down the on_draw handler stack

    def _on_key_press_calibration(self, symbol, modifiers):
        if symbol == pyglet.window.key.SPACE:
            # (manually) accept target fixation
            self.eyelink.sendKeybutton(SPACE_KEY, 0, pylink.KB_PRESS)
            self.eyelink.sendKeybutton(SPACE_KEY, 0, pylink.KB_RELEASE)

        if symbol == pyglet.window.key.BACKSPACE:
            # repeat previous target
            self.eyelink.sendKeybutton(BACKSPACE_KEY, 0, pylink.KB_PRESS)
            self.eyelink.sendKeybutton(BACKSPACE_KEY, 0, pylink.KB_RELEASE)

        if (symbol == pyglet.window.key.Q) or (symbol == pyglet.window.key.ESCAPE):
            self.eyelink.sendKeybutton(ESC_KEY, 0, pylink.KB_PRESS)
            self.eyelink.sendKeybutton(ESC_KEY, 0, pylink.KB_RELEASE)
            self.eyelink.startSetup()
            self.win.pop_handlers() # pop self._on_key_press_calibration
            # self.win.pop_handlers() # pop self._on_draw_target
            pyglet.clock.unschedule(self._update_calibration)
            self.c_status = 27
            self._showStatusScreen("Calibration was aborted.")

        return pyglet.event.EVENT_HANDLED # stop propagating down the on_key_press handler stack

    def _update_calibration(self, dt):
        # get calibration target position
        p = self.eyelink.getTargetPositionAndState()
        if p[0]:
            self.target.set_x(p[1])
            self.target.set_y(p[2])
            self.target.show()
        else:
            self.target.hide()

        # check if calibration ended
        c = self.eyelink.getCalibrationResult()
        if c != 1000:
            pyglet.clock.unschedule(self._update_calibration)
            self.win.pop_handlers() # pop self._on_key_press_calibration

            self.c_status = c
            c_msg = self.eyelink.getCalibrationMessage()
            self._showCalibrationDoneScreen(c_msg)


    ## CALIBRATION DONE
    def _showCalibrationDoneScreen(self, msg):
        self.text.text = f"Calibration {STATUS_MSGS[self.c_status]}\
            \n\t> {msg}\
            \nPress ENTER to accept the calibration and continue.\
            \nPress C to calibrate again.\
            \nPress V to validate.\
            \nPress BACKSPACE/ DELETE to discard the calibration."

        # The drawing is the same as for the finished screen, so we can reuse that.
        self.win.push_handlers(on_draw=self._on_draw_text, on_key_press=self._on_key_press_calibration_done)

    def _on_key_press_calibration_done(self, symbol, modifiers):
        if symbol == pyglet.window.key.ENTER:
            # accept calibration.
            self.eyelink.sendKeybutton(ENTER_KEY, 0, pylink.KB_PRESS)
            self.eyelink.sendKeybutton(ENTER_KEY, 0, pylink.KB_RELEASE)

            # return from calibration and continue/ call callback
            self.win.pop_handlers()
            self._showStatusScreen("Calibration accepted.")

        if symbol == pyglet.window.key.C:
            # restart calibration on tracker
            self.eyelink.sendKeybutton(DELETE_KEY, 0, pylink.KB_PRESS)
            self.eyelink.sendKeybutton(DELETE_KEY, 0, pylink.KB_RELEASE)

            # start local handling
            self.win.pop_handlers()
            self.calibrate(self.callback)

        if symbol == pyglet.window.key.V:
            # restart calibration on tracker
            self.eyelink.sendKeybutton(V_KEY, 0, pylink.KB_PRESS)
            self.eyelink.sendKeybutton(V_KEY, 0, pylink.KB_RELEASE)

            # start local handling
            self.win.pop_handlers()
            self.validate()

        if (symbol == pyglet.window.key.BACKSPACE) or (symbol == pyglet.window.key.DELETE):
            # Discard calibration without repeating
            self.eyelink.sendKeybutton(ESC_KEY, 0, pylink.KB_PRESS)
            self.eyelink.sendKeybutton(ESC_KEY, 0, pylink.KB_RELEASE)

            # show status screen
            self.win.pop_handlers()
            self.c_status = 1000
            self._showStatusScreen("Calibration discarded.")

        return pyglet.event.EVENT_HANDLED


    ### VALIDATION
    def validate(self):
        """Starts the validation procedure. Shows the status screen afterwards. 
        This function provides NO entry point to the setup as a validation is usually done after a calibration.
        """
        # start validation process
        self.eyelink.sendKeybutton(V_KEY, 0, pylink.KB_PRESS)
        self.eyelink.sendKeybutton(V_KEY, 0, pylink.KB_RELEASE)
        self.eyelink.setAcceptTargetFixationButton(SPACE_KEY)

        # The procedure is the same as for calibration, so we can use the same draw handler
        self.win.push_handlers(on_draw=self._on_draw_target, on_key_press=self._on_key_press_validation)

        # schedule validation update
        pyglet.clock.schedule(self._update_validation)

    def _on_key_press_validation(self, symbol, modifiers):
        if symbol == pyglet.window.key.SPACE:
            # (manually) accept target fixation
            self.eyelink.sendKeybutton(SPACE_KEY, 0, pylink.KB_PRESS)
            self.eyelink.sendKeybutton(SPACE_KEY, 0, pylink.KB_RELEASE)

        if symbol == pyglet.window.key.BACKSPACE:
            # repeat previous target
            self.eyelink.sendKeybutton(BACKSPACE_KEY, 0, pylink.KB_PRESS)
            self.eyelink.sendKeybutton(BACKSPACE_KEY, 0, pylink.KB_RELEASE)

        if (symbol == pyglet.window.key.Q) or (symbol == pyglet.window.key.ESCAPE):
            self.eyelink.sendKeybutton(ESC_KEY, 0, pylink.KB_PRESS)
            self.eyelink.sendKeybutton(ESC_KEY, 0, pylink.KB_RELEASE)
            self.eyelink.startSetup()
            self.win.pop_handlers() # pop self._on_key_press_calibration
            pyglet.clock.unschedule(self._update_validation)
            self.v_status = 27
            self._showStatusScreen("Validation was aborted.")

        return pyglet.event.EVENT_HANDLED
    
    def _update_validation(self, dt):
        # get validation target position
        p = self.eyelink.getTargetPositionAndState()
        if p[0]:
            self.target.set_x(p[1])
            self.target.set_y(p[2])
            self.target.show()
        else:
            self.target.hide()

        # check if  ended
        v = self.eyelink.getCalibrationResult()
        if v != 1000:
            pyglet.clock.unschedule(self._update_validation)
            self.win.pop_handlers() # pop self._on_key_press_calibration

            self.v_status = v
            v_msg = self.eyelink.getCalibrationMessage()
            self._showValidationDoneScreen(v_msg)


    ## VALIDATION DONE
    def _showValidationDoneScreen(self, msg):
        self._v_msg = msg
        self.text.text = f"Validation {STATUS_MSGS[self.v_status]}\
            \n\t> {msg}\
            \nPress ENTER to accept the validation and continue.\
            \nPress V to validate again.\
            \nPress BACKSPACE/ DELETE to discard the validation."

        # The drawing is the same as for the finished screen, so we can reuse that.
        self.win.push_handlers(on_draw=self._on_draw_text, on_key_press=self._on_key_press_validation_done)

    def _on_key_press_validation_done(self, symbol, modifiers):
        if symbol == pyglet.window.key.V:
            # restart validation on tracker
            self.eyelink.sendKeybutton(DELETE_KEY, 0, pylink.KB_PRESS)
            self.eyelink.sendKeybutton(DELETE_KEY, 0, pylink.KB_RELEASE)

            # start local handling
            self.win.pop_handlers()
            self.validate()

        if (symbol == pyglet.window.key.BACKSPACE) or (symbol == pyglet.window.key.DELETE):
            # Discard validation without repeating
            self.eyelink.sendKeybutton(ESC_KEY, 0, pylink.KB_PRESS)
            self.eyelink.sendKeybutton(ESC_KEY, 0, pylink.KB_RELEASE)

            # show status screen
            self.win.pop_handlers()
            self.v_status = 1000
            self._showStatusScreen("Validation discarded.")

        if symbol == pyglet.window.key.ENTER:
            # accept calibration and validation.
            self.eyelink.sendKeybutton(ENTER_KEY, 0, pylink.KB_PRESS)
            self.eyelink.sendKeybutton(ENTER_KEY, 0, pylink.KB_RELEASE)

            # store validation error
            v_res = self._v_msg.split(":")[1].strip().split(" ")
            self.v_error = (float(v_res[0]), float(v_res[4]))

            # return from calibration and continue/ call callback
            self.win.pop_handlers()
            self._showStatusScreen("Validation accepted.")

        return pyglet.event.EVENT_HANDLED
        

    ### DRIFT CORRECTION
    def driftCorrect(self, callback, direct_return=True):
        """Possible entry point. Immediately starts the drift correction. Shows the stastus screen afterwards.
        Args:
            callback (function): Callable that is called when setup is completed.
        """
        self.callback = callback
        self._drift_correct_direct_return = direct_return

        
        # place target in the middle of the screen
        self.target.set_x(self.win.width//2)
        self.target.set_y(self.win.height//2)
        self.target.show()

        self.eyelink.startDriftCorrect(self.win.width//2, self.win.height//2)

        # make sure "Apply correction" is active
        # ... TODO

        self.win.push_handlers(on_draw=self._on_draw_target, on_key_press=self._on_key_press_drift)
        pyglet.clock.schedule(self._update_drift)

        # same process as done before:
        # # start drift correction process
        # self.eyelink.sendKeybutton(D_KEY, 0, pylink.KB_PRESS)
        # self.eyelink.sendKeybutton(D_KEY, 0, pylink.KB_RELEASE)
        # self.eyelink.setAcceptTargetFixationButton(SPACE_KEY)


    def _on_key_press_drift(self, symbol, modifiers):
        if symbol == pyglet.window.key.SPACE:
            self.eyelink.sendKeybutton(SPACE_KEY, 0, pylink.KB_PRESS)
            self.eyelink.sendKeybutton(SPACE_KEY, 0, pylink.KB_RELEASE)

        if (symbol == pyglet.window.key.Q) or (symbol == pyglet.window.key.ESCAPE):
            self.win.pop_handlers()
            pyglet.clock.unschedule(self._update_drift)

            # leave drift correct mode on tracker
            self.eyelink.sendKeybutton(ESC_KEY, 0, pylink.KB_PRESS)
            self.eyelink.sendKeybutton(ESC_KEY, 0, pylink.KB_RELEASE)
            # # enter setup mode
            # self.eyelink.startSetup()

            if self._drift_correct_direct_return:
                self.callback(27)
            else:
                self._showStatusScreen("Drift correction aborted.")

        return pyglet.event.EVENT_HANDLED
            
    def _update_drift(self, dt):
        d = self.eyelink.getCalibrationResult()
        if d != 1000:
            d_msg = self.eyelink.getCalibrationMessage()
            # print(f"> d_msg: {d_msg}")
            r = self.eyelink.applyDriftCorrect()

            self.win.pop_handlers()
            pyglet.clock.unschedule(self._update_drift)

            # enter setup mode
            self.eyelink.startSetup()

            self.d_status = d

            if self._drift_correct_direct_return:
                self.callback(d)
            else:
                self._showStatusScreen("Drift correction applied.")


    ### STATUS SCREEN
    def _showStatusScreen(self, msg = ""):
        self.text.text = f"STATUS:\
            \n\t> {msg}\
            \n\nCalibration: {STATUS_MSGS[self.c_status]}\
            \nValidation: {STATUS_MSGS[self.v_status]}{f' - avg. error: {self.v_error} °' if self.v_error is not None else ''}\
            \n\n\tPress C to {'(re)' if self.c_status != 1000 else ''}calibrate.\
            \n\tPress V to {'(re)' if self.v_status != 1000 else ''}validate.\
            \n\tPress D to drift correct.\
            \n\tPress Q/ENTER to quit setup and continue.\
            \n\nUse SPACE to manually accept a fixation."

        self.win.push_handlers(on_draw=self._on_draw_text, on_key_press=self._on_key_press_status)

    def _on_draw_text(self):
        self.win.clear()
        self.bg.draw()
        self.text.draw()

        return pyglet.event.EVENT_HANDLED

    def _on_key_press_status(self, symbol, modifiers):
        if symbol == pyglet.window.key.C:
            self.win.pop_handlers() # pop self._on_key_press_status and self._on_draw_text
            self.calibrate(self.callback)

        if symbol == pyglet.window.key.V:
            self.win.pop_handlers()
            self.validate()

        if symbol == pyglet.window.key.D:
            self.win.pop_handlers()
            self.driftCorrect(self.callback)

        if (symbol == pyglet.window.key.Q) or (symbol == pyglet.window.key.ENTER):
            self.eyelink.setOfflineMode()
            self.win.pop_handlers()
            self.callback(self.c_status)

        return pyglet.event.EVENT_HANDLED


    ### TRACKING
    def startRecording(self, msg="trial start") -> None:
        """Starts recording. Requires an opened file.
        Will log the provided message and a timestamp to the edf file.
        Args:
            msg (str, optional): Message logged to the edf file upon start of recording.
                Could contain the trial ID. Defaults to "trial start".
        """
        self.trial_msg = msg

        timestamp = datetime.datetime.now()
        self.eyelink.sendMessage(f"TIMESTAMP {timestamp} - START OF TRIAL {msg}")
        # arguments: sample_to_file, events_to_file, sample_over_link, event_over_link 
        self.eyelink.startRecording(1, 1, 1, 1)

    def stopRecording(self) -> None:
        """Stops recording. 
        Will log the same message used for starting the trial and a timestamp to the edf file.
        """
        timestamp = datetime.datetime.now()
        self.eyelink.sendMessage(f"TIMESTAMP {timestamp} - END OF TRIAL {self.trial_msg}")
        self.eyelink.stopRecording()


    ### COMMUNICATION
    def getEyeSample(self) -> Tuple[Sample, Sample] | Sample:
        """Return the latest eye sample. A sample contains 
            Gaze position as (x, y) in px
            HREF as (x, y) in px
            Pupil raw as (x, y) in px
            Pupil size as (x, y) in ?mycro meter?

        If both eyes are tracked, a tuple of two samples is returned. Otherwise only one sample

        Returns:
            Tuple[Sample, Sample]: Sample of the Left and Sample of the Right eye.
        """
        s = self.eyelink.getNewestSample()

        if self.eye == "both":
            if s.isLeftSample():
                l = s.getLeftEye()
                ls = Sample(l.getGaze(), l.getHREF(), l.getRawPupil(), l.getPupilSize())
            else:
                ls = self.dummy_sample

            if s.isRightSample():
                r = s.getRightEye()
                rs = Sample(r.getGaze(), r.getHREF(), r.getRawPupil(), r.getPupilSize())
            else:
                rs = self.dummy_sample

            return (ls, rs)
        else:
            if s.isLeftSample():
                if self.eye == "left":
                    l = s.getLeftEye()
                    return Sample(l.getGaze(), l.getHREF(), l.getRawPupil(), l.getPupilSize())
                else:
                    raise(ValueError, "Expected left eye sample but received right eye sample.")
            elif s.isRightSample():
                if self.eye == "right":
                    r = s.getRightEye()
                    return Sample(r.getGaze(), r.getHREF(), r.getRawPupil(), r.getPupilSize())
                else:
                    raise(ValueError, "Expected right eye sample but received left eye sample.")
            else:
                raise(ValueError, "Received sample is neither left nor right.")
                # return self.dummy_sample
