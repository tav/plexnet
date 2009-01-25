"""Patch functions in the Python 2.5 Standard Library."""

import dis as dismodule
import inspect
import linecache
import re
import sys
import types

from types import FunctionType

def dis(x=None):
    """
    Disassemble classes, methods, functions, or code.

    With no argument, disassemble the last traceback.
    """

    if x is None:
        dismodule.distb()
        return
    if type(x) is types.InstanceType:
        x = x.__class__
    if hasattr(x, 'im_func'):
        x = x.im_func
    if isinstance(x, types.FunctionType):
        x = sys.get_func_code(x)
    if hasattr(x, '__dict__'):
        items = x.__dict__.items()
        items.sort()
        for name, x1 in items:
            if type(x1) in (types.MethodType,
                            types.FunctionType,
                            types.CodeType,
                            types.ClassType):
                print "Disassembly of %s:" % name
                try:
                    dis(x1)
                except TypeError, msg:
                    print "Sorry:", msg
                print
    elif hasattr(x, 'co_code'):
        dismodule.disassemble(x)
    elif isinstance(x, str):
        dismodule.disassemble_string(x)
    else:
        raise TypeError, \
              "don't know how to disassemble %s objects" % \
              type(x).__name__

def getargspec(func):
    """Get the names and default values of a function's arguments.

    A tuple of four things is returned: (args, varargs, varkw, defaults).
    'args' is a list of the argument names (it may contain nested lists).
    'varargs' and 'varkw' are the names of the * and ** arguments or None.
    'defaults' is an n-tuple of the default values of the last n arguments.
    """

    if inspect.ismethod(func):
        func = func.im_func
    if not inspect.isfunction(func):
        raise TypeError('arg is not a Python function')
    args, varargs, varkw = inspect.getargs(sys.get_func_code(func))
    return args, varargs, varkw, func.func_defaults

def getfile(object):
    """Work out which source or compiled file an object was defined in."""

    if inspect.ismodule(object):
        if hasattr(object, '__file__'):
            return object.__file__
        raise TypeError('arg is a built-in module')
    if inspect.isclass(object):
        object = sys.modules.get(object.__module__)
        if hasattr(object, '__file__'):
            return object.__file__
        raise TypeError('arg is a built-in class')
    if inspect.ismethod(object):
        object = object.im_func
    if inspect.isfunction(object):
        object = sys.get_func_code(object)
    if inspect.istraceback(object):
        object = object.tb_frame
    if inspect.isframe(object):
        object = object.f_code
    if inspect.iscode(object):
        return object.co_filename
    raise TypeError('arg is not a module, class, method, '
                    'function, traceback, frame, or code object')

def findsource(object):
    """Return the entire source file and starting line number for an object.

    The argument may be a module, class, method, function, traceback, frame,
    or code object.  The source code is returned as a list of all the lines
    in the file and the line number indexes a line in that list.  An IOError
    is raised if the source code cannot be retrieved."""

    file = inspect.getsourcefile(object) or inspect.getfile(object)
    module = inspect.getmodule(object, file)
    if module:
        lines = linecache.getlines(file, module.__dict__)
    else:
        lines = linecache.getlines(file)
    if not lines:
        raise IOError('could not get source code')

    if inspect.ismodule(object):
        return lines, 0

    if inspect.isclass(object):
        name = object.__name__
        pat = re.compile(r'^(\s*)class\s*' + name + r'\b')
        # make some effort to find the best matching class definition:
        # use the one with the least indentation, which is the one
        # that's most probably not inside a function definition.
        candidates = []
        for i in range(len(lines)):
            match = pat.match(lines[i])
            if match:
                # if it's at toplevel, it's already the best one
                if lines[i][0] == 'c':
                    return lines, i
                # else add whitespace to candidate list
                candidates.append((match.group(1), i))
        if candidates:
            # this will sort by whitespace, and by line number,
            # less whitespace first
            candidates.sort()
            return lines, candidates[0][1]
        else:
            raise IOError('could not find class definition')

    if inspect.ismethod(object):
        object = object.im_func
    if inspect.isfunction(object):
        object = sys.get_func_code(object)
    if inspect.istraceback(object):
        object = object.tb_frame
    if inspect.isframe(object):
        object = object.f_code
    if inspect.iscode(object):
        if not hasattr(object, 'co_firstlineno'):
            raise IOError('could not find function definition')
        lnum = object.co_firstlineno - 1
        pat = re.compile(r'^(\s*def\s)|(.*(?<!\w)lambda(:|\s))|^(\s*@)')
        while lnum > 0:
            if pat.match(lines[lnum]): break
            lnum = lnum - 1
        return lines, lnum
    raise IOError('could not find code object')

# ------------------------------------------------------------------------------
# patch the standard library
# ------------------------------------------------------------------------------

dismodule.dis = dis
inspect.findsource = findsource
inspect.getargspec = getargspec
inspect.getfile = getfile
