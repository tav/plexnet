import sys, os, signal, thread, Queue, time
import py
from py.compat import subprocess, optparse

if sys.platform == 'win32':
    PROCESS_TERMINATE = 0x1
    try:
        import win32api, pywintypes
    except ImportError:
        def _kill(pid, sig):
            print >>sys.stderr, "no process killing support without pywin32"
    else:
        def _kill(pid, sig):
            try:
                proch = win32api.OpenProcess(PROCESS_TERMINATE, 0, pid)
                win32api.TerminateProcess(proch, 1)
                win32api.CloseHandle(proch)
            except pywintypes.error, e:
                pass

    READ_MODE = 'rU'
    WRITE_MODE = 'wb'
else:
    def _kill(pid, sig):
        try:
            os.kill(pid, sig)
        except OSError:
            pass
    READ_MODE = 'r'
    WRITE_MODE = 'w'

EXECUTEFAILED = -1001
RUNFAILED  = -1000
TIMEDOUT = -999

def run(args, cwd, out, timeout=None):
    f = out.open('w')
    try:
        try:
            p = subprocess.Popen(args, cwd=str(cwd), stdout=f, stderr=f)
        except Exception, e:
            f.write("Failed to run %s with cwd='%s' timeout=%s:\n"
                    " %s\n"
                    % (args, cwd, timeout, e))
            return RUNFAILED

        if timeout is None:
            return p.wait()
        else:
            timedout = None
            t0 = time.time()
            while True:
                returncode = p.poll()
                if returncode is not None:
                    return timedout or returncode
                tnow = time.time()
                if (tnow-t0) > timeout:
                    if timedout:
                        _kill(p.pid, signal.SIGKILL)
                        return TIMEDOUT
                    else:
                        timedout = TIMEDOUT
                        _kill(p.pid, signal.SIGTERM)
                time.sleep(min(timeout, 10))
    finally:
        f.close()

def dry_run(args, cwd, out, timeout=None):
    f = out.open('w')
    try:
        f.write("run %s with cwd='%s' timeout=%s\n" % (args, cwd, timeout))
    finally:
        f.close()
    return 0

def getsignalname(n):
    for name, value in signal.__dict__.items():
        if value == n and name.startswith('SIG'):
            return name
    return 'signal %d' % (n,)

def execute_test(cwd, test, out, logfname, interp, test_driver,
                 do_dry_run=False, timeout=None):
    args = interp+test_driver
    args += ['--resultlog=%s' % logfname, test]

    args = map(str, args)
    if do_dry_run:
        runfunc = dry_run
    else:
        runfunc = run
    
    exitcode = runfunc(args, cwd, out, timeout=timeout)
    
    return exitcode

def interpret_exitcode(exitcode, test):
    extralog = ""
    if exitcode:
        failure = True
        if exitcode != 1:
            if exitcode > 0:
                msg = "Exit code %d." % exitcode
            elif exitcode == TIMEDOUT:
                msg = "TIMEOUT"
            elif exitcode == RUNFAILED:
                msg = "Failed to run interp"
            elif exitcode == EXECUTEFAILED:
                msg = "Failed with exception in execute-test"                
            else:
                msg = "Killed by %s." % getsignalname(-exitcode)
            extralog = "! %s\n %s\n" % (test, msg)
    else:
        failure = False
    return failure, extralog

def worker(num, n, run_param, testdirs, result_queue):
    sessdir = run_param.sessdir
    root = run_param.root
    get_test_driver = run_param.get_test_driver
    interp = run_param.interp
    dry_run = run_param.dry_run
    timeout = run_param.timeout
    cleanup = run_param.cleanup
    # xxx cfg thread start
    while 1:
        try:
            test = testdirs.pop(0)
        except IndexError:
            result_queue.put(None) # done
            return
        result_queue.put(('start', test))
        basename = py.path.local(test).purebasename        
        logfname = sessdir.join("%d-%s-pytest-log" % (num, basename))
        one_output = sessdir.join("%d-%s-output" % (num, basename))
        num += n

        try:
            test_driver = get_test_driver(test)
            exitcode = execute_test(root, test, one_output, logfname,
                                    interp, test_driver, do_dry_run=dry_run,
                                    timeout=timeout)

            cleanup(test)
        except:
            print "execute-test for %r failed with:" % test
            import traceback
            traceback.print_exc()
            exitcode = EXECUTEFAILED

        if one_output.check(file=1):            
            output = one_output.read(READ_MODE)
        else:
            output = ""
        if logfname.check(file=1):
            logdata = logfname.read(READ_MODE)
        else:
            logdata = ""

        failure, extralog = interpret_exitcode(exitcode, test)

        if extralog:
            logdata += extralog

        result_queue.put(('done', test, failure, logdata, output))

invoke_in_thread = thread.start_new_thread

def start_workers(n, run_param, testdirs):
    result_queue = Queue.Queue()
    for i in range(n):
        invoke_in_thread(worker, (i, n, run_param, testdirs,
                                  result_queue))
    return result_queue


