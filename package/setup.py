from setuptools import *

long_description = """
A sacred `RunObserver` which uses `visdom` to plot logged metrics and image artifacts. Supports creation
of dynamically updating plots with different sets of metrics easily.
"""

setup(name='visdom_observer',
		version='0.2',
		description='A sacred `RunObserver` which uses visdom to plot metrics and artifacts',
		long_description=long_description,
		author='Rajat Vadiraj Dwaraknath',
		url='https://github.com/rajatvd/VisdomObserver',
		install_requires=['sacred', 'visdom'],
		author_email='rajatvd@gmail.com',
		license='MIT',
		packages=['visdom_observer'],
		zip_safe=False)