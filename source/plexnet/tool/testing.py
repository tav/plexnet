"""Plexnet Testing Framework."""

import sys
import traceback

from ..util.doctest import testfile, testmod, ELLIPSIS
from ..util.io import DEVNULL
from ..util.io import print_message as heading, print_note as note
from ..util.io import print_text as text

# ------------------------------------------------------------------------------
# some konstants
# ------------------------------------------------------------------------------

PASSED = 'PASSED'
FAILED = "------ FAILED"
IMPORT_ERROR = "------ IMPORT ERROR"

# ------------------------------------------------------------------------------
# modules to be tested
# ------------------------------------------------------------------------------

DEFAULT_TEST_MODULES = (

    'util.secure',
    'util.modulesetup',
    '#SECURE_PYTHON',
    'util.optimise',
    'core.builtins',

    'core.capbase',
    'core.networking',
    'core.psf',
    'core.py2js',

    'service.facebook',
    'service.rst',
    'service.worldbank',

    'util.dict',
    'util.doctest',
    'util.io',
    'util.pytype',
    'util.urischeme',

    )

# ------------------------------------------------------------------------------
# handlers
# ------------------------------------------------------------------------------

handlers = {}
register_handler = handlers.__setitem__

def secure_python():
    from ..util.secure import secure_python
    secure_python()

register_handler('#SECURE_PYTHON', secure_python)

# ------------------------------------------------------------------------------
# a basik test framework ;p
# ------------------------------------------------------------------------------

def run_tests(argv=None, verbose=False, package='plexnet', handlers=handlers):
    """
    Run Plexnet Tests.

    Usage:

      %s [<list-of-modules>] [<options>] [--package <package-name>]

      The available options are:

        -v             Enable verbose output
        --summary      Print just the final summary
        --no-colour    Disable colour output
        --no-package   Specify an empty package
        --no-suppress  Don't suppress module output on import

    The default package of 'plexnet' is assumed.
    """

    argv = argv or sys.argv[1:]

    if ('--help' in argv) or ('-h' in argv):
        print run_tests.__doc__ % sys.argv[0]
        sys.exit()

    while '-v' in argv:
        verbose = True
        argv.remove('-v')

    ori_stdout = sys.stdout

    while '--summary' in argv:
        sys.stdout = DEVNULL
        argv.remove('--summary')

    if '--package' in argv:
        pos = argv.index('--package')
        del argv[pos]
        package = argv[pos]
        del argv[pos]

    while '--no-package' in argv:
        package = ''
        argv.remove('--no-package')

    suppress = True

    while '--no-suppress' in argv:
        suppress = False
        argv.remove('--no-suppress')

    global heading, note, text
    _heading, _note, _text = heading, note, text

    while '--no-colour' in argv:
        heading = lambda text, *arg, **kw: _heading(text, 80, 0, 'null', 'null')
        note = lambda text, *arg, **kw: _note(text, 'null', 'null')
        text = lambda colour, text: text
        argv.remove('--no-colour')

    if not argv:
        argv = DEFAULT_TEST_MODULES

    test_data = []; out = test_data.append

    for module in argv:
        if module in handlers:
            handlers[module]()
        else:
            out(test_module(module, verbose, package, suppress))

    print_test_summary(test_data, ori_stdout)

def test_module(module_name, verbosity=None, package='', suppress=False):
    """Test the given module, print failure output and return some state info."""

    if package:
        module_name = '%s.%s' % (package, module_name)

    if module_name.endswith('.'):
        module_name = module_name[:-1]

    print heading('Testing: ' + module_name)

    stdout = sys.stdout

    try:
        if suppress:
            sys.stdout = sys.stderr = DEVNULL
        module = __import__(module_name, globals(), locals(), [module_name])
        sys.stdout = stdout
        failures, tries = testmod(
            module, verbose=verbosity, optionflags=ELLIPSIS
            )
    except Exception as reason:
        sys.stdout = stdout
        sys.stderr = sys.__stderr__
        print
        print text('yellow', "* <%s>" % reason.__class__.__name__)
        print text('yellow', "  %s" % str(reason))
        print
        traceback.print_exception(*sys.exc_info())
        return module_name, 0, 0, IMPORT_ERROR

    if failures:
        print
        print text(
            'yellow',
            "FAILED %d of %d tests in %r" % (failures, tries, module_name)
            )
        print
        return module_name, failures, tries, FAILED

    print note("PASSED %d tests" % tries)
    return module_name, failures, tries, PASSED

# ------------------------------------------------------------------------------
# pretty print a summary
# ------------------------------------------------------------------------------

_marker = object()

def print_test_summary(results, stream):

    sys.stdout = stream

    print heading('Doctest Summary')
    print

    _last = _marker
    _total = _count = 0

    for name, failures, tries, status in results:

        _total += tries
        _split = name.rsplit('.', 1)

        if len(_split) == 2:
            package, module = _split
        else:
            package = ''
            module = _split[0]

        if _last is _marker or package != _last:
            print
            _count += 1
            _count_str = _count
            _package_str = package
        elif package == _last:
            _count_str = ''
            _package_str = ''

        _last = package

        if status == PASSED:
            failures = of = '  '
        elif status == IMPORT_ERROR:
            failures = of = tries = '  '
        else:
            of = 'of'

        print "%2s %s %21s %3s %2s %3s   %s" % (
            _count_str, _package_str.ljust(20), module, failures, of, tries, status
            )

    print
    print "%56s   TOTAL" % _total
    print

