
#include <Python.h>
#include <numpy/arrayobject.h>
#include <math.h>

// Forward function declaration.
static PyObject *potential(PyObject *self, PyObject *args); 
static PyObject *force(PyObject *self, PyObject *args); 
static PyObject *force_and_pot(PyObject *self, PyObject *args); 

// Boilerplate: function list.
static PyMethodDef ljmethods[] = {
  { "potential", potential, METH_VARARGS, "Calculate potential energy."},
  { "force", force, METH_VARARGS, "Calculate force."},
  { "force_and_pot", force_and_pot, METH_VARARGS, "Calculate force and potential energy."},
  { NULL, NULL, 0, NULL } /* Sentinel */
};

static struct PyModuleDef ljc =
{
    PyModuleDef_HEAD_INIT,
    "ljc",
    "Compute Lennard-Jones interactions",
    -1,
    ljmethods
};

// Boilerplate: Module initialization.
PyMODINIT_FUNC PyInit_ljc(void) {
  import_array();
  return PyModule_Create(&ljc);
}


static inline npy_float64 pbc_dist(npy_float64 x,
                                   npy_float64 box,
                                   npy_float64 ibox) {
    return x - nearbyint(x * ibox) * box;
}


static PyObject *potential(PyObject *self, PyObject *args) {
  // Input variables:
  npy_int64 npart, dim, ntype;
  npy_int64 itype, loc;
  PyArrayObject *py_pos, *py_box, *py_ibox, *py_lj3, *py_lj4, *py_rcut2, *py_offset, *py_ptype;
  // Internal variables:
  npy_float64 dx, dy, dz, rsq, r2inv, r6inv;
  npy_int64 i, xi, yi, zi;
  npy_int64 j, xj, yj, zj;

  // Parse arguments. 
  if (!PyArg_ParseTuple(args, "O!O!O!O!O!O!O!O!lll",
                        &PyArray_Type, &py_pos,
                        &PyArray_Type, &py_box,
                        &PyArray_Type, &py_ibox,
                        &PyArray_Type, &py_lj3,
                        &PyArray_Type, &py_lj4,
                        &PyArray_Type, &py_offset,
                        &PyArray_Type, &py_rcut2,
                        &PyArray_Type, &py_ptype,
                        &npart, &dim, &ntype)){
    return NULL;
  }
  // Get underlying arrays from numpy arrays. 
  npy_float64 *pos = (npy_float64*)PyArray_DATA(py_pos);
  npy_float64 *box = (npy_float64*)PyArray_DATA(py_box);
  npy_float64 *ibox = (npy_float64*)PyArray_DATA(py_ibox);
  npy_float64 *lj3 = (npy_float64*)PyArray_DATA(py_lj3);
  npy_float64 *lj4 = (npy_float64*)PyArray_DATA(py_lj4);
  npy_float64 *rcut2 = (npy_float64*)PyArray_DATA(py_rcut2);
  npy_float64 *offset = (npy_float64*)PyArray_DATA(py_offset);
  npy_int64 *ptype = (npy_int64*)PyArray_DATA(py_ptype);
  npy_float64 vpot = 0.0;
  // Calculate potential:
  for(i = 0; i < npart-1; i++){
    xi = 3*i;
    yi = 3*i + 1;
    zi = 3*i + 2;
    itype = ptype[i];
    for (j = i + 1; j < npart; j++){
        loc = itype + ntype * ptype[j];
        xj = 3*j;
        yj = 3*j + 1;
        zj = 3*j + 2;
        dx = pos[xi] - pos[xj];
        dy = pos[yi] - pos[yj];
        dz = pos[zi] - pos[zj];
        dx = pbc_dist(dx, box[0], ibox[0]);
        dy = pbc_dist(dy, box[1], ibox[1]);
        dz = pbc_dist(dz, box[2], ibox[2]);
        rsq = dx*dx + dy*dy + dz*dz;
        if (rsq < rcut2[loc]){
            r2inv = 1.0 / rsq;
            r6inv = r2inv*r2inv*r2inv;
            vpot += r6inv * (lj3[loc] * r6inv - lj4[loc]) - offset[loc];
        }
    }
  }
  /* Clean up */
  /* Build the output tuple */
  PyObject *ret = Py_BuildValue("d", vpot);
  return ret;
}


