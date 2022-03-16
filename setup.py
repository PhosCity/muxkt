from setuptools import setup

with open("README.md") as readme_file:
    readme = readme_file.read()

setup(
    name="muxkt",
    description="Wrapper for SubKt written in Python",
    version="0.1.4",
    py_modules=["muxkt"],
    install_requires=["Click", "colorama", "iterfzf"],
    entry_points="""
        [console_scripts]
        muxkt=muxkt.cli:main
    """,
    author="PhosCity",
    author_email="phoscity2@gmail.com",
    python_requires=">=3.6",
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    license="GNU General Public License v3",
    long_description=readme,
    long_description_content_type="text/markdown",
    keywords=["muxkt", "subkt", "SubKt"],
    url="https://github.com/PhosCity/muxkt",
)
