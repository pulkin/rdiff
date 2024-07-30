import setuptools
from Cython.Build import cythonize

setuptools.setup(
    packages=["rdiff"],
    ext_modules=cythonize(
        [
            setuptools.Extension(
                "*",
                ["rdiff/cmyers.pyx"],
                language="c",
            )
        ],
        annotate=True,
    ),
)
