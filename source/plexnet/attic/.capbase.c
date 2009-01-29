#include <Python.h>
#include <structmember.h>
#include <frameobject.h>

typedef struct {
    PyObject_HEAD
    long id;
    PyObject *env;
    PyObject *__weakref__;
} CapObject;

static long _id_counter = 1;
static PyObject *_key2id_store = 0;
static PyObject *_id2key_store = 0;

static char single_underscore[] = "_";
static char double_underscore[] = "__";

static PyObject *
CapObject_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {

    if (kwds == NULL) {
        // PyThreadState *tstate = PyEval_SaveThread();
        PyFrameObject *frame = PyThreadState_GET()->frame;
        PyFrame_FastToLocals(frame);
        kwds = frame->f_locals;
        // PyFrame_LocalsToFast(frame, 0);
        // PyEval_RestoreThread(tstate);
    }

    PyDictObject *environ = (PyDictObject *)kwds;

    PyObject *env, *keys;
    Py_ssize_t i, size;

    Py_ssize_t mask, key_len;
    PyObject *key, *value;
    PyDictEntry *entries;
	const char* key_str;

    /* Preallocate the list of tuples, to avoid allocations during
     * the loop over the items, which could trigger GC, which
     * could resize the dict. :-(
     */

    again:

    size = environ->ma_used;

    keys = PyList_New(0);
    if (keys == NULL)
        return NULL;

    env = PyList_New(0);
    if (env == NULL)
        return NULL;

    if (size != environ->ma_used) {
        /* Durnit.  The allocations caused the dict to resize.
         * Just start over, this shouldn't normally happen.
         */
        Py_DECREF(keys);
        Py_DECREF(env);
        goto again;
    }

    entries = environ->ma_table;
    mask = environ->ma_mask;

    for (i = 0; i <= mask; i++) {
        if ((value=entries[i].me_value) != NULL) {
            key = entries[i].me_key;
            if (!PyString_CheckExact(key)) {
                Py_DECREF(keys);
                Py_DECREF(env);
                PyErr_SetString(PyExc_ValueError, "Only string keys can be used in Objects.");
                return NULL;
            }
            key_len = PyString_GET_SIZE(key);
            if (!key_len)
                continue;
            key_str = PyString_AS_STRING(key);
            if (!memcmp(key_str, single_underscore, 1)) {
                if (key_len == 1 || (memcmp(key_str, double_underscore, 2)))
                    continue;
            }
            Py_INCREF(key);
            PyList_Append(keys, key);
            Py_INCREF(value);
            PyList_Append(env, value);
       }
    }

    /* We could save more memory by sorting the keys. */

    PyObject *keys_tuple;
    PyObject **p, **q;

    size = Py_SIZE(keys);
    keys_tuple = PyTuple_New(size);
    if (keys_tuple == NULL)
        return NULL;

    p = ((PyTupleObject *)keys_tuple)->ob_item;
    q = ((PyListObject *)keys)->ob_item;

    while (--size >= 0) {
        Py_INCREF(*q);
        *p = *q;
        p++;
        q++;
    }

    long hash;
    long id;

    hash = PyObject_Hash(keys_tuple);
    if (hash == -1) {
        PyErr_SetString(PyExc_ValueError, "Cannot hash the environ keys.");
        return NULL;
    }

    environ = (PyDictObject *)_key2id_store;
    entries = (environ->ma_lookup)(environ, keys_tuple, hash);

    if ((entries == NULL) || (entries->me_value == NULL)) {
        id = _id_counter;
        _id_counter++;
        value = PyLong_FromLong(id);
        if (value == NULL)
            return NULL;
        PyDict_SetItem(_key2id_store, keys_tuple, value);
        PyDict_SetItem(_id2key_store, value, keys_tuple);
    } else {
        id = PyLong_AsLong(entries->me_value);
        if (id == -1)
            return NULL;
    }

    CapObject *self;

    self = (CapObject *)type->tp_alloc(type, 0);
    if (self != NULL) {
        self->id = id;
        self->env = env;
        self->__weakref__ = NULL;
    }

    return (PyObject *)self;

}

static int
CapObject_init(CapObject *self, PyObject *args, PyObject *kwds) {
    return 0;
}

static int
CapObject_traverse(CapObject *self, visitproc visit, void *arg) {
    Py_VISIT(self->env);
    return 0;
}

static int
CapObject_clear(CapObject *self) {
    Py_CLEAR(self->env);
    return 0;
}

