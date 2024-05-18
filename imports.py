"""
this file is used to simplify importing the necessary modules for video scripting
this way we just have to include "from pydeation.imports import *" in our scripts
"""


# rreload function not used right now but saved for future reference
from types import ModuleType

try:
    from importlib import reload  # Python 3.4+
except ImportError:
    # Needed for Python 3.0-3.3; harmless in Python 2.7 where imp.reload is just an
    # alias for the builtin reload.
    from imp import reload

def rreload(module):
    """Recursively reload modules."""
    reload(module)
    for attribute_name in dir(module):
        attribute = getattr(module, attribute_name)
        if type(attribute) is ModuleType:
            rreload(attribute)



# first we reload the sublibraries to update the changes
import sys
import importlib
import pydeation.scene
import pydeation.utils
import pydeation.objects.helper_objects
import pydeation.objects.camera_objects
import pydeation.objects.custom_objects
import pydeation.objects.effect_objects
import pydeation.objects.line_objects
import pydeation.objects.solid_objects
import pydeation.objects.sketch_objects
import pydeation.constants
import pydeation.xpresso.xpresso
import pydeation.xpresso.xpressions
import pydeation.xpresso.userdata
import pydeation.animation.abstract_animators

pydeation_path = "/Users/davidrug/Library/Preferences/Maxon/Maxon Cinema 4D R26_8986B2D7/python39/libs/pydeation"

if pydeation_path not in sys.path:
    print("add path")
    sys.path.insert(0, pydeation_path)

reload(pydeation.scene)
reload(pydeation.utils)
reload(pydeation.objects.helper_objects)
reload(pydeation.objects.camera_objects)
reload(pydeation.objects.custom_objects)
reload(pydeation.objects.effect_objects)
reload(pydeation.objects.line_objects)
reload(pydeation.objects.solid_objects)
reload(pydeation.objects.sketch_objects)
reload(pydeation.constants)
reload(pydeation.xpresso.xpresso)
reload(pydeation.xpresso.xpressions)
reload(pydeation.xpresso.userdata)
reload(pydeation.animation.abstract_animators)


# then we import the objects from the sublibraries
from pydeation.scene import *
from pydeation.objects.helper_objects import *
from pydeation.objects.camera_objects import *
from pydeation.objects.custom_objects import *
from pydeation.objects.effect_objects import *
from pydeation.objects.line_objects import *
from pydeation.objects.solid_objects import *
from pydeation.objects.sketch_objects import *
from pydeation.constants import *
from pydeation.xpresso.xpresso import *
from pydeation.xpresso.xpressions import *
from pydeation.xpresso.userdata import *
from pydeation.animation.abstract_animators import *

# we add the InterBrain path to the sys path to allow for importing the InterBrain modules
interbrain_path = "/Users/davidrug/Library/Mobile Documents/iCloud~md~obsidian/Documents/InterBrain"
sys.path.append(interbrain_path)