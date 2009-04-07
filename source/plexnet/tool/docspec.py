"""
DocSpec -- Integrated documentation, specification, ticketing and testing.

--------------------------------------------------------------------------------
\ Example Usage
--------------------------------------------------------------------------------

You can create a new docspec using:

   $ docspec new

Running this will generate a new docspec file and open it using $EDITOR. You can
optionally specify a title for the new docspec:

   $ docspec new "A Descriptive Title"

You can also pass in an optional parameter -t of comma separated tags for the
new docspec:

   $ docspec new "A Descriptive Title" -t "backend, priority:high"

Docspecs are created in a docspec container directory, which is specified using
the -d parameter which can be supplied to all docspec commands:

   $ docspec new -d /path/to/some/project/docspec/

If no directory has been specified, it defaults to:

   $PLEXNET_ROOT/documentation/docspec/

Docspecs have a docspecid auto-generated for them, e.g. 1cd980243f

You can find text files in the container directory which match the docspecid,
e.g. 1cd980243f.txt

Once created, any actual state change of a docspec will have to be done by
manually editing these docspec files.

To help you find available docspec files, there is a listing command:

   $ docspec list

You can even supply additional parameters to the list command which will filter
the listing based on matching docspec tags, e.g.

   $ docspec list state:open

You can pass multiple filters separated by shell spacing, e.g.

   $ docspec list state:closed @tav

You can also use shell-like pattern matching syntax for filters, but will have
to quote the parameter to avoid your shell expanding it for you, e.g.

   $ docspec list "*gui*" state:review

And finally, you can generate an .html website similar to the yatiblog
framework, by running:

   $ docspec website /path/to/website/directory

If no you run docspec website without specifying a directory, it will default
to:

   $PLEXNET_ROOT/documentation/website/

And, of course, if you ever want to display this help message again:

   $ docspec help

--------------------------------------------------------------------------------
\ Tag Syntax
--------------------------------------------------------------------------------

Tags are at the heart of docspec. They provide much of the rich functionality.

They are either defined using the -t parameter when a new docspec is created or
with the 'X-Tags' field inside the docspec file. Besides commas, you can use
whatever characters you like inside a tag. The commas are used to delimit tags
from each other. And in addition any leading or trailing whitespace is stripped.

Example tags include:

   feature, backend, networking, crypto

You can tag a docspec with users using an @username tag, e.g.

   @tav, @Killarny, @sbp, @thruflo

And finally, 3 special typed tags are given special treatment in the default web
interface.

You can specify the "state" of a docspec. The recommended states are:

   state:new, state:dev, state:review, state:closed, state:invalid

You can specify the "priority" of a docspec. The recommended levels are:

  priority:low, priority:normal, priority:high

And finally you can specify what other docspecids this particular docspec is
dependent on. This is done with the "requires" type, e.g.

  requires:1cd97d6d84, requires:2ea31ae59f

"""

import plexnetenv
import sys

from os import listdir
from os.path import isdir, join as join_path
from time import time

# ------------------------------------------------------------------------------
# some konstants
# ------------------------------------------------------------------------------

DOCSPEC_TEMPLATE = """
:X-Depends:
:X-Tags:

  state:open, priority:low, untagged

"""

# ------------------------------------------------------------------------------
# utility funktions
# ------------------------------------------------------------------------------

def create_docspec_id():
    return hex(int(time()*100))[2:-1]

def create_docspec(title):

    title_length = len(title)
    header = "%s\n%s\n%s\n" % ('=' * title_length, title, '=' * title_length)
    docspec_content = header + DOCSPEC_TEMPLATE

    print docspec_content

def help():
    print __doc__
    sys.exit()

# ------------------------------------------------------------------------------
# main runner
# ------------------------------------------------------------------------------

def runner(argv=None):

    argv = argv or sys.argv[1:]

    if not argv or argv == ['--help'] or argv == ['-h']:
        help()

    command, argv = argv[0], argv[1:]

    docspec_directory = join_path(plexnetenv.PLEXNET_ROOT, 'documentation', 'docspec')

    try:
        docspec_directory = argv[argv.index('-d') + 1]
    except Exception:
        pass

    if not isdir(docspec_directory):
        print "!! Invalid docspec directory: %r !!" % docspec_directory
        sys.exit(1)

    if command == 'new':
        print
        # create_docspec()
        print create_docspec_id()

    elif command == 'list':
        print listdir(docspec_directory)

    elif command == 'help':
        help()

    elif command == 'website':
        pass

    else:
        print "!! Unknown docspec command !!"
