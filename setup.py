from setuptools import setup, find_packages
import os
import sys


with open('README.rst') as fp:
    long_description = fp.read()


local_ctx = {}
with open('src/when/__init__.py') as fp:
    exec(fp.read(), {}, local_ctx)


setup(
    name='when',
    version=local_ctx['VERSION'],
    description=local_ctx['__doc__'],
    license='MIT',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author='David Krauth',
    author_email='dakrauth@gmail.com',
    url='https://github.com/dakrauth/when',
    python_requires='>=3.6,<4',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    entry_points={'console_scripts': ['when = when.__main__:main',]},
    install_requires=['python-dateutil>=2.8.0', 'pytz>=2018.9'],
    classifiers=[
        'Development Status :: 1 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Software Distribution',
        'Topic :: Utilities',
    ],
    zip_safe=False,
)