static PyObject *force(PyObject *self, PyObject *args) {
  // Input variables:
  npy_int64 npart, dim, ntype;
  npy_int64 itype, loc;
  PyArrayObject *py_pos, *py_box, *py_ibox, *py_force, *py_virial;
  PyArrayObject *py_lj1, *py_lj2, *py_rcut2, *py_ptype;
  // Internal variables:
  npy_float64 dx, dy, dz, rsq, r2inv, r6inv;
  npy_float64 forcelj, fx, fy, fz;
  npy_int64 i, xi, yi, zi;
  npy_int64 j, xj, yj, zj;

  // Parse arguments. 
  if (!PyArg_ParseTuple(args, "O!O!O!O!O!O!O!O!O!lll",
                        &PyArray_Type, &py_pos,
                        &PyArray_Type, &py_box,
                        &PyArray_Type, &py_ibox,
                        &PyArray_Type, &py_lj1,
                        &PyArray_Type, &py_lj2,
                        &PyArray_Type, &py_rcut2,
                        &PyArray_Type, &py_ptype,
                        &PyArray_Type, &py_force,
                        &PyArray_Type, &py_virial,
                        &npart, &dim, &ntype)){
    return NULL;
  }
  // Get underlying arrays from numpy arrays. 
  npy_float64 *force = (npy_float64*)PyArray_DATA(py_force);
  npy_float64 *virial = (npy_float64*)PyArray_DATA(py_virial);
  npy_float64 *pos = (npy_float64*)PyArray_DATA(py_pos);
  npy_float64 *box = (npy_float64*)PyArray_DATA(py_box);
  npy_float64 *ibox = (npy_float64*)PyArray_DATA(py_ibox);
  npy_float64 *lj1 = (npy_float64*)PyArray_DATA(py_lj1);
  npy_float64 *lj2 = (npy_float64*)PyArray_DATA(py_lj2);
  npy_float64 *rcut2 = (npy_float64*)PyArray_DATA(py_rcut2);
  npy_int64 *ptype = (npy_int64*)PyArray_DATA(py_ptype);
  // Create array for forces:
  //PyObject *ret = PyArray_SimpleNew(dim, test, NPY_DOUBLE);
  // Zero virial:
  for(i = 0; i < dim*dim; i++) {
    virial[i] = 0;
  }
  // Set all forces to zero. 
  for(i = 0; i < npart; i++) {
    force[3*i] = 0;
    force[3*i+1] = 0;
    force[3*i+2] = 0;
  }
  // Calculate forces:
  for(i = 0; i < npart-1; i++){
    xi = 3*i;
    yi = 3*i + 1;
    zi = 3*i + 2;
    itype = ptype[i];
    for (j = i + 1; j < npart; j++){
        loc = itype + ntype * ptype[j];
        xj = 3*j;
        yj = 3*j + 1;
        zj = 3*j + 2;
        dx = pos[xi] - pos[xj];
        dy = pos[yi] - pos[yj];
        dz = pos[zi] - pos[zj];
        dx = pbc_dist(dx, box[0], ibox[0]);
        dy = pbc_dist(dy, box[1], ibox[1]);
        dz = pbc_dist(dz, box[2], ibox[2]);
        rsq = dx*dx + dy*dy + dz*dz;
        if (rsq < rcut2[loc]){
            r2inv = 1.0 / rsq;
            r6inv = r2inv*r2inv*r2inv;
            forcelj = r2inv * r6inv * (lj1[loc] * r6inv - lj2[loc]);
            fx = forcelj * dx;
            fy = forcelj * dy;
            fz = forcelj * dz;
            force[xi] += fx;
            force[yi] += fy;
            force[zi] += fz;
            force[xj] -= fx;
            force[yj] -= fy;
            force[zj] -= fz;
            virial[0] += fx*dx;
            virial[1] += fx*dy;
            virial[2] += fx*dz;
            virial[3] += fy*dx;
            virial[4] += fy*dy;
            virial[5] += fy*dz;
            virial[6] += fz*dx;
            virial[7] += fz*dy;
            virial[8] += fz*dz;
        }
    }
  }
  Py_RETURN_NONE;
}


