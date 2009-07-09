
import sys, os

pypy_path = os.path.join(os.path.split(__file__)[0], '..', '..',
                         'third_party', 'generic', 'pypy')
webkit_bridge_path = os.path.join(os.path.split(__file__)[0], '..', '..',
                                  'source', 'client')
sys.path.insert(0, pypy_path)
sys.path.insert(0, webkit_bridge_path)
