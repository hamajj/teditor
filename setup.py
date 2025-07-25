from setuptools import setup, find_packages

setup(
    name="teditor",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "windows-curses; platform_system=='Windows'",
        "curses; platform_system!='Windows'",
        "Pygments>=2.0.0",
    ],
    entry_points={
        'console_scripts': [
            'teditor = teditor.teditor:cli_main',
        ],
    }
)