# cython: language_level=3
import numpy as np
from cpython.ref cimport PyObject
from cpython.mem cimport PyMem_Malloc, PyMem_Free
import array
import cython
from warnings import warn

try:
    import numpy
except ImportError:
    numpy_avail = False
else:
    numpy_avail = True


cdef double compare_call(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra):
    return (<object>a)(i, j)


cdef double compare_str(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra):
    return (<unicode>a)[i] == (<unicode>b)[j]


cdef double compare_array_8(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra):
    return (<char*>a)[i] == (<char*>b)[j]


cdef double compare_array_8_ext_2d(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra):
    cdef:
        Py_ssize_t t
        double r = 0
    for t in range(n):
        r += ((<char*>a)[i * n + t] == (<char*>b)[j * n + t]) * (1 if extra == cython.NULL else (<double*>extra)[t])
    return r / n


cdef double compare_array_16(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra):
    return (<short*>a)[i] == (<short*>b)[j]


cdef double compare_array_16_ext_2d(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra):
    cdef:
        Py_ssize_t t
        double r = 0
    for t in range(n):
        r += ((<short*>a)[i * n + t] == (<short*>b)[j * n + t]) * (1 if extra == cython.NULL else (<double*>extra)[t])
    return r / n


cdef double compare_array_32(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra):
    return (<int*>a)[i] == (<int*>b)[j]


cdef double compare_array_32_ext_2d(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra):
    cdef:
        Py_ssize_t t
        double r = 0
    for t in range(n):
        r += ((<int*>a)[i * n + t] == (<int*>b)[j * n + t]) * (1 if extra == cython.NULL else (<double*>extra)[t])
    return r / n


cdef double compare_array_64(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra):
    return (<long*>a)[i] == (<long*>b)[j]


cdef double compare_array_64_ext_2d(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra):
    cdef:
        Py_ssize_t t
        double r = 0
    for t in range(n):
        r += ((<long*>a)[i * n + t] == (<long*>b)[j * n + t]) * (1. if extra == cython.NULL else (<double*>extra)[t])
    return r / n


cdef double compare_array_128(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra):
    return (<long long*>a)[i] == (<long long*>b)[j]


cdef double compare_array_128_ext_2d(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra):
    cdef:
        Py_ssize_t t
        double r = 0
    for t in range(n):
        r += ((<long long*>a)[i * n + t] == (<long long*>b)[j * n + t]) * (1 if extra == cython.NULL else (<double*>extra)[t])
    return r / n


cdef double compare_array_var(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra):
    cdef:
        Py_ssize_t t
    a += i * n
    b += j * n
    for t in range(n):
        if (<char*>a)[t] != (<char*>b)[t]:
            return 0
    return 1


cdef double compare_object(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra):
    return (<object>a)[i] == (<object>b)[j]


# cdef double ratio(void* a, void* b, char* protocol, double* weights):
#     cdef:
#         double result = 0
#         double weight
#         Py_ssize_t i = 0
#         char code
#
#     if protocol.code == b'U':
#         return ((<unicode> protocol.a)[i] == (<unicode> protocol.b)[j]) * protocol.weight[0]
#
#     for i in range(protocol.n):
#         code = protocol.code[i]
#         if i == b'c':
#             weight = (<char> a_) == (<char> b_)
#             a_ += sizeof(char)
#             b_ += sizeof(char)
#         elif i == b'h':
#             weight = (<short> a_) == (<short> b_)
#             a_ += sizeof(short)
#             b_ += sizeof(short)
#         elif i == b'i':
#             weight = (<int> a_) == (<int> b_)
#             a_ += sizeof(int)
#             b_ += sizeof(int)
#         elif i == b'f':
#             weight = (<long> a_) == (<long> b_)
#             a_ += sizeof(long)
#             b_ += sizeof(long)
#         elif i == b'l':
#             weight = (<long long> a_) == (<long long> b_)
#             a_ += sizeof(long long)
#             b_ += sizeof(long long)
#         elif i == b'f':
#             weight = (<float> a_) == (<float> b_)
#             a_ += sizeof(float)
#             b_ += sizeof(float)
#         elif i == b'd':
#             weight = (<double> a_) == (<double> b_)
#             a_ += sizeof(double)
#             b_ += sizeof(double)
#         else:
#             raise ValueError(f"unknown code: {i}")
#         result += weight * protocol.weight[i]
#     return result
