CONTRIBUTING
============

First of all, thank you very much for contributing to this project. Please base
your work on the ``master`` branch and target ``master`` in your pull request.

Tools
-----
We are currently evaluating the upcoming `Pipfile`_ standard and for that employ `pipenv`_ .
The assumption is that you have `pipenv` installed as a user installation (`pip install --user pipenv`). If
you are not familiar with `pipenv`, you can view a solid introduction on why `requirements.txt` no longer suffices in
 the python packaging community in `this video`_.

Pep8 compliance
---------------
Where possible we adhere to pep8, and a max McCabe complexity of 5. The tool `flake8`_ will help you accomplish this.


.. _Pipfile: https://github.com/pypa/pipfile
.. _pipenv: https://github.com/pypa/pipfile
.. _tox plugin: https://github.com/tox-dev/tox-pipenv
.. _this video: https://www.youtube.com/watch?v=GBQAKldqgZs
.. _flake8: http://flake8.pycqa.org/en/latest/
