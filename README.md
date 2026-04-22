# WinClean: A python Data Cleaning Engine for Windows

WinClean is a Python based Data Cleaning Engine for Windows with a focus on Windows file path command errors.

**Feel free to take WinClean for a test run!**
However, please do not make changes directly to this repository.

## Project Overview

WinClean uses both static and dynamic analysis to detect Windows path bugs, and cleans the data by fixing the bug, all without the user experiencing a crash in the first place. The idea is eventually that WinClean is automatically passed all path commands and analyzes them for possible bugs ahead of time.

This project uses the python Abstract Syntax Tree package and Z3, an SMT solver, to conduct static analysis. The Z3 SMT solver
is only used when a python code file is dynamically building Windows file paths throughout a program, rather than hard-coding
it. For all other cases, the Python Abstract Syntax Tree with a series of well-defined rules based on the constraints of the\
Windows file path design, is used. WinClean also uses Python's venv setup to conduct dynamic analysis. Having both static and
dynamic analysis allows for an option that is more efficient, static analysis, and an option that is more accurate, dynamic
analysis. Using a venv setup allows for the code to be run without possibly doing irreversible damage to the file system.
Please note that the Z3 SMT solver is only able to guess at what may be a dangerous path when any form of user-driven input is
involved as it is not running the code in real time.

For the data cleaning aspect of this project, WinClean uses an ACP approach in conjunctions with the OpenCode AI server. This
allows for more versatilty as newer bugs become known as there are constantly new bugs being discovered. By connecting with
ACP, I am able to communicate programatically with the OpenCode AI server and pass it a prompt containing broken code, analysis
results, and a clear description of the information I would like to recieve back. I am also able to engage in an iterative
querying with few shot approach that allows the server to iterate on the prompt a few times before giving backa clean command.
This allows for hopefully improved learning as well as a higher chance of a truly clean command the first time. After fixing
the bug, WinClean passes the cleanest version it has back out and the corrected path is printed to the terminal.

**Please Note:** WinClean is still in development and will be experiencing various changes and big feature additons to improve
the tool and the experince of its users. The refinement of WinClean's prompt that is sent to OpenCode's AI server via ACP and
other bug fixes are on the list to fix and update as WinClean's concept becomes a reality.

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

This command connects with the setup script that will install all dependencies for the cli functionality and WinClean as a
whole.

## Tool Usage

WinClean is intended to be used with the intention of having an educational purpose and is geared toward mainly beginners in
the computer science industry that may be new to navigating file systems and would thus benefit from the feedback WinClean will
provide. WinClean is also based in Windows file path command errors, so its primary use is for Windows users, though those
hoping to develop for Windows may also find the tool helpful for their needs.

### CLI Usage Hints and Examples

The command should look like this:

``` cmd
winclean --mode [enter mode here] --script-path or --path-command [enter path or command here in quotes] -- venv [enter
desired venv path here]
```

A real-world example of the WinClean command for static analysis on a file path command would look like this:

``` cmd
winclean --mode static --path-command "cd C:\github\TL_Stuff"
```

The path-command flag is used because there is a file path command being passed as the input to clean, and the mode is static
because WinClean will be asked to perform static analysis on the file path command.

Another real-world example of the WinClean command for dynamic analysis on a Python code file would look like this:

``` cmd
winclean --mode dynamic --script-path "test_suite\test_path_dynamic.py" --venv "my_venv"
```

The script-path flag is used because there is a path to a Python code file being passed so WinClean knows where to find the
file it needs to clean, and the mode is dyanmic because WinClean will be asked to perform dynamic analysis on the Python code
file found at the path provided. There is also the addition of the venv flag to give a name the user would like WinClean to use
for the virtual environment for dynamic analysis. This can be either an existing or new environment, this example sjhows the
set up for a new environment, providing only a name as a string.

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
- --script-path "test_suite\test_path_dynamic.py"
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
