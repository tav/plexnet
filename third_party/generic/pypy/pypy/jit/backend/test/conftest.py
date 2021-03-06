import py, random

option = py.test.config.option

def pytest_addoption(parser):
    group = parser.addgroup('random test options')
    group.addoption('--random-seed', action="store", type="int",
                    default=random.randrange(0, 10000),
                    dest="randomseed",
                    help="choose a fixed random seed")
    group.addoption('--backend', action="store",
                    default='llgraph',
                    choices=['llgraph', 'x86'],
                    dest="backend",
                    help="select the backend to run the functions with")
    group.addoption('--block-length', action="store", type="int",
                    default=30,
                    dest="block_length",
                    help="insert up to this many operations in each test")
    group.addoption('--n-vars', action="store", type="int",
                    default=10,
                    dest="n_vars",
                    help="supply this many randomly-valued arguments to "
                         "the function")
    group.addoption('--repeat', action="store", type="int",
                    default=15,
                    dest="repeat",
                    help="run the test this many times"),
    group.addoption('--output', '-O', action="store", type="str",
                    default="", dest="output",
                    help="dump output to a file")

