import pylink
from psychopy import visual, core, event
from psychopy.hardware import keyboard
from psychopy.visual import Window

import datetime
import os

from typing import Tuple

from .utils import Target, MultiLineText
from ..utils import *


class EyeConnector():
    def __init__(self, win:Window, host:str="100.1.1.1", eye:str="both", prefix:str="", download_directory:str="./eye_tracking/",
                 sample_rate:int=1000) -> None:
        """Create connector object to communicate with an EyeLink 1000+.
        Args:
            win (pygame.Surface): Surface to draw to during setup.
            host (str, optional): IP of the EyeLink Host PC. Defaults to "100.1.1.1".
            eye (str, optional): Choose which eye to track. Options: ["both", "right", "left"]. Defaults to "both".
            prefix (str, optional): Session prefix. Will be added to all files handled by this connection. 
                                    Could, e.g., combine experiment and participant ID. Defaults to "".
            download_directory (str, optional): Local directory to store downloaded EDF files to. Defaults to "./eye_tracking/".
            sample_rate (int, optional): Sampling rate. Should not exceed 1000 for tracking both eyes. Defaults to 1000.
        """
        self.win = win
        self.kb = keyboard.Keyboard()
        self.host = host
        self.eyelink = self.connect(host)

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
        self.isFileOpen = False
        self.sample_rate = sample_rate

        os.makedirs(self.download_directory, exist_ok=True)

        # assume the whole monitor is used. Get resolution from system.
        self._w, self._h = win.size

        # displayable objects
        self.bg_color = GREY
        self.target = Target(self.win)
        
        # for handling communication to EyeLink
        self.dummy_sample = Sample((self._w, self._h), (self._w, self._h), (self._w, self._h), 0.)


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
            file_name (str): The edf file name is self.prefix + "_" + file_name, if self.prefix is specified. 
                Otherwise it is just file_name. Total fil name length must not exceed 8 characters.
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
        self.eyelink.sendCommand(f"add_file_preamble_text 'RECORDED BY Pylink-Pygame Connector tagged {self.prefix}'")

        # define coordinate system [LEFT, TOP, RIGHT, BOTTOM]
        self.eyelink.sendMessage(f"DISPLAY_COORDS {-self._w/2} {self._h/2} {self._w/2} {-self._h/2}") # DISPLAY_COORDS msg is used by the DATA VIEWER
        self.eyelink.sendCommand(f"screen_pixel_coords = {-self._w/2} {self._h/2} {self._w/2} {-self._h/2}") # This should be used for defining calibration targets... 

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

        # switch flag for housekeeping
        self.isFileOpen = True

    def closeFile(self) -> None:
        """Sets the tracker to offline mode and closes the currently opened edf file"""
        self.eyelink.setOfflineMode()
        self.eyelink.closeDataFile()

        # switch flag for housekeeping
        self.isFileOpen = False

    def downloadFile(self) -> None:
        """Closes open file and downloads it to self.download_directory."""
        self.closeFile()
        self.eyelink.receiveDataFile(self.edf_file_name, self.download_directory + self.edf_file_name)


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


    ####################### PYGAME specific
    ### GENERAL SETUP ENTRY
    def runSetup(self) -> None:
        """Possible entry point. Requires an opened edf file on the host PC.
        Show the steup screen from which calibration, validation and drift-correction can be started.
        """
        assert(self.isFileOpen)

        # enter setup mode
        self.eyelink.startSetup()

        # hide mouse if shown
        _mousWasVisible = self.win.mouseVisible
        self.win.setMouseVisible(False)

        # show calibration info screen
        done = False
        text = f"STATUS:\
            \n\nCalibration: {STATUS_MSGS[self.c_status]}\
            \nValidation: {STATUS_MSGS[self.v_status]}{f' - avg. error: {self.v_error} °' if self.v_error is not None else ''}\
            \n\n\tPress C to {'(re)' if self.c_status != 1000 else ''}calibrate.\
            \n\tPress V to {'(re)' if self.v_status != 1000 else ''}validate.\
            \n\tPress D to drift correct.\
            \n\tPress Q/ENTER to quit setup and continue.\
            \n\nUse SPACE to manually accept a fixation."
        mlText = MultiLineText(self.win, text)

        # clear key events
        self.kb.clearEvents()

        while not done:
            # handle events
            for key in self.kb.getKeys():
                if key == 'c':
                    msg = self.calibrate()
                    # Update the status text
                    text = f"STATUS:\
                        \n\t>{msg}\
                        \n\nCalibration: {STATUS_MSGS[self.c_status]}\
                        \nValidation: {STATUS_MSGS[self.v_status]}{f' - avg. error: {self.v_error} °' if self.v_error is not None else ''}\
                        \n\n\tPress C to {'(re)' if self.c_status != 1000 else ''}calibrate.\
                        \n\tPress V to {'(re)' if self.v_status != 1000 else ''}validate.\
                        \n\tPress D to drift correct.\
                        \n\tPress Q/ENTER to quit setup and continue.\
                        \n\nUse SPACE to manually accept a fixation."
                    mlText = MultiLineText(self.win, text)
                elif key == 'v':
                    msg = self.validate()
                    # Update the status text
                    text = f"STATUS:\
                        \n\t>{msg}\
                        \n\nCalibration: {STATUS_MSGS[self.c_status]}\
                        \nValidation: {STATUS_MSGS[self.v_status]}{f' - avg. error: {self.v_error} °' if self.v_error is not None else ''}\
                        \n\n\tPress C to {'(re)' if self.c_status != 1000 else ''}calibrate.\
                        \n\tPress V to {'(re)' if self.v_status != 1000 else ''}validate.\
                        \n\tPress D to drift correct.\
                        \n\tPress Q/ENTER to quit setup and continue.\
                        \n\nUse SPACE to manually accept a fixation."
                    mlText = MultiLineText(self.win, text)
                elif key == 'd':
                    msg = self.driftCorrect()
                    # Update the status text
                    text = f"STATUS:\
                        \n\t>{msg}\
                        \n\nCalibration: {STATUS_MSGS[self.c_status]}\
                        \nValidation: {STATUS_MSGS[self.v_status]}{f' - avg. error: {self.v_error} °' if self.v_error is not None else ''}\
                        \n\n\tPress C to {'(re)' if self.c_status != 1000 else ''}calibrate.\
                        \n\tPress V to {'(re)' if self.v_status != 1000 else ''}validate.\
                        \n\tPress D to drift correct.\
                        \n\tPress Q/ENTER to quit setup and continue.\
                        \n\nUse SPACE to manually accept a fixation."
                    mlText = MultiLineText(self.win, text)
                elif key == 'q' or key == "return":
                    done = True

            # render text
            mlText.render()

            # update window
            self.win.flip()


        self.eyelink.setOfflineMode()

        # show mouse if it was shown
        self.win.setMouseVisible(_mousWasVisible)

        return
            
    ### CALIBRATION 
    def calibrate(self) -> None:
        """Possible entry point. Requires an opened edf file on the host PC.
        Performs the calibration. Shows a status screen when done.
        Upon exiting the status screen, a status message is returned.
        """
        assert(self.isFileOpen)

        # enter setup mode
        self.eyelink.startSetup()

        # hide mouse if shown
        _mousWasVisible = self.win.mouseVisible
        self.win.setMouseVisible(False)

        # configure calibration
        self.eyelink.setCalibrationType("HV9")
        self.eyelink.sendCommand("calibration_area_proportion = 0.5 0.5")
        self.eyelink.sendCommand("validation_area_proportion = 0.5 0.5")

        # start calibration on host
        self.eyelink.sendKeybutton(C_KEY, 0, pylink.KB_PRESS)
        self.eyelink.sendKeybutton(C_KEY, 0, pylink.KB_RELEASE)
        self.eyelink.setAcceptTargetFixationButton(SPACE_KEY)

        # clear key events
        self.kb.clearEvents()

        # DO calibration
        msg = ""
        done = False

        while not done:
            # handle events
            for key in self.kb.getKeys():
                if key == 'space':
                    # (manually) accept target fixation
                    self.eyelink.sendKeybutton(SPACE_KEY, 0, pylink.KB_PRESS)
                    self.eyelink.sendKeybutton(SPACE_KEY, 0, pylink.KB_RELEASE)
                if key == 'backspace':
                    # repeat previous target
                    self.eyelink.sendKeybutton(BACKSPACE_KEY, 0, pylink.KB_PRESS)
                    self.eyelink.sendKeybutton(BACKSPACE_KEY, 0, pylink.KB_RELEASE)
                elif key == 'q' or key == "escape":
                    self.eyelink.sendKeybutton(ESC_KEY, 0, pylink.KB_PRESS)
                    self.eyelink.sendKeybutton(ESC_KEY, 0, pylink.KB_RELEASE)
                    self.c_status = 27
                    msg = "Calibration was aborted."
                    done = True

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
                self.c_status = c
                msg = self.eyelink.getCalibrationMessage()
                done = True

            # render target
            self.target.render()

            # update
            self.win.flip()

        # show mouse if it was shown
        self.win.setMouseVisible(_mousWasVisible)

        self._showCalibrationDoneScreen(msg=f"Calibration status: {STATUS_MSGS[self.c_status]}. Result: {msg}")

    def _showCalibrationDoneScreen(self, msg:str="") -> str:
        """Shows calibration results. Should not be called directly.
            May call calibrate (again) or validate from here.
            Upon exit, a status message is returend

        Args:
            msg (str, optional): Message to display. Defaults to "".

        Returns:
            str: Last actions status message.
        """    
        text = f"Calibration {STATUS_MSGS[self.c_status]}\
            \n\t> {msg}\
            \nPress ENTER to accept the calibration and continue.\
            \nPress C to calibrate again.\
            \nPress V to validate.\
            \nPress BACKSPACE/ DELETE to discard the calibration and return."
        mlText = MultiLineText(self.win, text)

        # hide mouse if shown
        _mousWasVisible = self.win.mouseVisible
        self.win.setMouseVisible(False)

        # clear key events
        self.kb.clearEvents()

        callback = None
        msg = ""
        done = False
        while not done:
            # handle events
            for key in self.kb.getKeys():
                if key == 'return':
                    # accept calibration.
                    self.eyelink.sendKeybutton(ENTER_KEY, 0, pylink.KB_PRESS)
                    self.eyelink.sendKeybutton(ENTER_KEY, 0, pylink.KB_RELEASE)
                    callback = None
                    msg = "Calibration accepted."
                    done = True
                if key == 'c':
                    # restart calibration on tracker
                    self.eyelink.sendKeybutton(DELETE_KEY, 0, pylink.KB_PRESS)
                    self.eyelink.sendKeybutton(DELETE_KEY, 0, pylink.KB_RELEASE)
                    callback = self.calibrate
                    done = True
                if key == 'v':
                    callback = self.validate
                    done = True
                if key == 'backspace' or key == 'delete':
                    # Discard calibration without repeating
                    self.eyelink.sendKeybutton(ESC_KEY, 0, pylink.KB_PRESS)
                    self.eyelink.sendKeybutton(ESC_KEY, 0, pylink.KB_RELEASE)
                    self.c_status = 1000
                    callback = None
                    msg = "Calibration discarded."
                    done = True

            # render text
            mlText.render()

            # update
            self.win.flip()

        # show mouse if it was visible
        self.win.setMouseVisible(_mousWasVisible)

        if callback is not None:
            return callback()
        else:
            return msg


    ### VALIDATION
    def validate(self) -> None:
        """Possible entry point. Requires an opened edf file and successfull calibration on the host PC.
        Performs the validation. Shows a status screen when done.
        Should be called from the calibration-done-screen or the setup-screen.
        Calling from the experiment directly may cause problems.
        Upon exiting the status screen, a status message is returned.
        """
        assert(self.isFileOpen)

        # start validation process
        self.eyelink.sendKeybutton(V_KEY, 0, pylink.KB_PRESS)
        self.eyelink.sendKeybutton(V_KEY, 0, pylink.KB_RELEASE)
        self.eyelink.setAcceptTargetFixationButton(SPACE_KEY)

        # hide mouse if shown
        _mousWasVisible = self.win.mouseVisible
        self.win.setMouseVisible(False)

        # clear key events
        self.kb.clearEvents()

        # DO validation
        msg = ""
        done = False
        while not done:
            # handle events
            keys = self.kb.getKeys()
            for key in keys:
                if key == 'space':
                    # (manually) accept target fixation
                    self.eyelink.sendKeybutton(SPACE_KEY, 0, pylink.KB_PRESS)
                    self.eyelink.sendKeybutton(SPACE_KEY, 0, pylink.KB_RELEASE)
                if key == 'backspace':
                    # repeat previous target
                    self.eyelink.sendKeybutton(BACKSPACE_KEY, 0, pylink.KB_PRESS)
                    self.eyelink.sendKeybutton(BACKSPACE_KEY, 0, pylink.KB_RELEASE)

                if key == 'q' or key == 'escape':
                    self.eyelink.sendKeybutton(ESC_KEY, 0, pylink.KB_PRESS)
                    self.eyelink.sendKeybutton(ESC_KEY, 0, pylink.KB_RELEASE)
                    self.v_status = 27
                    msg = "Validation was aborted."
                    done = True

            # get validation target position
            p = self.eyelink.getTargetPositionAndState()
            if p[0]:
                self.target.set_x(p[1])
                self.target.set_y(p[2])
                self.target.show()
            else:
                self.target.hide()

            # check if validation ended
            v = self.eyelink.getCalibrationResult()
            if v != 1000:
                self.v_status = v
                msg = self.eyelink.getCalibrationMessage()
                done = True

            # render target
            self.target.render()

            # update
            self.win.flip()

        # show mouse if it was visible
        self.win.setMouseVisible(_mousWasVisible)

        self._showValidationDoneScreen(msg=f"Validation status: {STATUS_MSGS[self.v_status]}. Result: {msg}")

    def _showValidationDoneScreen(self, msg:str="") -> str:
        """Shows validation results. Should not be called directly.
            May call validate again from here.
            Upon exit, a status message is returend

        Args:
            msg (str, optional): Message to display. Defaults to "".
            
        Returns:
            str: Last actions status message.
        """    
        text = f"Validation {STATUS_MSGS[self.v_status]}\
            \n\t> {msg}\
            \nPress ENTER to accept the validation and continue.\
            \nPress V to validate again.\
            \nPress BACKSPACE/ DELETE to discard the validation."
        mlText = MultiLineText(self.win, text)

        # hide mouse if shown
        _mousWasVisible = self.win.mouseVisible
        self.win.setMouseVisible(False)

        # clear key events
        self.kb.clearEvents()

        callback = None
        msg = None
        done = False
        while not done:
            # handle events
            for key in self.kb.getKeys():
                if key == 'return':
                    # accept validation.
                    self.eyelink.sendKeybutton(ENTER_KEY, 0, pylink.KB_PRESS)
                    self.eyelink.sendKeybutton(ENTER_KEY, 0, pylink.KB_RELEASE)
                    callback = None
                    msg = "Validation accepted."
                    done = True

                if key == 'v':
                    # restart validation on tracker
                    self.eyelink.sendKeybutton(DELETE_KEY, 0, pylink.KB_PRESS)
                    self.eyelink.sendKeybutton(DELETE_KEY, 0, pylink.KB_RELEASE)
                    callback = self.validate
                    done = True

                if key == 'backspace' or key == 'delete':
                    # Discard validation without repeating
                    self.eyelink.sendKeybutton(ESC_KEY, 0, pylink.KB_PRESS)
                    self.eyelink.sendKeybutton(ESC_KEY, 0, pylink.KB_RELEASE)
                    self.v_status = 1000
                    callback = None
                    msg = "Validation discarded."
                    done = True

            # render text
            mlText.render()

            # update
            self.win.flip()

        # show mouse if it was visible
        self.win.setMouseVisible(_mousWasVisible)

        if callback is not None:
            return callback()
        else:
            return msg


    ### DRIFT CORRECTION
    def driftCorrect(self, settings:dict) -> str:
        """Possible entry point. Requires an opened edf file on the host PC.
        Perform drift correction. 
        ATTENTION: Make sure that "Apply correction" is active on the drift correction screen on the EyeLink Host PC.

        Args:
            settings (dict): required keys: render_fps

        Returns:
            str: drift correction result
        """
        # position target and make visible
        self.target.set_pos([0,0])
        self.target.show()

        # hide mouse if shown
        _mousWasVisible = self.win.mouseVisible
        self.win.setMouseVisible(False)

        self.eyelink.startDriftCorrect(self._w, self._h)
        # make sure "Apply correction" is active
        # ... TODO

        # clear key events
        self.kb.clearEvents()

        done = False
        while not done:
            # handle events
            for key in self.kb.getKeys():
                if key == 'space':
                    self.eyelink.sendKeybutton(SPACE_KEY, 0, pylink.KB_PRESS)
                    self.eyelink.sendKeybutton(SPACE_KEY, 0, pylink.KB_RELEASE)

                if key == 'q' or key == 'escape':
                    # leave drift correct mode on tracker
                    self.eyelink.sendKeybutton(ESC_KEY, 0, pylink.KB_PRESS)
                    self.eyelink.sendKeybutton(ESC_KEY, 0, pylink.KB_RELEASE)
                    self.d_status = 27
                    done = True

            # get drift correct status
            d = self.eyelink.getCalibrationResult()
            if d != 1000:
                self.d_status = d
                d_msg = self.eyelink.getCalibrationMessage()
                # print(f"> d_msg: {d_msg}")

                r = self.eyelink.applyDriftCorrect()
                # print(f"> drift res: {r}")

                # enter setup mode
                self.eyelink.startSetup()
                done = True

            # render target
            self.target.render()

            # update
            self.win.flip()

        # show mouse if it was visible
        self.win.setMouseVisible(_mousWasVisible)

        return f"Drift correction: {STATUS_MSGS[self.d_status]}"