def execute_tests(run_param, testdirs, logfile, out):
    sessdir = py.path.local.make_numbered_dir(prefix='usession-testrunner-',
                                              keep=4)
    run_param.sessdir = sessdir

    run_param.startup()

    N = run_param.parallel_runs
    failure = False

    for testname in testdirs:
        out.write("-- %s\n" % testname)
    out.write("-- total: %d to run\n" % len(testdirs))

    result_queue = start_workers(N, run_param, testdirs)

    done = 0
    started = 0

    worker_done = 0
    while True:
        res = result_queue.get()
        if res is None:
            worker_done += 1
            if worker_done == N:
                break
            continue

        if res[0] == 'start':
            started += 1
            out.write("++ starting %s [%d started in total]\n" % (res[1],
                                                                  started)) 
            continue
        
        testname, somefailed, logdata, output = res[1:]
        done += 1
        failure = failure or somefailed

        heading = "__ %s [%d done in total] " % (testname, done)
        
        out.write(heading + (79-len(heading))*'_'+'\n')

        out.write(output)
        if logdata:
            logfile.write(logdata)

    run_param.shutdown()

    return failure


class RunParam(object):
    dry_run = False
    interp = [os.path.abspath(sys.executable)]
    test_driver = [os.path.abspath(os.path.join('py', 'bin', 'py.test'))]
    parallel_runs = 1
    timeout = None
    cherrypick = None
    
    def __init__(self, root):
        self.root = root
        self.self = self

    def startup(self):
        pass

    def shutdown(self):
        pass

    def get_test_driver(self, testdir):
        return self.test_driver

    def is_test_py_file(self, p):
        name = p.basename
        return name.startswith('test_') and name.endswith('.py')

    def reltoroot(self, p):
        rel = p.relto(self.root)
        return rel.replace(os.sep, '/')

    def collect_one_testdir(self, testdirs, reldir, tests):
        testdirs.append(reldir)
        return

    def collect_testdirs(self, testdirs, p=None):
        if p is None:
            p = self.root
            
        reldir = self.reltoroot(p)
        entries = [p1 for p1 in p.listdir() if p1.check(dotfile=0)]

        if p != self.root:
            for p1 in entries:
                if self.is_test_py_file(p1):
                    self.collect_one_testdir(testdirs, reldir,
                                   [self.reltoroot(t) for t in entries
                                    if self.is_test_py_file(t)])
                    return

        for p1 in entries:
            if p1.check(dir=1, link=0):
                self.collect_testdirs(testdirs, p1)

    def cleanup(self, testdir):
        pass


def main(args):
    parser = optparse.OptionParser()
    parser.add_option("--logfile", dest="logfile", default=None,
                      help="accumulated machine-readable logfile")
    parser.add_option("--output", dest="output", default='-',
                      help="plain test output (default: stdout)")
    parser.add_option("--config", dest="config", default=[],
                      action="append",
                      help="configuration python file (optional)")
    parser.add_option("--root", dest="root", default=".",
                      help="root directory for the run")
    parser.add_option("--parallel-runs", dest="parallel_runs", default=0,
                      type="int",
                      help="number of parallel test runs")
    parser.add_option("--dry-run", dest="dry_run", default=False,
                      action="store_true",
                      help="dry run"),
    parser.add_option("--timeout", dest="timeout", default=None,
                      type="int",
                      help="timeout in secs for test processes")
        
    opts, args = parser.parse_args(args)

    if opts.logfile is None:
        print "no logfile specified"
        sys.exit(2)

    logfile = open(opts.logfile, WRITE_MODE)
    if opts.output == '-':
        out = sys.stdout
    else:
        out = open(opts.output, WRITE_MODE)

    root = py.path.local(opts.root)

    testdirs = []

    run_param = RunParam(root)
    # the config files are python files whose run overrides the content
    # of the run_param instance namespace
    # in that code function overriding method should not take self
    # though a self and self.__class__ are available if needed
    for config_py_file in opts.config:
        config_py_file = os.path.expanduser(config_py_file)
        if py.path.local(config_py_file).check(file=1):
            print >>out, "using config", config_py_file
            execfile(config_py_file, run_param.__dict__)
    run_param.__dict__.pop('__builtins__', None)

    if run_param.cherrypick:
        for p in run_param.cherrypick:
            run_param.collect_testdirs(testdirs, root.join(p))
    else:
        run_param.collect_testdirs(testdirs)

    if opts.parallel_runs:
        run_param.parallel_runs = opts.parallel_runs
    if opts.timeout:
        run_param.timeout = opts.timeout
    run_param.dry_run = opts.dry_run

    if run_param.dry_run:
        print >>out, run_param.__dict__
    
    res = execute_tests(run_param, testdirs, logfile, out)

    if res:
        sys.exit(1)


if __name__ == '__main__':
    main(sys.argv)
