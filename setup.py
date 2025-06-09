from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension(
        name="sdiff.cython.compare",
        sources=["sdiff/cython/compare.pyx"],
        include_dirs=["sdiff/cython"],  # Allow cimport to find .pxd files
    ),
    Extension(
        name="sdiff.cython.cmyers",
        sources=["sdiff/cython/cmyers.pyx"],
        include_dirs=["sdiff/cython"],  # Allow cimport to find .pxd files
    )
]

setup(
    name="sdiff",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            'language_level': 3,
        },
        include_path=["sdiff/cython"],
        annotate=True,
    ),
    packages=["sdiff"],
    zip_safe=False,
    include_package_data=True,
)
