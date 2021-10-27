/* Copyright (c) 2021, PyRETIS Development Team.
Distributed under the LGPLv2.1+ License. See LICENSE for more info. */
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <numpy/arrayobject.h>
#include <math.h>

// Forward function declaration.
static PyObject *step1(PyObject *self, PyObject *args); 
static PyObject *step2(PyObject *self, PyObject *args); 

// Boilerplate: function list.
static PyMethodDef vvmethods[] = {
  { "step1", step1, METH_VARARGS, "Velocity Verlet - update positions and velocity"},
  { "step2", step2, METH_VARARGS, "Velocity Verlet - update velocity"},
  { NULL, NULL, 0, NULL } /* Sentinel */
};

static struct PyModuleDef vvintegrator =
{
    PyModuleDef_HEAD_INIT,
    "vvintegrator",
    "Velocity Verlet Integrator",
    -1,
    vvmethods
};

// Boilerplate: Module initialization.
PyMODINIT_FUNC PyInit_vvintegrator(void) {
  import_array();
  return PyModule_Create(&vvintegrator);
}


static PyObject *step1(PyObject *self, PyObject *args) {
  // Input variables:
  npy_int64 npart, dim;
  npy_float64 delta_t, half_delta_t;
  PyArrayObject *py_pos, *py_vel, *py_force, *py_imass;
  // Internal variables:
  npy_int64 i, xi, yi, zi;

  // Parse arguments. 
  if (!PyArg_ParseTuple(args, "O!O!O!O!ddll",
                        &PyArray_Type, &py_pos,
                        &PyArray_Type, &py_vel,
                        &PyArray_Type, &py_force,
                        &PyArray_Type, &py_imass,
                        &delta_t, &half_delta_t,
                        &npart, &dim)){
    return NULL;
  }
  // Get underlying arrays from numpy arrays. 
  npy_float64 *pos = (npy_float64*)PyArray_DATA(py_pos);
  npy_float64 *vel = (npy_float64*)PyArray_DATA(py_vel);
  npy_float64 *force = (npy_float64*)PyArray_DATA(py_force);
  npy_float64 *imass = (npy_float64*)PyArray_DATA(py_imass);
  // Update positions and velocity
  for(i = 0; i < npart; i++){
    xi = 3*i;
    yi = 3*i + 1;
    zi = 3*i + 2;
    vel[xi] += half_delta_t * force[xi] * imass[i];
    vel[yi] += half_delta_t * force[yi] * imass[i];
    vel[zi] += half_delta_t * force[zi] * imass[i];
    pos[xi] += delta_t * vel[xi];
    pos[yi] += delta_t * vel[yi];
    pos[zi] += delta_t * vel[zi];
  }
  Py_RETURN_NONE;
}

static PyObject *step2(PyObject *self, PyObject *args) {
  // Input variables:
  npy_int64 npart, dim;
  npy_float64 half_delta_t;
  PyArrayObject *py_vel, *py_force, *py_imass;
  // Internal variables:
  npy_int64 i, xi, yi, zi;

  // Parse arguments. 
  if (!PyArg_ParseTuple(args, "O!O!O!dll",
                        &PyArray_Type, &py_vel,
                        &PyArray_Type, &py_force,
                        &PyArray_Type, &py_imass,
                        &half_delta_t,
                        &npart, &dim)){
    return NULL;
  }
  // Get underlying arrays from numpy arrays. 
  npy_float64 *vel = (npy_float64*)PyArray_DATA(py_vel);
  npy_float64 *force = (npy_float64*)PyArray_DATA(py_force);
  npy_float64 *imass = (npy_float64*)PyArray_DATA(py_imass);
  // Update positions and velocity
  for(i = 0; i < npart; i++){
    xi = 3*i;
    yi = 3*i + 1;
    zi = 3*i + 2;
    vel[xi] += half_delta_t * force[xi] * imass[i];
    vel[yi] += half_delta_t * force[yi] * imass[i];
    vel[zi] += half_delta_t * force[zi] * imass[i];
  }
  Py_RETURN_NONE;
}
