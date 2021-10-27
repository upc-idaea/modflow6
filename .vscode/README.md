# Compiling and Visual Debugging with VSCode

VSCode is a free integrated development environment for Windows, Linux, and
MacOS. There are two major advantages over Visual Studio:

* Most of VSCode's source code is open-source and the releases are (proprietary) freeware.
* VSCode runs on Linux.

This folder contains the configuration files for using VSCode for MODFLOW 6 
development.
At the moment they are used for building and debugging MODFLOW 6.
In order to build MODFLOW 6 follow the steps in [DEVELOPER.md](../DEVELOPER.md)

## Visual Studio Code

Install VSCode from https://code.visualstudio.com/

### Extensions

Install the following VSCode extensions:

- Modern Fortran:
  https://marketplace.visualstudio.com/items?itemName=krvajalm.linter-gfortran
- FORTRAN IntelliSense: https://marketplace.visualstudio.com/items?itemName=hansec.fortran-ls
- C/C++: https://marketplace.visualstudio.com/items?itemName=ms-vscode.cpptools
- Fortran Breakpoint Support:
  https://marketplace.visualstudio.com/items?itemName=ekibun.fortranbreaker

Now, configure the VSCode files for the modflow6 directory. Open the `modflow6`
directory in VSCode. Make sure that this setting points toward your Python executable.

```json
{
    "python.defaultInterpreterPath": "/path/to/python",
}
```

In order to compile run:

* Press `Ctrl + Shift + P` in VSCode.
* Type `Tasks`.
* Select `Run Tasks` (press Enter).
* Select the suitable task for your situation.


### Language Server

1. Install the fortran language server via:

```bash
pip install -U fortran-language-server
```

2. Find out where the executable is

- bash: `which fortls`
- cmd: `where fortls`
- PowerShell: `Get-Command fortls`

3. Add this to `.vscode/settings.json`. In case this file does not exist yet, create a new one. Also remember to adapt `fortran-ls.executablePath` to the path you get in the step before.


```json
    "fortran-ls.executablePath": "/path/to/fortls",
    "fortran-ls.hoverSignature": true,
    "fortran-ls.lowercaseIntrinsics": true,
    "fortran-ls.notifyInit": true,
    "fortran-ls.variableHover": true,    
    "fortran.linterEnabled": false,
    "fortran.provideHover": false,
    "fortran.provideCompletion": false,
    "fortran.provideSymbols": false,
    "[FortranFreeForm]": {
        "editor.acceptSuggestionOnEnter": "off",
    },
```



### Debugging

Add a `launch.json` in `.vscode` similar to this.

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Launch Modflow Model",
            "type": "cppdbg",
            "request": "launch",
            "program": "${workspaceFolder}/bin/mf6.exe",
            "args": [],
            "stopAtEntry": false,
            "cwd": "/path/to/modflow6/model",
            "environment": [],
            "externalConsole": false,
            "MIMode": "gdb",
            "miDebuggerPath": "/path/to/gdb.exe",
            "setupCommands": [
                {
                    "description": "Enable pretty-printing for gdb",
                    "text": "-enable-pretty-printing",
                    "ignoreFailures": true
                }
            ]
        }
    ]
}
````

Also remember to adapt the following two lines in `launch.json` according to your setup:

```json
"cwd": "/path/to/your/modflow6/model",
```

```json
"miDebuggerPath": "/path/to/gdb",
```

After building modflow, you can start debugging.

- Set a breakpoint somewhere in the source code.
- Press `Ctrl + F5` to start debugging.
