"""Utility tools to render structured content in SVN as HTML articles."""

import shelve
import sys

from commands import getoutput
from datetime import datetime
from fnmatch import fnmatch, filter
from os import getcwd, listdir, sep as SEP, stat, environ, walk
from os.path import abspath, basename, dirname, join as join_path, isfile, isdir
from os.path import split as split_path, splitext, isabs
from optparse import OptionParser
from pickle import load as load_pickle, dump as dump_pickle
from re import compile
from time import time

from genshi.template import MarkupTemplate, TemplateLoader
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer

from ..service.rst import render_rst

# ------------------------------------------------------------------------------
# some konstants
# ------------------------------------------------------------------------------

LINE = '-' * 78
HOME = getcwd()

MORE_LINE = '\n.. more\n'
SEPARATORS = ('-', ':')

SVN_INFO = "svn info -R %s" # -R HEAD
SVN_CACHE = {}

AUTHORS_CACHE = {}
TRACKER_CACHE = {}

SYNTAX_FORMATTER = HtmlFormatter(cssclass='syntax', lineseparator='<br/>')

INDEX_FILES = (
    ('index.html', 2, 'xhtml'),
    ('feed.rss', 0, 'xml'),
    ('archive.html', 1, 'xhtml'),
    )

# ------------------------------------------------------------------------------
# utility funktion
# ------------------------------------------------------------------------------

match_non_whitespace_regex = compile(r'\S').match
docstring_regex = compile(r'[r]?"""[^"\\]*(?:(?:\\.|"(?!""))[^"\\]*)*"""')

def strip_leading_indent(text):
    """
    Strip common leading indentation from a piece of ``text``.

      >>> indented_text = \"""
      ...
      ...     first indented line
      ...     second indented line
      ...
      ...     \"""

      >>> print strip_leading_indent(indented_text)
      first indented line
      second indented line

    """

    lines = text.split('\n')

    if len(lines) == 1:
        return lines[0].lstrip()

    last_line = lines.pop()

    if match_non_whitespace_regex(last_line):
        raise ValueError("Last line contains non-whitespace!")

    indent = len(last_line)
    return '\n'.join(line[indent:] for line in lines).strip()

def get_svn_info(path, pattern):
    """Return a dict of subversion info for the given path."""

    if (path, pattern) in SVN_CACHE:
        return SVN_CACHE[(path, pattern)]

    environ['TZ'] = 'UTC'
    
    svn_info = getoutput(SVN_INFO % path)
    info = {}
    item = None

    for line in svn_info.splitlines():
        if not line:
            continue
        key, value = line.split(': ', 1)
        if key == 'Path':
            if item:
                item['__svn__'] = 1
                info[item_path] = item
            item = {'__path__': value}
            item_path = value
        elif item:
            if key == 'URL':
                item['__url__'] = value.replace('https://', 'http://', 1)
            elif key == 'Node Kind' and value == 'directory':
                item = None
            elif key == 'Last Changed Author':
                item['__by__'] = value
            elif key == 'Last Changed Date':
                date, time, tz = value.split()[:3]
                if tz != '+0000':
                    raise ValueError(
                        "Got a non-UTC timezone from svn info: %r" % tz
                        )
                item['__updated__'] = datetime(*[
                    int(j) for i, segment in enumerate((date, time))
                    for j in segment.split(SEPARATORS[i])
                    ])

    items = info.items()
    info = {}

    for item_path, item in items:
        if pattern:
            if not fnmatch(item_path, pattern):
                continue
        if '__updated__' not in item:
            item['__updated__'] = datetime.utcfromtimestamp(
                stat(item_path).st_mtime
                )
        info[item_path] = item

    return SVN_CACHE.setdefault((path, pattern), info)

