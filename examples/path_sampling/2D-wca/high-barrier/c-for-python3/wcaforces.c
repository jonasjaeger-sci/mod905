/* Copyright (c) 2015, PyRETIS Development Team.
Distributed under the LGPLv2.1+ License. See LICENSE for more info. */
#include <Python.h>
#include <numpy/arrayobject.h>
#include <math.h>
#include <x86intrin.h>

// Forward function declaration.
static PyObject *potential2D(PyObject *self, PyObject *args); 
static PyObject *force2D(PyObject *self, PyObject *args); 
static PyObject *force_and_pot2D(PyObject *self, PyObject *args); 

// Method table:
static PyMethodDef methods[] = {
  { "potential2D", potential2D, METH_VARARGS, "Calculate potential energy."},
  { "force2D", force2D, METH_VARARGS, "Calculate force."},
  { "force_and_pot2D", force_and_pot2D, METH_VARARGS, "Calculate force and potential energy."},
  { NULL, NULL, 0, NULL } /* Sentinel */
};


// Module definition:
static struct PyModuleDef forcemodule = {
   PyModuleDef_HEAD_INIT,
   "wcaforces", // name of module
   "Calculate forces and potential for WCA example",
    -1,
   methods
};


// Boilerplate: Module initialization.
PyMODINIT_FUNC PyInit_wcaforces(void) {
  //(void) Py_InitModule("wcalambda", methods);
  import_array();
  return PyModule_Create(&forcemodule);
}

static inline npy_float64 pbc_dist(npy_float64 x,
                                   npy_float64 box,
                                   npy_float64 ibox) {
    return x - nearbyint(x * ibox) * box;
}


static PyObject *potential2D(PyObject *self, PyObject *args) {
  npy_int64 posi, posj, i, j, npart;
  npy_float64 rwidth, width2, height;
  PyArrayObject *p_pos, *p_box, *p_ibox; 
  npy_float64 delr, d1, d2;
  npy_float64 lj3, lj4, offset, rcut2, r2inv, r6inv;
  __m128d dr, drsq;

  // Parse arguments. 
  if (!PyArg_ParseTuple(args, "O!O!O!dddllddddl",
                        &PyArray_Type, &p_pos,
                        &PyArray_Type, &p_box,
                        &PyArray_Type, &p_ibox,
                        &rwidth, &width2, &height,
                        &posi, &posj,
                        &lj3, &lj4, &offset, &rcut2, &npart)){
    return NULL;
  }
  // Get underlying arrays from numpy arrays. 
  __m128d *pos = (__m128d*)PyArray_DATA(p_pos);
  npy_float64 *box = (npy_float64*)PyArray_DATA(p_box);
  npy_float64 *ibox = (npy_float64*)PyArray_DATA(p_ibox);
  // Calculate the contribution from the bond:
  dr =_mm_sub_pd(pos[posi], pos[posj]);
  dr[0] = pbc_dist(dr[0], box[0], ibox[0]);
  dr[1] = pbc_dist(dr[1], box[1], ibox[1]);
  drsq = _mm_dp_pd(dr, dr, 0x71);
  delr = sqrt(drsq[0]);
  d1 = pow(delr - rwidth, 2);
  d2 = pow(1.0 - (d1 / width2),2);
  npy_float64 vpot = height * d2;
  // Calculate the contribution from WCA pairs:
  for(i = 0; i < npart-1; i++){
    for (j = i + 1; j < npart; j++){
        dr = _mm_sub_pd(pos[i], pos[j]);
        dr[0] = pbc_dist(dr[0], box[0], ibox[0]);
        dr[1] = pbc_dist(dr[1], box[1], ibox[1]);
        drsq = _mm_dp_pd(dr, dr, 0x71);
        delr = drsq[0];
        if (delr < rcut2){
            r2inv = 1.0 / delr;
            r6inv = r2inv*r2inv*r2inv;
            vpot += r6inv * (lj3 * r6inv - lj4) - offset;
        }
    }
  }
  PyObject *ret = Py_BuildValue("d", vpot);
  return ret;
}


