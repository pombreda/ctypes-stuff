# pep328.subpackage1 package
from .moduleY import spam
from .moduleY import spam as ham
from . import moduleY
from ..subpackage1 import moduleY
from ..subpackage2.moduleZ import eggs
from ..moduleA import foo

# These are mentioned in PEP 328, but they do not work:
##from ...pep328 import bar
##from ...sys import path
