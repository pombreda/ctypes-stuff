#include "Python.h"

static char module_docs[] = "XXX tbd";

static PyObject *interface_version; /* "PyArrayInterface Version 3" */

typedef struct {
	int two;		/* contains the integer 2 -- simple sanity check */
	int nd;			/* number of dimensions */
	char typekind;		/* kind in array --- character code of typestr */
	int itemsize;		/* size of each element */
	int flags;		/* flags indicating how the data should be interpreted */
				/*   must set ARR_HAS_DESCR bit to validate descr */
	Py_intptr_t *shape;	/* A length-nd array of shape information */
	Py_intptr_t *strides;	/* A length-nd array of stride information */
	void *data;		/* A pointer to the first element of the array */
/*	PyObject *descr;	/* NULL or data-description (same as descr key
				        of __array_interface__) -- must set ARR_HAS_DESCR
					flag or this will be ignored */
} PyArrayInterface;


typedef struct {
	PyObject_HEAD
	int nd;
	char typekind;
	int itemsize;
	Py_intptr_t *shape;
} ArrayStruct;

static void
ArrayDescr_free(void *ptr, void *extra)
{
	PyMem_Free(ptr);
}

static PyObject *
ArrayStruct_descr_get(PyObject *_self, PyObject *obj, PyObject *type)
{
	ArrayStruct *self = (ArrayStruct *)_self;
	PyArrayInterface *ai;
	Py_ssize_t size;
	void *ptr;

	if (obj == NULL) {
		Py_INCREF(_self);
		return _self;
	}

	if ((obj->ob_type->tp_as_buffer == NULL)
	    || (obj->ob_type->tp_as_buffer->bf_getreadbuffer == NULL)) {
		PyErr_SetString(PyExc_TypeError,
				"object does not expose buffer interface");
		return NULL;
	}

	size = obj->ob_type->tp_as_buffer->bf_getreadbuffer(obj, 0, (void *)&ptr);
	if (size < 0)
		return NULL;

	ai = (PyArrayInterface *)PyMem_Malloc(sizeof(PyArrayInterface));
	if (ai == NULL)
		return NULL;

	ai->two = 2;
	ai->nd = self->nd;
	ai->typekind = self->typekind;
	ai->itemsize = self->itemsize;
	ai->flags = 0x701; /* WRITEABLE | NOTSWAPPED | ALIGNED | CONTIGUOUS */
	ai->shape = self->shape;
	ai->strides = NULL;
	ai->data = ptr;

#ifdef _DEBUG
	_asm int 3;
#endif

	return PyCObject_FromVoidPtrAndDesc(ai,
					    PyTuple_Pack(2, interface_version, obj),
					    ArrayDescr_free);
}

PyTypeObject ArrayStruct_Type = {
	PyObject_HEAD_INIT(NULL)
	0,					/* ob_size */
	"_array_struct.ArrayStruct",		/* tp_name */
	sizeof(ArrayStruct),			/* tp_basicsize */
	0,					/* tp_itemsize */
	0,					/* tp_dealloc */
	0,					/* tp_print */
	0,					/* tp_getattr */
	0,					/* tp_setattr */
	0,					/* tp_compare */
	0,			       		/* tp_repr */
	0,					/* tp_as_number */
	0,					/* tp_as_sequence */
	0,					/* tp_as_mapping */
	0,					/* tp_hash */
	0,					/* tp_call */
	0,					/* tp_str */
	0,					/* tp_getattro */
	0,					/* tp_setattro */
	0,					/* tp_as_buffer */
	Py_TPFLAGS_DEFAULT,			/* tp_flags */
	"__array_struct__ descriptor",		/* tp_doc */
	0,					/* tp_traverse */
	0,					/* tp_clear */
	0,					/* tp_richcompare */
	0,					/* tp_weaklistoffset */
	0,					/* tp_iter */
	0,					/* tp_iternext */
	0,					/* tp_methods */
	0,					/* tp_members */
	0,					/* tp_getset */
	0,					/* tp_base */
	0,					/* tp_dict */
	&ArrayStruct_descr_get,			/* tp_descr_get */
	0,					/* tp_descr_set */
	0,					/* tp_dictoffset */
	0,					/* tp_init */
	0,					/* tp_alloc */
	0,					/* tp_new */
	0,					/* tp_free */
};


static char prep_simple_doc[] = "prep_simple(ctype, typekind, itemsize)";

static PyObject *typecodes;