def parse_authors_file(file):
    if file in AUTHORS_CACHE:
        return AUTHORS_CACHE[file]
    authors_file = open(file, 'rb')
    author = False
    authors = {}
    for line in authors_file.readlines():
        if line.startswith('*'):
            if author:
                authors[author] = info
            author = line.replace('*', '').strip()
            info = []
        elif line.startswith('.. '):
            break
        elif author:
            line = line.strip()
            if not line:
                continue
            line = line.split('* ', 1)[1]
            if line[0] == '\\':
                line = line[1:]
            if '(' in line:
                line = line.split('(')[0]
            info.append(line)
    if author:
        authors[author] = info
    return AUTHORS_CACHE.setdefault(file, authors)

def parse_tracker_file(filename):

    if filename in TRACKER_CACHE:
        return TRACKER_CACHE[filename]

    info = {
        '__type__': 'tracker',
        '__updated__': datetime.utcfromtimestamp(stat(filename).st_mtime),
        '__name__': 'tracker',
        'title': 'Life Tracker',
        'subtitle': 'Foo Bar',
        }

    tracker_file = open(filename, 'rb')
    tracker_data = tracker_file.read()
    tracker_file.close()

    return {}
    return TRACKER_CACHE.setdefault(filename, info)

def blog(args): # @/@ needs to bekome standalone
    title = u' '.join(args)
    filename = '-'.join(''.join(
        (c.lower() for c in title if (c.isalnum() or c.isspace()))
        ).split())
    filename = join_path(output_path, filename + '.txt')
    if isfile(filename):
        raise IOError("%r already exists!" % filename)
    title_length = len(title)
    if verbose:
        print "Creating:", filename
    article = open(filename, 'wb')
    article.write('=' * title_length)
    article.write('\n')
    article.write(title)
    article.write('\n')
    article.write('=' * title_length)
    article.write('\n\n:X-Created: [%s]\n\n' % datetime.utcnow().strftime('%Y-%m-%d, %H:%M'))
    article.close()
    return filename

# thanks http://code.activestate.com/recipes/208993/

def get_relative_path(path1, path2):
    """Return the relative path between two paths."""
    common, segment1, segment2 = get_common_path(
        path1.split(SEP), path2.split(SEP), []
        )
    elements = []
    if segment1:
        elements.append('../' * (len(segment1) - 1))
    elements.extend(segment2)
    return join_path(*elements)

def get_common_path(segment1, segment2, common):
    if len(segment1) < 1 or len(segment2) < 1:
        return (common, segment1, segment2)
    if segment1[0] != segment2[0]:
        return (common, segment1, segment2)
    return commonpath(segment1[1:], segment2[1:], common+[segment1[0]])

# ------------------------------------------------------------------------------
# our main skript funktion
# ------------------------------------------------------------------------------

