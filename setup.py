from setuptools import setup, find_packages
from muxkt.helpers.__version__ import VERSION

requirements = ["click", "colorama", "iterfzf"]

setup(
    name="muxkt",
    version=VERSION,
    author="PhosCity",
    author_email="phoscity2@gmail.com",
    description="Wrapper for SubKt written in python",
    packages=find_packages(),
    url="https://github.com/PhosCity/muxkt",
    keywords=["muxkt", "subkt", "SubKt"],
    install_requires=requirements,
    entry_points="""
        [console_scripts]
        muxkt=muxkt.main:cli
    """,
    license="GNU General Public License v3",
)
