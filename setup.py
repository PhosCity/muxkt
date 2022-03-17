from setuptools import setup, find_packages
from muxkt.helpers.__version__ import VERSION

setup(
    name="muxkt",
    version=VERSION,
    author="PhosCiry",
    author_email="phoscity2@gmail.com",
    description="Wrapper for SubKt written in python",
    packages=find_packages(),
    url="https://github.com/PhosCity/muxkt",
    keywords=["muxkt", "subkt", "SubKt"],
    install_requires=[
        "click",
        "iterfzf",
        "colorama",
    ],
    entry_points="""
        [console_scripts]
        muxkt=muxkt.main:cli
    """,
)
