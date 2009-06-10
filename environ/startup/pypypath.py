
import sys, os

pypy_path = os.path.join(os.path.split(__file__)[0], '..', '..',
                         'third_party', 'generic', 'pypy')
sys.path.insert(0, pypy_path)
