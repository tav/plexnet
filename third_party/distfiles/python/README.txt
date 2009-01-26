`Python <http://www.python.org/>`_ is a high-level interpreted language.

To update the sources:

* Get the latest source from http://www.python.org

* Remove the following directories:

  - Demo
  - Doc
  - Mac/IDLE (except for Makefile.in)
  - Mac/PythonLauncher (except for Makefile.in)
  - Misc (except for python.man and python-config.in)
  - Tool (except for the scripts sub-directory)

* Apply ``patch.Makefile.pre.in`` which skips the installation of utility
  Applications on OS X.

* Apply ``patch.Lib.site.py`` which adds support for the plexnetenv setup.

* Follow the usual procedure.