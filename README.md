## EyeLink Connector Class for Pygame and Pyglet

[pylink](https://pypi.org/project/PyLink/) is an awesome interface and offers great flexibility. <br>
However, when setting up an eye-tracking application, you may want something with a bit higher-level interface.

Also, it seems it only supports calibration for the backends `psychopy` and `pygame`, and not for `pyglet`.

So, here we go: An EyeLink Connector Class developed for and tested on the EyeLink 1000+ with python>=3.10 on Windows.

---
Current limitations
* When performing a drift correction you have to manually check that "Apply Correction" is toggled 'on'
---

## Installation

If you want to use it only for pygame, pyglet, OR psychopy see below.

Install the package

```bash
pip install pyelink-connector
```

If you want to install only the dependencies for pygame, pyglet or psychopy use the following command with only the one backend you need needed:
```bash
pip install pyelink-connector[<pygame|pyglet|psychopy>]
```

If you have no running pylink version for your EyeLink 1000 + yet, also see [Installing pylink](#installing-pylink) below.

### Dependencies
The pylink_connector was built for the following packages

* pygame-ce==2.5.3
* pyglet==2.0.15
* psychopy==2024.2.4

... and should support new versions. Other versions might work as well.

It further requires software by [SR-Research](https://www.sr-research.com).

### Installing pylink
<a name="installing-pylink"></a>
#### System wide python
You can find some support for installing pylink for communicating with an EyeLink, for example, on the [SR-Research forum](https://www.sr-research.com/support/thread-48.html).

I have not tested their suggestion, because I was using a conda python environment.

#### Using conda or other virtual python environments
When working with a conda environment, only installing [pylink](https://pypi.org/project/PyLink/) with pip to was not sufficient to communicate with the EyeLink 1000 + in my case.
I figured out the following procedure to install pylink for communicating with an EyeLink

1. Download and install the [SR-Research development kit](https://www.sr-research.com/support/showthread.php?tid=13). You need to register an account to access the page.
2. Create your conda environment with its own python version. For example

```bash
conda create -n eyeLinkEnv --python=3.12
```

3. Activate it and install pylink with pip.

```bash
conda activate eyeLinnkEnv
pip install pylink
```

4. Windows specific: Copy the pylink files that came with the development kit to the site-packages folder of pylink of your environment. You can adapt the example below to your needs.

Example:
    Assuming
    - you installed the SR development kit to `C:\Program Files (x86)\SR Research\` 
    - the python packages of your conda environment are located at `C:\Users\USERNAME\.conda\envs\eyeLinkEnv\Lib\site-packages`
    - and you are using 3.12...
    then you can copy the contents of `C:\Program Files (x86)\SR Research\EyeLink\SampleExperiments\Python\64\3.12\pylink` to `C:\Users\USERNAME\.conda\envs\eyeLinkEnv\Lib\site-packages\pylink\`


## Usage
Minimum example with pygame

```python
from pyelink_connector.pygameConnector.pygame import EyeConnector

settings = {
        "render_fps": 60,
        }

pygame.init()

surface = pygame.display.set_mode(depth=0, display=0, vsync=1, flags=pygame.FULLSCREEN)

eyeConnector = EyeConnector(win=surface, prefix="TEST")
eyeConnector.openFile(file_name="pga")

# Perform calibration and validation
eyeConnector.runSetup(settings=settings)

eyeConnector.startRecording(msg="test trial start")

# show your stimuli
...

eyeConnector.stopRecording()

eyeConnector.downloadFile()
eyeConnector.close()
```

You can find more examples for pygame, pyglet and psychopy on github.

## Build locally
This package was build using `'python -m build`. <br>

## Contact & Support

I am happy for any bug reports or feature requests! Please use github for these.

If the pyelink-connector was helpful to you and you feel like supporting, you are welcome to [buy me a coffee](https://buymeacoffee.com/uvest) or simply [reach out](mailto:kai.streiling@gmail.com) and tell me how you made use of this package!
