#include <Python.h>
#include <frameobject.h>

PyObject * get_frame_locals() {
    PyFrameObject *frame = PyThreadState_GET()->frame;
    PyFrame_FastToLocals(frame);
    return frame->f_locals;
}
