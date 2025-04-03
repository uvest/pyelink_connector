## EyeLink Connector Class for Pygame and Pyglet

[pylink](https://pypi.org/project/PyLink/){:target="_blank"} is an awesome interface and offers great flexibility. <br>
However, when setting up an eye-tracking application, you may want something with a bit higher-level interface.

Also, it seems it only supports calibration for the backends `psychopy` and `pygame`, and not for `pyglet`.

So, here we go: An EyeLink Connector Class developed for and tested on the EyeLink 1000+ with python>=3.10 on Windows.

---
Current limitations
* Currently `pyglet` and `pygame` are supported. Support for `psychopy` is coming soon.
* Currently only binoccular mode is supported. Support for tracking only one eye is coming soon.
---

## Installation

If you want to use it only for pygame OR pyglet, see below.

Install the package

```bash
pip install --index-url https://test.pypi.org/simple/ pyelink-connector
```

If you want to install only the dependencies for pygame use
```bash
pip install --index-url https://test.pypi.org/simple/ pyelink-connector[pygame]
```
If you want to install only the dependencies for pyglet use
```bash
pip install --index-url https://test.pypi.org/simple/ pyelink-connector[pyglet]
```

If you have no running pylink version for your EyeLink 1000 + yet, also see [Installing pylink](#installing-pylink) below.

### Dependencies
The pylink_connector was built for the following packages

* pygame-ce==2.5.3
* pyglet==2.0.15

Other versions might work as well.

It further requires software by [SR-Research](https://www.sr-research.com){:target="_blank"}.

### Installing pylink
#### System wide python
You can find some support for installing pylink for communicating with an EyeLink, for example, on the [SR-Research forum](https://www.sr-research.com/support/thread-48.html){:target="_blank"}.

I have not tested their suggestion, because I was using a conda python environment.

#### Using conda or other virtual python environments
When working with a conda environment, only installing [pylink](https://pypi.org/project/PyLink/){:target="_blank"} with pip to was not sufficient to communicate with the EyeLink 1000 + in my case.
I figured out the following procedure to install pylink for communicating with an EyeLink

1. Download and install the [SR-Research development kit](https://www.sr-research.com/support/showthread.php?tid=13){:target="_blank"}. You need to register an account to access the page.
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

self.eyeConnector.startRecording(msg="test trial start")

# show your stimuli
...

self.eyeConnector.stopRecording()

self.eyeConnector.downloadFile()
eyeConnector.close()
```

You can find more examples for pygame or pyglet on github.

## Contact & Support

I am happy for any bug reports or feature requests! Please use github for these.

If the pyelink-connector was helpful to you and you feel like supporting, you are welcome to [buy me a coffee](https://buymeacoffee.com/uvest){:target="_blank"} or simply [reach out](mailto:kai.streiling@gmail.com) and tell me how you made use of this package!
