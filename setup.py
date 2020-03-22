from setuptools import setup, find_packages

setup(
    name="jdb",
    version="0.0.1",
    description="jdb",
    author="thejchap",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "black==19.10b0",
        "flake8==3.7.9",
        "mypy==0.770",
        "pytest==5.3.5",
        "uvarint==v1.2.0",
    ],
)