static PyObject *
prep_simple(PyObject *self, PyObject *args)
{
	PyObject *ctype;
	int typekind, itemsize;
	ArrayStruct *ai;
	int res;
	char fmt[32];

	if (!PyArg_ParseTuple(args, "Oii",
			      &ctype, &typekind, &itemsize))
		return NULL;
	sprintf(fmt, "%c%d", typekind, itemsize);
	/* build a dictionary where we can lookup simple types */
	if (-1 == PyDict_SetItemString(typecodes, fmt, ctype))
		return NULL;
	ai = (ArrayStruct *)PyObject_CallObject((PyObject *)&ArrayStruct_Type, NULL);
	if (ai == NULL)
		return NULL;
	ai->nd = 0;
	ai->typekind = typekind;
	ai->itemsize = itemsize;
	ai->shape = NULL;

	res = PyObject_SetAttrString(ctype, "__array_struct__", (PyObject *)ai);
	Py_DECREF((PyObject *)ai);
	if (res == -1)
		return NULL;
	Py_INCREF(Py_None);
	return Py_None;
}

static char prep_array_doc[] = "prep_array(ctype, arraydesc, shape)";

static PyObject *
prep_array(PyObject *self, PyObject *args)
{
	PyObject *ctype;
	PyObject *shape;
	ArrayStruct *ai;
	ArrayStruct *item_ai;
	int res;
	Py_ssize_t i;

	if (!PyArg_ParseTuple(args, "OO!O!",
			      &ctype,
			      &ArrayStruct_Type, &item_ai,
			      &PyTuple_Type, &shape))
		return NULL;

	ai = (ArrayStruct *)PyObject_CallObject((PyObject *)&ArrayStruct_Type, NULL);
	if (ai == NULL)
		return NULL;

	ai->shape = PyMem_Malloc(sizeof(Py_intptr_t) * PyTuple_GET_SIZE(shape));
	if (ai->shape == NULL) {
		Py_DECREF(ai);
		return NULL;
	}
	ai->nd = PyTuple_GET_SIZE(shape);

	for (i = 0; i < PyTuple_GET_SIZE(shape); ++i) {
		ai->shape[i] = PyInt_AsLong(PyTuple_GET_ITEM(shape, i));
		if (ai->shape[i] == -1 && PyErr_Occurred()) {
			Py_DECREF(ai);
			return NULL;
		}
	}

	ai->typekind = item_ai->typekind;
	ai->itemsize = item_ai->itemsize;

	res = PyObject_SetAttrString(ctype, "__array_struct__", (PyObject *)ai);
	Py_DECREF((PyObject *)ai);
	if (res == -1)
		return NULL;

	Py_INCREF(Py_None);
	return Py_None;
}

static char as_ctypes_doc[] = "Create a ctypes array from an object implementing PEP 3118";

static PyObject *
as_ctypes(PyObject *self, PyObject *arg)
{
	PyObject *cobj;
//	PyObject *arr;
	PyArrayInterface *ai;
	char fmt[32];
	PyObject *ctype, *atype;
	PyObject *result;
	Py_intptr_t i;

#ifdef _DEBUG
	_asm int 3;
#endif

	cobj = PyObject_GetAttrString(arg, "__array_struct__");
	if (cobj == NULL)
		return NULL;
//	arr = PyCObject_GetDesc(cobj);

	ai = (PyArrayInterface *)PyCObject_AsVoidPtr(cobj);
	if (ai->two != 2) {
		PyErr_Format(PyExc_TypeError,
			     "Wrong array interface version '%d', expected '2'",
			     ai->two);
		return NULL;
	}
	if ((ai->flags & 0x701) != 0x701) {
		PyErr_Format(PyExc_TypeError,
			     "Array style %x unsupported",
			     ai->flags);
	}
	sprintf(fmt, "%c%d", ai->typekind, ai->itemsize);
	ctype = PyDict_GetItemString(typecodes, fmt);
	if (ctype == NULL)
		return NULL;
	atype = ctype;
	Py_INCREF(atype);
	for (i = 0; i < ai->nd; ++i) {
		PyObject *factor = PyInt_FromLong((int)ai->shape[i]);
		// XXX NULL CHECK
		ctype = PyNumber_Multiply(atype, factor);
		// XXX NULL CHECK
		Py_DECREF(atype);
		atype = ctype;
	}
	result = PyObject_CallMethod(atype, "from_address",
				     "N", PyLong_FromVoidPtr(ai->data));
	Py_DECREF(atype);
	PyObject_SetAttrString(result, "__keep", arg);
	/* ai->descr; is unused */
	return result;
}

PyMethodDef module_methods[] = {
	{"prep_simple", prep_simple, METH_VARARGS, prep_simple_doc},
	{"prep_array", prep_array, METH_VARARGS, prep_array_doc},
	{"as_ctypes", as_ctypes, METH_O, as_ctypes_doc},
	{NULL,      NULL}        /* Sentinel */
};

PyMODINIT_FUNC
init_array_struct(void)
{
	PyObject *m;

	m = Py_InitModule3("_array_struct", module_methods, module_docs);
	if (!m)
		return;

	interface_version = PyString_FromString("PyArrayInterface Version 3");

	ArrayStruct_Type.tp_new = PyType_GenericNew;
	if (PyType_Ready(&ArrayStruct_Type) < 0)
		return;

	typecodes = PyDict_New();
	if (typecodes == NULL)
		return;
}
