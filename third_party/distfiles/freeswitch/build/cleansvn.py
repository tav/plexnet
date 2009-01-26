import os
import shutil

from commands import getoutput
from os.path import join as join_path

cur_dir = os.getcwd()

for dirpath, dirnames, filenames in os.walk('.'):

    if '.svn' in dirpath:
        continue

    if '.svn' not in dirnames:
        print "Removing:", dirpath
        # shutil.rmtree(dirpath)

#     for file in filenames:
#         nfile = join_path(dirpath, file)
#         out = getoutput('svn info %s' % nfile)
#         if 'Not a versioned resource' in out:
#             print "Removing:", nfile
#             os.remove(nfile)