static PyObject *force2D(PyObject *self, PyObject *args) {
  npy_int64 npart, dim, pari, parj;
  npy_float64 rwidth, width2, height4;
  PyArrayObject *p_pos, *p_box, *p_ibox, *p_force, *p_virial; 
  npy_float64 delr, d1, forcelj, lj1, lj2, rcut2, r2inv, r6inv;
  npy_int64 i, j;
  __m128d dr, drsq, forceij;

  // Parse arguments. 
  if (!PyArg_ParseTuple(args, "O!O!O!O!O!dddlldddll",
                        &PyArray_Type, &p_pos,
                        &PyArray_Type, &p_box,
                        &PyArray_Type, &p_ibox,
                        &PyArray_Type, &p_force,
                        &PyArray_Type, &p_virial,
                        &rwidth, &width2, &height4,
                        &pari, &parj, &lj1, &lj2, &rcut2,
                        &npart, &dim)){
    return NULL;
  }
  // Get underlying arrays from numpy arrays. 
  __m128d *force = (__m128d*)PyArray_DATA(p_force);
  __m128d *pos = (__m128d*)PyArray_DATA(p_pos);
  npy_float64 *virial = (npy_float64*)PyArray_DATA(p_virial);
  npy_float64 *box = (npy_float64*)PyArray_DATA(p_box);
  npy_float64 *ibox = (npy_float64*)PyArray_DATA(p_ibox);
  // Zero virial:
  for(i = 0; i < dim*dim; i++) {
    virial[i] = 0;
  }
  // Set all forces to zero. 
  for(i = 0; i < npart; i++) {
    force[i] = _mm_set1_pd(0);
  }
  // Calculate forces from bond:
  dr =_mm_sub_pd(pos[pari], pos[parj]);
  dr[0] = pbc_dist(dr[0], box[0], ibox[0]);
  dr[1] = pbc_dist(dr[1], box[1], ibox[1]);
  drsq = _mm_dp_pd(dr, dr, 0x71);
  delr = sqrt(drsq[0]);
  d1 = delr - rwidth;
  forcelj = height4 * (1.0 - pow(d1, 2) / width2) * (d1 / width2);
  forceij = forcelj * dr / delr;
  force[pari] += forceij;
  force[parj] -= forceij;
  virial[0] += forceij[0]*dr[0];
  virial[1] += forceij[0]*dr[1];
  virial[2] += forceij[1]*dr[0];
  virial[3] += forceij[1]*dr[1];
  // Calculate forces from WCA-pairs:
  for(i = 0; i < npart-1; i++){
    for (j = i + 1; j < npart; j++){
        dr = _mm_sub_pd(pos[i], pos[j]);
        dr[0] = pbc_dist(dr[0], box[0], ibox[0]);
        dr[1] = pbc_dist(dr[1], box[1], ibox[1]);
        drsq = _mm_dp_pd(dr, dr, 0x71);
        delr = drsq[0];
        if (delr < rcut2){
            r2inv = 1.0 / delr;
            r6inv = r2inv*r2inv*r2inv;
            forcelj = r2inv * r6inv * (lj1 * r6inv - lj2);
            forceij = forcelj * dr;
            force[i] += forceij;
            force[j] -= forceij;
            virial[0] += forceij[0]*dr[0];
            virial[1] += forceij[0]*dr[1];
            virial[2] += forceij[1]*dr[0];
            virial[3] += forceij[1]*dr[1];
        }
    }
  }
  Py_RETURN_NONE;
}


static PyObject *force_and_pot2D(PyObject *self, PyObject *args) {
  npy_int64 npart, dim, pari, parj;
  npy_float64 rwidth, width2, height, height4;
  PyArrayObject *p_pos, *p_box, *p_ibox, *p_force, *p_virial; 
  npy_float64 delr, d1, d2, forcelj;
  npy_float64 lj1, lj2, lj3, lj4, offset, rcut2;
  npy_float64 r2inv, r6inv;
  npy_int64 i, j;
  __m128d dr, drsq, forceij;
  // Parse arguments. 
  if (!PyArg_ParseTuple(args, "O!O!O!O!O!ddddllddddddll",
                        &PyArray_Type, &p_pos,
                        &PyArray_Type, &p_box,
                        &PyArray_Type, &p_ibox,
                        &PyArray_Type, &p_force,
                        &PyArray_Type, &p_virial,
                        &rwidth, &width2, &height, &height4,
                        &pari, &parj, 
                        &lj1, &lj2, &lj3, &lj4, &offset, &rcut2,
                        &npart, &dim)){
    return NULL;
  }
  // Get underlying arrays from numpy arrays. 
  __m128d *force = (__m128d*)PyArray_DATA(p_force);
  __m128d *pos = (__m128d*)PyArray_DATA(p_pos);
  npy_float64 *virial = (npy_float64*)PyArray_DATA(p_virial);
  npy_float64 *box = (npy_float64*)PyArray_DATA(p_box);
  npy_float64 *ibox = (npy_float64*)PyArray_DATA(p_ibox);
  // Zero virial:
  for(i = 0; i < dim*dim; i++) {
    virial[i] = 0;
  }
  // Set all forces to zero. 
  for(i = 0; i < npart; i++) {
    force[i] = _mm_set1_pd(0);
  }
  // Calculate forces:
  dr =_mm_sub_pd(pos[pari], pos[parj]);
  dr[0] = pbc_dist(dr[0], box[0], ibox[0]);
  dr[1] = pbc_dist(dr[1], box[1], ibox[1]);
  drsq = _mm_dp_pd(dr, dr, 0x71);
  delr = sqrt(drsq[0]);
  d1 = delr - rwidth;
  forcelj = height4 * (1.0 - pow(d1, 2) / width2) * (d1 / width2);
  forceij = forcelj * dr / delr;
  force[pari] += forceij;
  force[parj] -= forceij;
  virial[0] += forceij[0]*dr[0];
  virial[1] += forceij[0]*dr[1];
  virial[2] += forceij[1]*dr[0];
  virial[3] += forceij[1]*dr[1];
  d2 = pow(1.0 - (d1*d1 / width2),2);
  npy_float64 vpot = height * d2;
  // Calculate contributions from WCA-pairs:
  for(i = 0; i < npart-1; i++){
    for (j = i + 1; j < npart; j++){
        dr = _mm_sub_pd(pos[i], pos[j]);
        dr[0] = pbc_dist(dr[0], box[0], ibox[0]);
        dr[1] = pbc_dist(dr[1], box[1], ibox[1]);
        drsq = _mm_dp_pd(dr, dr, 0x71);
        delr = drsq[0];
        if (delr < rcut2){
            r2inv = 1.0 / delr;
            r6inv = r2inv*r2inv*r2inv;
            forcelj = r2inv * r6inv * (lj1 * r6inv - lj2);
            vpot += r6inv * (lj3 * r6inv - lj4) - offset;
            forceij = forcelj * dr;
            force[i] += forceij;
            force[j] -= forceij;
            virial[0] += forceij[0]*dr[0];
            virial[1] += forceij[0]*dr[1];
            virial[2] += forceij[1]*dr[0];
            virial[3] += forceij[1]*dr[1];
        }
    }
  }
  PyObject *ret = Py_BuildValue("d", vpot);
  return ret;
}

