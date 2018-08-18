from setuptools import *

long_description = """
A sacred `RunObserver` which uses visdom to plot logged metrics and image artifacts. Supports easy creation
of plots with particular subsets of the logged metrics.
"""

setup(name='visdom_observer',
		version='0.1',
		description='A sacred `RunObserver` which uses visdom to plot metrics and artifacts',
		long_description=long_description,
		author='Rajat Vadiraj Dwaraknath',
		url='https://github.com/rajatvd/VisdomObserver',
		install_requires=['sacred'],
		author_email='rajatvd@gmail.com',
		license='MIT',
		packages=find_packages(),
		zip_safe=False)