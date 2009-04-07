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

If you run docspec website without specifying a directory, it will default to:

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

Certain "typed" tags are given special treatment in the default web interface.

You can tag a docspec with users using an @username tag, e.g.

   @tav, @Killarny, @sbp, @thruflo

You can specify the "state" of a docspec. The recommended states are:

   state:new, state:dev, state:review, state:closed, state:invalid

You can specify the "priority" of a docspec. The recommended levels are:

  priority:low, priority:normal, priority:high

And finally you can specify what other docspecids this particular docspec is
dependent on. This is done with the "requires" type, e.g.

  requires:1cd97d6d84, requires:2ea31ae59f

"""

import os
import subprocess
import sys

from datetime import datetime
from os import listdir
from os.path import exists, isdir, join as join_path
from textwrap import TextWrapper
from time import time

import plexnetenv

# ------------------------------------------------------------------------------
# some konstants
# ------------------------------------------------------------------------------

DOCSPEC_TEMPLATE = """%s
%s
%s

:X-Created: [%s]
:X-Tags:

    %s

"""

NOW = datetime.utcnow()

# ------------------------------------------------------------------------------
# utility klasses
# ------------------------------------------------------------------------------

class Tag(object):

    def __init__(self):
        self.people = []
        self.state = 'new'
        self.priority = 'normal'
        self.requires = []
        self.tags = []

# ------------------------------------------------------------------------------
# utility funktions
# ------------------------------------------------------------------------------

def create_docspec_id():
    return hex(int(time()*100))[2:-1]

def create_docspec(docspec_id, title, tags):

    title = title.strip()
    if not title:
        title = "Docspec %s" % docspec_id

    title_length = len(title)

    tags = tags.strip()
    if not tags:
        tags = "state:new, priority:normal, untagged"

    wrapper = TextWrapper(width=80)
    wrapper.subsequent_indent = '    '
    tags = wrapper.fill(tags)

    return DOCSPEC_TEMPLATE % (
        '=' * title_length,
        title,
        '=' * title_length,
        NOW.strftime('%Y-%m-%d, %H:%M'),
        tags
        )

def help():
    print __doc__
    sys.exit()

def parse_tag_string(tags):
    result = Tag()
    tags = filter(None, map(str.strip, tags.split(',')))
    for tag in tags:
        tag = '-'.join(tag.split()).lower()
        result.tags.append(tag)
        if tag.startswith('@'):
            result.people.append(tag[1:])
        elif tag.startswith('state:'):
            result.state = tag[6:]
        elif tag.startswith('priority:'):
            result.priority = tag[9:]
        elif tag.startswith('requires:'):
            result.requires.append(tag[9:])
    return result.__dict__

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
        dir_pos = argv.index('-d')
        del argv[dir_pos]
        docspec_directory = argv.pop(dir_pos)
    except Exception:
        pass

    if not isdir(docspec_directory):
        print "!! Invalid docspec directory: %r !!" % docspec_directory
        sys.exit(1)

    if command == 'new':

        docspec_id = create_docspec_id()
        tags = title = ''

        if '-t' in argv:
            tag_pos = argv.index('-t')
            del argv[tag_pos]
            try:
                tags = argv.pop(tag_pos)
            except IndexError:
                pass

        if argv:
            title = argv[0]

        content = create_docspec(docspec_id, title, tags)
        docspec_filename = join_path(docspec_directory, docspec_id + '.txt')

        if exists(docspec_filename):
            print "!! File %r already exists !!" % docspec_filename
            sys.exit(1)

        docspec = open(docspec_filename, 'wb')
        docspec.write(content)
        docspec.close()

        if 'EDITOR' in os.environ:
            retval = subprocess.call([os.environ['EDITOR'], docspec_filename])
            if retval:
                print "!! Couldn't open %r with $EDITOR !!" % docspec_filename
            print
            print " Docspec Id:    %s" % docspec_id
            print " Docspec File:  %s" % docspec_filename
            print

    elif command == 'list':

        # sort on created

        print
        print " +------------+--------------------+------------+--------+--------------------------------+"
        print " | Docspec ID |              Title |    Created |  State |                           Tags |"
        print " +------------+--------------------+------------+--------+--------------------------------+"
        for docspec in listdir(docspec_directory):
            tags = ['@tav', 'state:new', 'gui', 'requires:21155315131']
            print " | %10s | %18s | %s | %6s | %s |" % (
                docspec[:-4], "hOIHOIHOIHO IHO HOI HOIHOIO"[:18], '2009/02/23',
                'new'[:6], ','.join(tags)[:30]
                )
        print " +------------+--------------------+------------+--------+--------------------------------+"

    elif command == 'help':
        help()

    elif command == 'website':
        pass

    else:
        print "!! Unknown docspec command !!"