static PyObject *force_and_pot(PyObject *self, PyObject *args) {
  // Input variables:
  npy_int64 npart, dim, ntype;
  npy_int64 itype, loc;
  PyArrayObject *py_pos, *py_box, *py_ibox, *py_force, *py_virial;
  PyArrayObject *py_lj1, *py_lj2, *py_lj3, *py_lj4, *py_rcut2, *py_offset, *py_ptype;
  // Internal variables:
  npy_float64 dx, dy, dz, rsq, r2inv, r6inv;
  npy_float64 forcelj, fx, fy, fz;
  npy_int64 i, xi, yi, zi;
  npy_int64 j, xj, yj, zj;

  // Parse arguments. 
  if (!PyArg_ParseTuple(args, "O!O!O!O!O!O!O!O!O!O!O!O!lll",
                        &PyArray_Type, &py_pos,
                        &PyArray_Type, &py_box,
                        &PyArray_Type, &py_ibox,
                        &PyArray_Type, &py_lj1,
                        &PyArray_Type, &py_lj2,
                        &PyArray_Type, &py_lj3,
                        &PyArray_Type, &py_lj4,
                        &PyArray_Type, &py_offset,
                        &PyArray_Type, &py_rcut2,
                        &PyArray_Type, &py_ptype,
                        &PyArray_Type, &py_force,
                        &PyArray_Type, &py_virial,
                        &npart, &dim, &ntype)){
    return NULL;
  }
  // Get underlying arrays from numpy arrays. 
  npy_float64 *force = (npy_float64*)PyArray_DATA(py_force);
  npy_float64 *virial = (npy_float64*)PyArray_DATA(py_virial);
  npy_float64 *pos = (npy_float64*)PyArray_DATA(py_pos);
  npy_float64 *box = (npy_float64*)PyArray_DATA(py_box);
  npy_float64 *ibox = (npy_float64*)PyArray_DATA(py_ibox);
  npy_float64 *lj1 = (npy_float64*)PyArray_DATA(py_lj1);
  npy_float64 *lj2 = (npy_float64*)PyArray_DATA(py_lj2);
  npy_float64 *lj3 = (npy_float64*)PyArray_DATA(py_lj3);
  npy_float64 *lj4 = (npy_float64*)PyArray_DATA(py_lj4);
  npy_float64 *offset = (npy_float64*)PyArray_DATA(py_offset);
  npy_float64 *rcut2 = (npy_float64*)PyArray_DATA(py_rcut2);
  npy_int64 *ptype = (npy_int64*)PyArray_DATA(py_ptype);
  npy_float64 vpot = 0.0;
  // Create array for forces:
  //PyObject *ret = PyArray_SimpleNew(dim, test, NPY_DOUBLE);
  // Zero virial:
  for(i = 0; i < dim*dim; i++) {
    virial[i] = 0;
  }
  // Set all forces to zero. 
  for(i = 0; i < npart; i++) {
    force[3*i] = 0;
    force[3*i+1] = 0;
    force[3*i+2] = 0;
  }
  // Calculate forces:
  for(i = 0; i < npart-1; i++){
    xi = 3*i;
    yi = 3*i + 1;
    zi = 3*i + 2;
    itype = ptype[i];
    for (j = i + 1; j < npart; j++){
        loc = itype + ntype * ptype[j];
        xj = 3*j;
        yj = 3*j + 1;
        zj = 3*j + 2;
        dx = pos[xi] - pos[xj];
        dy = pos[yi] - pos[yj];
        dz = pos[zi] - pos[zj];
        dx = pbc_dist(dx, box[0], ibox[0]);
        dy = pbc_dist(dy, box[1], ibox[1]);
        dz = pbc_dist(dz, box[2], ibox[2]);
        rsq = dx*dx + dy*dy + dz*dz;
        if (rsq < rcut2[loc]){
            r2inv = 1.0 / rsq;
            r6inv = r2inv*r2inv*r2inv;
            forcelj = r2inv * r6inv * (lj1[loc] * r6inv - lj2[loc]);
            vpot += r6inv * (lj3[loc] * r6inv - lj4[loc]) - offset[loc];
            fx = forcelj * dx;
            fy = forcelj * dy;
            fz = forcelj * dz;
            force[xi] += fx;
            force[yi] += fy;
            force[zi] += fz;
            force[xj] -= fx;
            force[yj] -= fy;
            force[zj] -= fz;
            virial[0] += fx*dx;
            virial[1] += fx*dy;
            virial[2] += fx*dz;
            virial[3] += fy*dx;
            virial[4] += fy*dy;
            virial[5] += fy*dz;
            virial[6] += fz*dx;
            virial[7] += fz*dy;
            virial[8] += fz*dz;
        }
    }
  }
  PyObject *ret = Py_BuildValue("d", vpot);
  return ret;
}
