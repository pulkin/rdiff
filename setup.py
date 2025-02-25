import setuptools
from Cython.Build import cythonize

setuptools.setup(
    packages=setuptools.find_namespace_packages(),
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
