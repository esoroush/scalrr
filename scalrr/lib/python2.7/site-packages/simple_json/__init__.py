"""
simple_json was renamed to simplejson to comply with PEP 8 module naming
conventions.  This is a compatibility shim.

%s/simple_json/simplejson/g
"""
__version__ = '1.1'
import warnings
warnings.warn(
    "simple_json is deprecated due to rename, import simplejson instead",
    DeprecationWarning)
import pkg_resources
pkg_resources.require('simplejson')
import simplejson
from simplejson import *
__all__ = simplejson.__all__
