from setuptools import setup, Extension, find_namespace_packages
from Cython.Build import cythonize

extensions = [
    Extension(
        name="rdiff.cython.compare",
        sources=["rdiff/cython/compare.pyx"],
        include_dirs=["rdiff/cython"],  # Allow cimport to find .pxd files
    ),
    Extension(
        name="rdiff.cython.cmyers",
        sources=["rdiff/cython/cmyers.pyx"],
        include_dirs=["rdiff/cython"],  # Allow cimport to find .pxd files
    )
]

setup(
    name="rdiff",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            'language_level': 3,
        },
        include_path=["rdiff/cython"],
        annotate=True,
    ),
    packages=find_namespace_packages(),
    zip_safe=False,
    include_package_data=True,
)
