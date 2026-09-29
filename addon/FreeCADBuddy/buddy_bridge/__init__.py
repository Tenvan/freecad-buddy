"""Transport between FreeCAD and the FreeCAD Buddy server.

Runs inside FreeCAD's Python and uses the standard library only (plus FreeCAD's ``PySide``
shim in ``qt_dispatcher``). ``protocol``, ``tokens``, ``client`` and ``server`` do not
import FreeCAD, so they are usable and testable outside of it.
"""

__version__ = "0.3.0"
