# flake8: noqa
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ''

    def run_tests(self):
        # Import here, cause outside the eggs aren't loaded
        import shlex
        import pytest
        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


setup(
    name="unide-python",
    version=open("VERSION").readline()[:-1],
    description="An API for PPMP, the Production Performance Management Protocol",
    license="Eclipe Public License",
    zip_safe=True,
    long_description=open("README.rst").read(),
    author="Contact Software",
    author_email="unide@contact-software.com",
    url="https://github.com/eclipse/unide.python",
    keywords='PPMP IoT Unide Eclipse',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Communications',
        'Topic :: Internet',
    ],
    package_dir={"": "src"},
    packages=find_packages("src"),
    install_requires=[
        "python-dateutil",
    ],
    tests_require=["pytest"],
    cmdclass={'test': PyTest},
)