static void
CapObject_dealloc(CapObject* self) {

    if (self->__weakref__ != NULL)
        PyObject_ClearWeakRefs((PyObject *) self);

    CapObject_clear(self);
    self->ob_type->tp_free((PyObject*)self);

}

static PyObject *
CapObject_getattro(CapObject *self, PyObject *attribute) {

    PyObject *id, *keys, **item;
    Py_ssize_t size;

    id = PyLong_FromLong(self->id);
    if (id == NULL)
        return NULL;

    keys = PyDict_GetItem(_id2key_store, id);
    if (keys == NULL)
        return NULL;

    size = Py_SIZE(keys);
    item = ((PyTupleObject *)keys)->ob_item;

    PyObject *truth, *env_item;
    int i = 0;

    while (--size >= 0) {
        truth = PyObject_RichCompare(*item, attribute, Py_EQ);
        if (truth == NULL)
            return NULL;
        if (truth == Py_True) {
            env_item = ((PyListObject *)self->env)->ob_item[i];
            Py_INCREF(env_item);
            return env_item;
        }
        item++;
        i++;
    }

    truth = PyObject_GenericGetAttr((PyObject *)self, attribute);

    if (truth == NULL)
        return NULL;

    return truth;

    /*     PyErr_SetString(PyExc_AttributeError, "Cannot find."); */
    /*     return NULL; */

}

static PyMemberDef CapObject_members[] = {
/*     {"env", T_OBJECT_EX, offsetof(CapObject, env), 0, "env"}, */
/*     {"keys", T_OBJECT_EX, offsetof(CapObject, keys), 0, "keys"}, */
/*     {"id", T_OBJECT_EX, offsetof(CapObject, id), 0, "id"}, */
    {NULL}
};

static PyMethodDef CapObject_methods[] = {
    {"__getattribute__", (PyCFunction)CapObject_getattro, METH_O, 0},
    {NULL}
};

static PyTypeObject CapObjectType = {
    PyObject_HEAD_INIT(NULL)
    0,                                /* ob_size           */
    "Object",                         /* tp_name           */
    sizeof(CapObject),                /* tp_basicsize      */
    0,                                /* tp_itemsize       */
    (destructor)CapObject_dealloc,    /* tp_dealloc        */
    0,                                /* tp_print          */
    0,                                /* tp_getattr        */
    0,                                /* tp_setattr        */
    0,                                /* tp_compare        */
    0,                                /* tp_repr           */
    0,                                /* tp_as_number      */
    0,                                /* tp_as_sequence    */
    0,                                /* tp_as_mapping     */
    0,                                /* tp_hash           */
    0,                                /* tp_call           */
    0,                                /* tp_str            */
    (getattrofunc)CapObject_getattro, /* tp_getattro       */
    0,                                /* tp_setattro       */
    0,                                /* tp_as_buffer      */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,
                                      /* tp_flags          */
    "A Capability Object.",           /* tp_doc            */
    (traverseproc)CapObject_traverse, /* tp_traverse       */
    (inquiry)CapObject_clear,         /* tp_clear          */
    0,                                /* tp_richcompare    */
    offsetof(CapObject, __weakref__), /* tp_weaklistoffset */
    0,                                /* tp_iter           */
    0,                                /* tp_iternext       */
    CapObject_methods,                /* tp_methods        */
    0,                                /* tp_members        */
    0,                                /* tp_getset         */
    0,                                /* tp_base           */
    0,                                /* tp_dict           */
    0,                                /* tp_descr_get      */
    0,                                /* tp_descr_set      */
    0,                                /* tp_dictoffset     */
    0, /* (initproc)CapObject_init */ /* tp_init           */
    0,                                /* tp_alloc          */
    CapObject_new,                    /* tp_new            */
};

static PyMethodDef module_methods[] = {
    {NULL}
};

/*

if (! PyObject_TypeCheck(some_object, &CapObjectType)) {
    PyErr_SetString(PyExc_TypeError, "Not an Object.");
    return NULL;
}

*/

PyMODINIT_FUNC
init_capbase(void) {

    _key2id_store = PyDict_New();
    _id2key_store = PyDict_New();

    /* CapObjectType.tp_new = PyType_GenericNew; */

    if (PyType_Ready(&CapObjectType) < 0)
        return;

    PyObject* m;

    m = Py_InitModule3("_capbase", module_methods, "Capability support in Python.");

    if (m == NULL)
        return;

    Py_INCREF(&CapObjectType);
    PyModule_AddObject(m, "Object", (PyObject *)&CapObjectType);

    PyModule_AddObject(m, "_key2id_store", _key2id_store);
    PyModule_AddObject(m, "_id2key_store", _id2key_store);

}
