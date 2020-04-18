from setuptools import setup

setup(
    name="jdb",
    version="0.0.1",
    description="jdb",
    author="thejchap",
    packages=["jdb"],
    install_requires=[
        "black",
        "pylint",
        "flake8",
        "mypy",
        "pytest",
        "uvarint",
        "lz4tools",
        "python-snappy",
        "xxhash",
        "structlog",
        "colorama",
    ],
)
