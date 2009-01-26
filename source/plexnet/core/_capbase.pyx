# ------------------------------------------------------------------------------
# externs
# ------------------------------------------------------------------------------

cdef extern from "Python.h":

    ctypedef void PyObject
    ctypedef struct PyTypeObject

    int PyObject_TypeCheck(object, PyTypeObject*)

    bint PyFunction_Check(object o)

    int PyDict_Contains(object p, object key)
    int PyDict_DelItem(object p, object key)
    object PyDict_Keys(object p)
    PyObject* PyDict_GetItem(object p, object key)
    object PyDict_Items(object p)
    int PyDict_SetItem(object p, object key, object val)
    int PyDict_SetItemString(object p, char *key, object val)
    PyObject* PyDictProxy_New(object dict)

    object PyWeakref_NewRef(object ob, object callback)

    int PyList_Append(object list, object item)
    object PyList_AsTuple(object list)
    object PyList_GET_ITEM(object list, Py_ssize_t i)
    int PyList_Insert(object list, Py_ssize_t index, object item)
    PyObject* PyList_New(Py_ssize_t len)
    void PyList_SET_ITEM(PyObject *list, Py_ssize_t i, object o)
    int PyList_Sort(object list)

    int PyUnicode_Tailmatch(object str, object substr, Py_ssize_t start, Py_ssize_t end, int direction)


cdef extern from "support.h":
    object get_frame_locals()

cdef inline bint typecheck(object ob, object tp):
    return PyObject_TypeCheck(ob, <PyTypeObject*>tp)

# ------------------------------------------------------------------------------
# some globals
# ------------------------------------------------------------------------------

cdef dict _key2id_store, _id2key_store
cdef int _last_id

_keys2id_store = {}
_id2keys_store = {}

_last_id = 1 # long

# ------------------------------------------------------------------------------
# kapability sekure object type
# ------------------------------------------------------------------------------

cdef class Namespace:
    """A Namespace object."""

    cdef object __weakref__
    cdef list env
    cdef int id

    def __cinit__(Namespace self, **env):

        cdef object key, name
        cdef list keys_list, id_data
        cdef tuple keys_tuple
        cdef int id

        if env:
            keys_list = PyDict_Keys(env)
        else:
            env = get_frame_locals()
            keys_list = [
                name for name in PyDict_Keys(env)
                if not (name.startswith('_') and (not name.startswith('__')))
                ]

        # PyList_Sort(_keys)
        keys_tuple = PyList_AsTuple(keys_list)

        if PyDict_Contains(_keys2id_store, keys_tuple):
            id_data = <object>PyDict_GetItem(_keys2id_store, keys_tuple)
            id = PyList_GET_ITEM(id_data, 0)
            PyList_Append(id_data, PyWeakref_NewRef(self, None))
        else:
            global _last_id
            id = _last_id
            _last_id = id + 1
            _keys2id_store[keys_tuple] = [id, PyWeakref_NewRef(self, None)]
            _id2keys_store[id] = keys_tuple

        self.id = id
        self.env = [env[key] for key in keys_tuple]

    def __getattribute__(Namespace self, attribute):

        cdef int i
        cdef object key

        i = 0

        for key in _id2keys_store[self.id]:
            if key == attribute:
                return self.env[i]
            i = i + 1

        raise AttributeError("'Namespace' object has no attribute %r" % attribute)

    def __dir__(Namespace self):
        return list(_id2keys_store[self.id])

    def __str__(Namespace self):
        return getattr(self, ('__str__'))()
 
    def __repr__(Namespace self):
        return getattr(self, ('__repr__'))()

cdef _prune_stores():

    cdef list remlist, surv
    cdef int id

    remlist = []

    for keys in _keys2id_store:
        surv = []
        id = 0
        for item in keys:
            if id == 0:
                id = item
            else:
                if item():
                    PyList_Append(surv, item)
        if surv:
            PyList_Insert(surv, 0, id)
            PyDict_SetItem(_keys2id_store, keys, surv)
        else:
            PyList_Append(remlist, (keys, id))
    if remlist:
        for key, id in remlist:
            PyDict_DelItem(_keys2id_store, keys)
            PyDict_DelItem(_id2keys_store, id)

def prune_stores():
    _prune_stores()

def get_store():
    return (_id2keys_store, _keys2id_store)
