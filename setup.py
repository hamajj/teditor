from setuptools import setup, find_packages

setup(
    name="teditor",
    version="0.1",
    packages=find_packages(),
    install_requires=[
    ],
    entry_points={
        'console_scripts': [
            'teditor = teditor.teditor:cli_main',
        ],
    }
)
