Contributing
============

Thank you for making this project better!

Development Setup
-----------------

1. Fork the repository
2. Clone your fork::

    git clone https://github.com/your-username/sdiff.git
    cd sdiff

3. Create a virtual environment and activate it::

    python -m venv venv
    source venv/bin/activate

4. Install development dependencies::

    pip install -e ".[dev]"

Development Process
-------------------

1. Create a new branch for your feature or bugfix::

    git checkout -b feature-name

2. Make your changes
3. Write or update tests if necessary
4. Run tests::

    pytest

Making a Pull Request
---------------------

1. Push your changes to your fork::

    git push origin feature-name

2. Go to the original repository and create a Pull Request
3. Describe your changes in detail
4. Reference any related issues

Code Style
----------

- Please be reasonable about the code style
- Use meaningful variable and function names
- Add docstrings for functions and classes
- Keep functions and methods focused and concise
- Write descriptive commit messages

Documentation
-------------

To build the documentation locally::

    cd docs
    make html

The built documentation will be in ``docs/build/html``.

Questions or Problems?
----------------------

If you have questions or problems, please:

1. Check existing issues
2. Create a new issue with a descriptive title
3. Provide as much relevant information as possible

Thank you for your contribution!