def main(argv, genfiles=None):

    op = OptionParser()

    op.add_option('-a', dest='authors', default='',
                  help="Set the path for a special authors file (optional)")

    op.add_option('-c', dest='package', default='',
                  help="Generate documentation for the Python package (optional)")

    op.add_option('-d', dest='data_file', default='',
                  help="Set the path for a persistent data file (optional)")

    op.add_option('-e', dest='output_encoding', default='utf-8',
                  help="Set the output encoding (default: utf-8)")

    op.add_option('-f', dest='format', default='html',
                  help="Set the output format (default: html)")

    op.add_option('-i', dest='input_encoding', default='utf-8',
                  help="Set the input encoding (default: utf-8)")

    op.add_option('-o', dest='output_path', default=HOME,
                  help="Set the output directory for files (default: $PWD)")

    op.add_option('-p', dest='pattern', default='',
                  help="Generate index files for the path pattern (optional)")

    op.add_option('-r', dest='root_path', default='',
                  help="Set the path to the root working directory (optional)")

    op.add_option('-t', dest='template', default='',
                  help="Set the path to a template file (optional)")

    op.add_option('--quiet', dest='quiet', default=False, action='store_true',
                  help="Flag to suppress output")

    op.add_option('--stdout', dest='stdout', default=False, action='store_true',
                  help="Flag to redirect to stdout instead of to a file")

    try:
        options, args = op.parse_args(argv)
    except SystemExit:
        return

    authors = options.authors

    if authors:
        if not isfile(authors):
            raise IOError("%r is not a valid path!" % authors)
        authors = parse_authors_file(authors)
    else:
        authors = {}

    output_path = options.output_path.rstrip('/')

    if not isdir(output_path):
        raise IOError("%r is not a valid directory!" % output_path)

    root_path = options.root_path

    siteinfo = join_path(output_path, '.siteinfo')
    if isfile(siteinfo):
        env = {}
        execfile(siteinfo, env)
        siteinfo = env['INFO']
    else:
        siteinfo = {
            'site_url': '',
            'site_nick': '',
            'site_description': '',
            'site_title': ''
            }

    stdout = sys.stdout if options.stdout else None
    verbose = False if stdout else (not options.quiet)

    format = options.format

    if format not in ('html', 'tex'):
        raise ValueError("Unknown format: %s" % format)

    if (format == 'tex') or (not options.template):
        template = False
    elif not isfile(options.template):
        raise IOError("%r is not a valid template!" % options.template)
    else:
        template_path = abspath(options.template)
        template_root = dirname(template_path)
        template_loader = TemplateLoader([template_root])
        template_file = open(template_path, 'rb')
        template = MarkupTemplate(
            template_file.read(), loader=template_loader, encoding='utf-8'
            )
        template_file.close()

    data_file = options.data_file

    if data_file:
        if isfile(data_file):
            data_file_obj = open(data_file, 'rb')
            data_dict = load_pickle(data_file_obj)
            data_file_obj.close()
        else:
            data_dict = {}

    input_encoding = options.input_encoding
    output_encoding = options.output_encoding

    if genfiles:

        files = genfiles

    elif options.package:

        package_root = options.package
        files = []
        add_file = files.append
        package = None
        for part in reversed(package_root.split(SEP)):
            if part:
                package = part
                break
        if package is None:
            raise ValueError("Couldn't find the package name from %r" % package_root)

        for dirpath, dirnames, filenames in walk(package_root):
            for filename in filenames:

                if not filename.endswith('.py'):
                    continue

                filename = join_path(dirpath, filename)
                module = package + filename[len(package_root):]
                if module.endswith('__init__.py'):
                    module = module[:-12]
                else:
                    module = module[:-3]

                module = '.'.join(module.split(SEP))
                module_file = open(filename, 'rb')
                module_source = module_file.read()
                module_file.close()

                docstring = docstring_regex.search(module_source)

                if docstring:
                    docstring = docstring.group(0)
                    if docstring.startswith('r'):
                        docstring = docstring[4:-3]
                    else:
                        docstring = docstring[3:-3]

                if docstring and docstring.strip().startswith('=='):
                    docstring = strip_leading_indent(docstring)
                    module_source = docstring_regex.sub('', module_source, 1)
                else:
                    docstring = ''

                info = {}

                if root_path and isabs(filename) and filename.startswith(root_path):
                    info['__path__'] = filename[len(root_path)+1:]
                else:
                    info['__path__'] = filename

                info['__updated__'] = datetime.utcfromtimestamp(
                    stat(filename).st_mtime
                    )

                info['__outdir__'] = output_path
                info['__name__'] = 'package.' + module
                info['__type__'] = 'py'
                info['__title__'] = module
                info['__source__'] = highlight(module_source, PythonLexer(), SYNTAX_FORMATTER)
                add_file((docstring, '', info))

    else:

        files = []
        add_file = files.append

        for filename in args:

            if not isfile(filename):
                raise IOError("%r doesn't seem to be a valid file!" % filename)

            if root_path and isabs(filename) and filename.startswith(root_path):
                path = filename[len(root_path)+1:]
            else:
                path = filename

            try:
                info = get_svn_info(path.split(SEP)[0], '*.txt')[path]
            except KeyError:
                info = {}
                info['__path__'] = path
                info['__url__'] = ''
                info['__updated__'] = datetime.utcfromtimestamp(
                    stat(filename).st_mtime
                    )

            source_file = open(filename, 'rb')
            source = source_file.read()
            source_file.close()

            if MORE_LINE in source:
                source_lead = source.split(MORE_LINE)[0]
                source = source.replace(MORE_LINE, '')
            else:
                source_lead = ''

            filebase, filetype = splitext(basename(filename))
            info['__outdir__'] = output_path
            info['__name__'] = filebase.lower()
            info['__type__'] = 'txt'
            info['__title__'] = filebase.replace('-', ' ')
            add_file((source, source_lead, info))

    for source, source_lead, info in files:

        if verbose:
            print
            print LINE
            print 'Converting: [%s] %s in [%s]' % (
                info['__type__'], info['__path__'], split_path(output_path)[1]
                )
            print LINE
            print

        if template:
            output, props = render_rst(
                source, format, input_encoding, True
                )
            # output = output.encode(output_encoding)
            info['__text__'] = output.encode(output_encoding)
            info.update(props)
            if source_lead:
                info['__lead__'] = render_rst(
                    source_lead, format, input_encoding, True
                    )[0].encode(output_encoding)
            output = template.generate(
                content=output,
                info=info,
                authors=authors,
                **siteinfo
                ).render('xhtml', encoding=output_encoding)
        else:
            output, props = render_rst(
                source, format, input_encoding, True, as_whole=True
                )
            info.update(props)
            output = output.encode(output_encoding)
            info['__text__'] = output
            if source_lead:
                info['__lead__'] = render_rst(
                    source_lead, format, input_encoding, True, as_whole=True
                    )[0].encode(output_encoding)

        if data_file:
            data_dict[info['__path__']] = info

        if stdout:
            print output
        else:
            output_filename = join_path(
                output_path, '%s.%s' % (info['__name__'], format)
                )
            output_file = open(output_filename, 'wb')
            output_file.write(output)
            output_file.close()
            if verbose:
                print 'Done!'

    if data_file:
        data_file_obj = open(data_file, 'wb')
        dump_pickle(data_dict, data_file_obj)
        data_file_obj.close()

    if options.pattern:

        pattern = options.pattern

        items = [
            item
            for item in data_dict.itervalues()
            if item['__outdir__'] == pattern
            ]

        # index.js/json

        import json

        index_js_template = join_path(output_path, 'index.js.template')

        if isfile(index_js_template):

            index_json = json.dumps([
                [_art['__name__'], _art['title'].encode('utf-8')]
                for _art in sorted(
                    [item for item in items if item.get('x-created') and
                     item.get('x-type', 'blog') == 'blog'],
                    key=lambda i: i['x-created']
                    )
                ])

            index_js_template = open(index_js_template, 'rb').read()
            index_js = open(join_path(output_path, 'index.js'), 'wb')
            index_js.write(index_js_template % index_json)
            index_js.close()

        for name, mode, format in INDEX_FILES:

            pname = name.split('.', 1)[0]
            template_file = None

            if siteinfo['site_nick']:
                template_path = join_path(
                    template_root, '%s.%s.genshi' % (pname, siteinfo['site_nick'])
                    )
                if isfile(template_path):
                    template_file = open(template_path, 'rb')

            if not template_file:
                template_path = join_path(template_root, '%s.genshi' % pname)

            template_file = open(template_path, 'rb')
            page_template = MarkupTemplate(
                template_file.read(), loader=template_loader, encoding='utf-8'
                )
            template_file.close()

            poutput = page_template.generate(
                items=items[:],
                authors=authors,
                root_path=output_path,
                **siteinfo
                ).render(format)

            poutput = unicode(poutput, output_encoding)

            if mode:
                output = template.generate(
                    alternative_content=poutput,
                    authors=authors,
                    **siteinfo
                    ).render(format)
            else:
                output = poutput

            # @/@ wtf is this needed???
            if isinstance(output, unicode):
                output = output.encode(output_encoding)

            output_file = open(join_path(output_path, name), 'wb')
            output_file.write(output)
            output_file.close()

# ------------------------------------------------------------------------------
# run farmer!
# ------------------------------------------------------------------------------

if __name__ == '__main__':
    main(sys.argv[1:])
