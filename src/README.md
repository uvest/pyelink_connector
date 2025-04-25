## Code structure


## API

Have a look at the functions doc strings for more details.

### Status codes
Status codes are taken from the pylink manual and are defined as followed:

* 1000 = not done/ still running
* 0 = success
* 27 = Aborted (ESC pressed)
* 1 = failed (poor result)
* -1 = failed
* 2 = ... 

---

**Deprecated** <br>
The following information might be deprecated.


### Pyglet specific information
All you need to initialize a connector object is a pyglet window. All other parameters are optional but may help to manage your experiment.

```py
def __init__(self, win:pyglet.window.Window, host:str="100.1.1.1", prefix:str="", download_directory:str="./eye_tracking/") -> None:
        """Create connector object to communicate with an EyeLink 1000+.
        Args:
            host (str, optional): IP of the EyeLink Host PC. Defaults to "100.1.1.1".
            prefix (str, optional): Session prefix. Will be added to all files handled by this connection. 
                                    Could, e.g., combine experiment and participant ID. Defaults to "".
            download_directory (str, optional): Local directory to store downloaded EDF files to. Defaults to "./eye_tracking/".
        """
```

### Starting the setup
You currently have 3 entry points to the setup:

* `startSetup(self, callback)` <br>
    Possible entry point. Shows the status screen from which other functions can be called.

    Args:<br>
        callback (function): Callable that is called when setup is completed.

* `calibrate(self, callback)` <br>
    Possible entry point. Immediately starts the calibration. Shows the stastus screen afterwards.

    Args: <br>
        callback (function): Callable that is called when setup is completed.

* `driftCorrect(self, callback, direct_return=True)` <br>
    Possible entry point. Immediately starts the drift correction. Shows the stastus screen afterwards.

    Args: <br>
        callback (function): Callable that is called when setup is completed.


`startSetup` and `calibrate` will end on the status screen from which the user can return to their experiment by pressing Q or ENTER. <br>
`driftCorrect` will either return directly (`direct_return=True`) or also end on the status screen (`direct_return=True`).

Upon returning from the setup, the connector will call the provided *callback* function. <br>
This callback function must accept one integer parameter which is the respective status of the performed setup action:
* If returning from the setup status screen (as for calibration, validation and drift correction that does not immediately return), the callback is called with the current calibration status
* If returning from the drift correction directly, the callback is called with the current drift correction status


### Handling files
You can open, close and download an edf file on the tracker using the methods

* `openFile(self, file_name:str) -> None:` <br>
  Opens an edf file on the EyeLink. 

    Args: <brs>
        file_name (str): The edf file name is self.prefix + "_" + file_name, if self.prefix is specified. Otherwise it is just file_name.

* `closeFile(self) -> None:`

* `downloadFile(self) -> None:` <br>
    Closes open file and downloads it to self.download_directory.


### Managing recording
You can start and stop recording - which will write the samples and events to the file and provide the samples dirctly over the link - using:

* `startRecording(self, msg="trial start") -> None:` <br>
    Starts recording. Requires an opened file.
    Will log the provided message and a timestamp to the edf file.

    Args:<br>
        msg (str, optional): Message logged to the edf file upon start of recording.
            Could contain the trial ID. Defaults to "trial start".

* `stopRecording(self) -> None:` <br>
    Stops recording.
    Will log the same message used for starting the trial and a timestamp to the edf file.


### Downloading Samples online
You can get the latest sample of both eyes during your experiment by simply using

* `getEyeSample(self) -> Tuple[Sample, Sample]:`<br>
    Return the latest eye sample. A sample contains <br>
        Gaze position as (x, y) in px<br>
        HREF as (x, y) in px<br>
        Pupil raw as (x, y) in px<br>
        Pupil size as (x, y) in ?mycro meter?<br>

    Returns:<br>
        Tuple[Sample, Sample]: Sample of the Left and Sample of the Right eye.



## Examples
For a usage example look at the [test_pyglet_pylink_connector.py](./test_pyglet_pylink_connector.py) script.

This will first start the setup, giving you the chance to calibate, validate and/ or drift correct.
After the setup returned this script will display a red target and the eye position of the left (green) and right (blue) eye as retrieved from the tracker.
