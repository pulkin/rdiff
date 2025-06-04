ctypedef double (*compare_type)(void*, void*, Py_ssize_t, Py_ssize_t, Py_ssize_t, void*)
cdef struct compare_protocol:
    compare_type kernel
    void* a
    void* b
    Py_ssize_t n
    void* extra


cdef double compare_call(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra)
cdef double compare_str(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra)
cdef double compare_object(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra)

cdef double compare_array_8(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra)
cdef double compare_array_8_ext_2d(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra)
cdef double compare_array_16(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra)
cdef double compare_array_16_ext_2d(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra)
cdef double compare_array_32(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra)
cdef double compare_array_32_ext_2d(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra)
cdef double compare_array_64(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra)
cdef double compare_array_64_ext_2d(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra)
cdef double compare_array_128(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra)
cdef double compare_array_128_ext_2d(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra)
cdef double compare_array_var(void* a, void* b, Py_ssize_t i, Py_ssize_t j, Py_ssize_t n, void* extra)
