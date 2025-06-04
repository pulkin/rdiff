import setuptools
from Cython.Build import cythonize

setuptools.setup(
    packages=setuptools.find_namespace_packages(),
    ext_modules=cythonize(
        [
            setuptools.Extension(
                "rdiff.cmyers",
                ["rdiff/cython/cmyers.pyx", "rdiff/cython/compare.pyx"],
                language="c",
            )
        ],
        annotate=True,
    ),
    include_package_data=True,
)
