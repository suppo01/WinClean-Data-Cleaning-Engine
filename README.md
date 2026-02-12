# WinClean: A python Data Cleaning Engine for Windows

WinClean is a Python based Data Cleaning Engine for Windows with a focus on Windows path command errors.

## Project Overview

WinClean uses both static and dynamic analysis to detect Windows path bugs, cleans the data by fixing the bug, and send the
user feedback about what went wrong, all without the user experiencing a crash in the first place. The eventual idea would be
that WinClean is automatically passed all path commands and analyzes them for possible bugs ahead of time.

This project will use the python Abstract Syntax Tree package to conduct static analysis and python's venv setup to conduct
dynamic analysis. Having both static and dynamic analysis allows for an option that is more efficient, static analysis, and an
option that is more accurate, dynamic analysis. Using a venv setup allows for the code to be run without possibly doing
irreversible damage to the file system.

For the data cleaning aspect of this project, WinClean will use a machine learning approach. This allows for more versatilty as
newer bugs become known as there are constantly new bugs being discovered. The hope is to look at integrating ai or something
similar into the repo for the tool and to train it to take the found bugs and fix them correctly. After fixing the bug,
WinClean will pass the cleaned version back out and print out a feedback message with what was wrong with the original command
and how to fix it.

## Research Context

The context for the research and creation of WinClean is that Windows path commands are very distinct and different from Mac
and Linux commands. In addition, in the computer science department at Allegheny College, there are not many Windows users
among students who are knowledgable, or have been in the department long enough to learn the correct procedures for doing basic
things with github and traversing file systems. With this, the faculty members usually lean towards Mac or Linux systems, so a
lot of being a Windows user on campus becomes learning as you go and always looking things up.

I have a passion for computer science and have been helping out in the department as a Technical Leader, or TL. I would love to
help Windows people learn and find a passion for coding and computer science, but I am one person with a finite amount of time.
With a tool like WinClean, students can learn from their mistakes without causing crashes in their file systems from incorrect
path commands and improve for next time.

## Installation

To install WinClean first clone the repository code using your terminal of choice. Then, make sure you have pip or uv
installed. Finally, get into the WinClean directory and use the corresponding command to install the WinClean package for the
cli functionality.

``` cmd
- For uv Users: uv install .
- For pip Users: pip install .
```

## Tool Usage

WinClean is intended to be used with the intention of having an educational purpose and is geared toward mainly beginners in
the computer science industry that may be new to navigating file systems and would thus benefit from the feedback WinClean will
provide.

### CLI Usage Hints and Examples

The command should look like this:

``` cmd
winclean --mode [enter mode here] --script-path or --path-command [enter path or command here in quotes] -- venv [enter
desired venv path here]
```

#### Mode Flag

The mode can either be static or dynamic representing either static or synamic analysis.

``` cmd
- --mode static
- --mode dynamic
```

#### Script Path and Path Command Flags

The next flag can either be for a script path or an individual path command. A script path is used when you want to pass a
whole python file to WinClean. A path command is used when you want to look at an individual command. Either command can be
used with static and dynamic modes of analysis.

``` cmd
- --script-path "test_suite\runtime_path_test.py"
- --path_command "cd \Users\a\github"
```

#### Venv Flag

The venv flag is only used when the mode flag is being called as dynamic. It can be an existing vitual environment you would
like to use, or you can provide a name to use for the creation of a new virtual environment. If an existing virtual environment
setup is being used, the full path to the virtual environment will need to be provided.

``` cmd
- --venv "\Users\a\github\old_venv"
- --venv "my_venv"
```
