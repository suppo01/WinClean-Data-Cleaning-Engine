# setup.py
from setuptools import setup, find_packages

setup(
    name="winclean",
    version="0.1.0",
    description="Windows Path Cleaning Engine",
    py_modules=["main", "detect_static_analysis", "detect_dynamic_analysis", "OpenCode_runner", "symbolic_class"],
    entry_points={
        "console_scripts": [
            "winclean=main:main",
        ],
    },
)
