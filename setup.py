import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand

if sys.version_info < (3, 4):
    sys.stderr.write(
        'Got python:' + sys.version + '\n'
        'Required python>=3.4\n'
    )
    exit(1)


P = __import__('sbs')


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import pytest here: tests_require makes it available only on test run
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name='sbs',
    version=P.__versionstr__,
    description="Sainsbury's dummy spider",
    keywords='sainsburys dummy spider',
    author='lukmdo',
    author_email='me@glukmdo.com',
    url='https://github.com/lukmdo/sbs',
    license='MIT',
    py_modules=['sbs'],
    scripts=["sbs.py"],
    zip_safe=False,
    install_requires=['lxml', 'requests'],
    tests_require=["pytest"],
    cmdclass={'test': PyTest},
    classifiers=[
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
