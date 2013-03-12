from setuptools import setup, find_packages

setup(
    name = 'gtrclient',
    version = '0.0.1',
    packages = find_packages(),
    install_requires = [
        "requests==1.1.0",
        "lxml"
		]
)

