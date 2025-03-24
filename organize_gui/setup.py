#!/usr/bin/env python3
"""
Setup script for the File Organization System frontend.
"""

from setuptools import setup, find_packages

setup(
    name="organize-gui",
    version="1.0.0",
    description="GUI frontend for the organize-tool file organization system",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "pyyaml>=6.0",
        "organize-tool>=2.4.0",
    ],
    entry_points={
        'console_scripts': [
            'organize-gui=organize_gui.app:main',
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Desktop Environment :: File Managers",
        "Topic :: Utilities",
    ],
    python_requires=">=3.6",
)