# WinClean: A python Data Cleaning Engine for Windows
WinClean is a Python based Data Cleaning Engine for Windows with a focus on Windows path command errors.

## Project Overview
WinClean uses both static and dynamic analysis to detect Windows path bugs, cleans the data by fixing the bug, and send the user feedback about what went wrong, all without the user experiencing a crash in the
first place. The eventual idea would be that WinClean is automatically passed all path commands and analyzes them for possible bugs ahead of time.

This project will use the python Abstract Syntax Tree package to conduct static analysis and python's venv setup to conduct dynamic analysis. Having both static and dynamic analysis allows for an option that is
more efficient, static analysis, and an option that is more accurate, dynamic analysis. Using a venv setup allows for the code to be run without possibly doing irreversible damage to the file system.

For the data cleaning aspect of this project, WinClean will use a machine learning approach. This allows for more versatilty as newer bugs become known as there are constantly new bugs being discovered. The hope is
to look at integrating ai or something similar into the repo for the tool.

## Research Context

## Installation

## Tool Usage
