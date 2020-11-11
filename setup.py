import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="placekey",
    version="0.0.6",
    author="SafeGraph Inc.",
    author_email="russ@safegraph.com",
    description="Utilities for working with Placekeys",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Placekey/placekey-py",
    packages=setuptools.find_packages(),
    install_requires=['h3', 'shapely', 'requests', 'ratelimit', 'backoff'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
