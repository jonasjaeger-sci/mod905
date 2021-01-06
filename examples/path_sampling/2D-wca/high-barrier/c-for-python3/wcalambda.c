/* Copyright (c) 2021, PyRETIS Development Team.
Distributed under the LGPLv2.1+ License. See LICENSE for more info. */
#include <Python.h>
#include <numpy/arrayobject.h>
#include <math.h>
#include <x86intrin.h>

// Forward function declaration.
static PyObject *orderp(PyObject *self, PyObject *args); 
static PyObject *orderv(PyObject *self, PyObject *args); 

// Method table:
static PyMethodDef methods[] = {
  { "orderp", orderp, METH_VARARGS, "Calculate order parameter."},
  { "orderv", orderv, METH_VARARGS, "Calculate velocity in order parameter."},
  { NULL, NULL, 0, NULL } /* Sentinel */
};

// Module definition:
static struct PyModuleDef lambdamodule = {
   PyModuleDef_HEAD_INIT,
   "wcalambda", // name of module
   "Calculate order parameters for WCA example",
    -1,
   methods
};


// Boilerplate: Module initialization.
PyMODINIT_FUNC PyInit_wcalambda(void) {
  //(void) Py_InitModule("wcalambda", methods);
  import_array();
  return PyModule_Create(&lambdamodule);
}


static inline npy_float64 pbc_dist(npy_float64 x,
                                   npy_float64 box,
                                   npy_float64 ibox) {
    return x - nearbyint(x * ibox) * box;
}


static PyObject *orderp(PyObject *self, PyObject *args) {
  // Input variables:
  npy_int64 i, j;
  PyArrayObject *ppos, *pbox, *pibox; 
  // Internal variables:
  npy_float64 delr;
  __m128d dr, drsq;

  // Parse arguments. 
  if (!PyArg_ParseTuple(args, "O!O!O!ll",
                        &PyArray_Type, &ppos,
                        &PyArray_Type, &pbox,
                        &PyArray_Type, &pibox,
                        &i, &j)){
    return NULL;
  }
  // Get underlying arrays from numpy arrays. 
  __m128d *pos = (__m128d*)PyArray_DATA(ppos);
  npy_float64 *box = (npy_float64*)PyArray_DATA(pbox);
  npy_float64 *ibox = (npy_float64*)PyArray_DATA(pibox);
  dr =_mm_sub_pd(pos[i], pos[j]);
  dr[0] = pbc_dist(dr[0], box[0], ibox[0]);
  dr[1] = pbc_dist(dr[1], box[1], ibox[1]);
  drsq = _mm_dp_pd(dr, dr, 0x71);
  delr = sqrt(drsq[0]);
  PyObject *ret = Py_BuildValue("d", delr);
  return ret;
}

static PyObject *orderv(PyObject *self, PyObject *args) {
  // Input variables:
  npy_int64 i, j;
  PyArrayObject *ppos, *pvel, *pbox, *pibox; 
  // Internal variables:
  npy_float64 delv;
  __m128d dr, drsq, dv, drdv;

  // Parse arguments. 
  if (!PyArg_ParseTuple(args, "O!O!O!O!ll",
                        &PyArray_Type, &ppos,
                        &PyArray_Type, &pvel,
                        &PyArray_Type, &pbox,
                        &PyArray_Type, &pibox,
                        &i, &j)){
    return NULL;
  }
  // Get underlying arrays from numpy arrays. 
  __m128d *pos = (__m128d*)PyArray_DATA(ppos);
  __m128d *vel = (__m128d*)PyArray_DATA(pvel);
  npy_float64 *box = (npy_float64*)PyArray_DATA(pbox);
  npy_float64 *ibox = (npy_float64*)PyArray_DATA(pibox);
  dr =_mm_sub_pd(pos[i], pos[j]);
  dr[0] = pbc_dist(dr[0], box[0], ibox[0]);
  dr[1] = pbc_dist(dr[1], box[1], ibox[1]);
  drsq = _mm_dp_pd(dr, dr, 0x71);
  dv =_mm_sub_pd(vel[i], vel[j]);
  drdv = _mm_dp_pd(dr, dv, 0x71);
  delv = drdv[0] / sqrt(drsq[0]);
  PyObject *ret = Py_BuildValue("d", delv);
  return ret;
}
