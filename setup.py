import setuptools

with open("README.md","r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="RedBlobGreenBlob",
    version="0.0.1",
    install_requires=["pygame>=2.0.0"],
    author="Ross Watts",
    description="A platformer game - the sequel to RetroParkourer.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Ross-TheBoss/RedBlobGreenBlob",
    packages=setuptools.find_packages(),
    package_data={"RedBlobGreenBlob":["images/*.png",
                                      "levels/*.txt",
                                      "sounds/*.ogg",
                                      "*.ini",
                                     "*.csv"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 3 - Alpha",
        "Topic :: Games/Entertainment :: Side-Scrolling/Arcade Games",
        "Topic :: Software Development :: Libraries :: pygame",
    ],
    python_requires=">=3.7",
)
