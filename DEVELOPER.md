# Building and Testing MODFLOW 6

This document describes how to set up your development environment to build and test MODFLOW 6.
It also explains the basic mechanics of using `git`.

* [Prerequisite Software](#prerequisite-software)
* [Getting the Sources](#getting-the-sources)
* [Installing NPM Modules](#installing-npm-modules)
* [Building](#building)
* [Running Tests Locally](#running-tests-locally)

See the [contribution guidelines](https://github.com/MODFLOW-USGS/modflow6/blob/develop/CONTRIBUTING.md)
if you'd like to contribute to MODFLOW 6.

## Prerequisite Software

Before you can build and test MODFLOW 6, you must install and configure the
following products on your development machine.

### Git

[Git](https://git-scm.com) and/or the **GitHub app** (for [Mac](https://mac.github.com) or [Windows](https://windows.github.com)).
[GitHub's Guide to Installing Git](https://help.github.com/articles/set-up-git) is a good source of information.


### gfortran (version 4.9 to 10)

gfortran can be used to compile MODFLOW 6 and associated utilities and generate distributable files.

#### Linux

- fedora-based: `dnf install gcc-gfortran`
- debian-based: `apt install gfortran`

#### macOS

- [Homebrew](https://brew.sh/): `brew install gcc`
- [MacPorts](https://www.macports.org/): `sudo port install gcc10`

#### Windows

- Download the Minimalist GNU for Windows (MinGW) installer from Source Forge:
  https://sourceforge.net/projects/mingw-w64/files/Toolchains%20targetting%20Win32/Personal%20Builds/mingw-builds/installer/mingw-w64-install.exe
- Run the installer. Make sure to change `Architecture` to `x86_64`. Leave the
  other settings on default.
- Find the `mingw64/bin` directory in the installation and add it
  to your PATH. Find `Edit the system environment variables` in your Windows
  Start Screen. Click the `Environmental Variables` button and double-click the
  `Path` variable in the User Variables (the top table). Click the `New` button
  and enter the location of the `mingw64/bin` directory.


### Python

Install Python, for example via [miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/products/individual).
Please make sure that your Python version is 3.7 or higher.
Then install all packages necessary to run the tests either by executing [install-python-std.sh](.github/common/install-python-std.sh) via bash directly or by installing the listed packages manually.

### ifort (optional)

Intel fortran can be used to compile MODFLOW 6 and associated utilities and generate distributable files (if not using gfortran).
Download the Intel oneAPI HPC Toolkit: https://software.intel.com/content/www/us/en/develop/tools/oneapi/hpc-toolkit/download.html

### LaTeX (optional)

[LaTeX](https://www.latex-project.org/) which is used to generate the MODFLOW 6 release notes and Input/Output documents (docs/mf6io/mf6io.nightlybuild).

## Getting the Sources

Fork and clone the MODFLOW 6 repository:

1. Login to your GitHub account or create one by following the instructions given
   [here](https://github.com/signup/free).
2. [Fork](http://help.github.com/forking) the [main MODFLOW 6](https://github.com/MODFLOW-USGS/modflow6).
3. Clone your fork of the MODFLOW 6 repository and define an `upstream` remote pointing back to the MODFLOW 6 repository that you forked in the first place.

```shell
# Clone your GitHub repository:
git clone git@github.com:<github username>/modflow6.git

# Go to the MODFLOW 6 directory:
cd modflow6

# Add the main MODFLOW 6 repository as an upstream remote to your repository:
git remote add upstream https://github.com/MODFLOW-USGS/modflow6.git
```

## Building

### Meson

First, install [Meson](https://mesonbuild.com/Getting-meson.html) and assure it is in your [PATH](https://en.wikipedia.org/wiki/PATH_(variable)).
When using Visual Studio Code, you can use tasks as described [here](.vscode/README.md).
For the more general instructions, continue to read this section.

First configure the build directory.
Per default it uses the compiler flags for a release build.
If you want to create a debug build, add `-Doptimization=0` to the following `setup` command.

```shell
# bash (linux and macOS)
meson setup builddir --prefix=$(pwd) --libdir=bin

# cmd (windows)
meson setup builddir --prefix=%CD% --libdir=bin
```

Compile MODFLOW 6 by executing:

```shell
meson compile -C builddir
```

In order to run the tests the binaries have to be installed:

```shell
meson install -C builddir
```

The binaries can then be found in the `bin` folder.
`meson install` also triggers a compilation if necessary.
Therefore, executing `meson install` is enough to get up-to-date binaries in the `bin` folder.

### Visual Studio

As of October 2021, debugging with Visual Studio tends to be more convenient than with other solutions.
First, download Visual Studio from the [official website](https://visualstudio.microsoft.com/).
The solution files can be found in the `msvs` folder.

### Pymake

Follow the installation instructions as explained on the README of the [repository](https://github.com/modflowpy/pymake).
The README also explains how to build MODFLOW 6 with it.

### Make

We also provide make files which can be used to build MODFLOW 6 with [GNU Make](https://www.gnu.org/software/make/).
For the build instructions we refer to the [GNU Make Manual](https://www.gnu.org/software/make/manual/).


## Running Tests Locally

For complete testing as done on the CI, clone the modflow6-testmodels repository:

```shell
# Clone your GitHub repository:
git clone git@github.com:<github username>/modflow6-testmodels.git
```
* The modflow6-testmodels repository must be cloned in the same directory that contains the modflow6 repository.

To run tests first change directory to the `autotest` folder:

```shell
cd modflow6/autotest
```

Update your flopy installation by executing

```shell
python update_flopy.py
```

The tests require other MODFLOW-related binary executables, distributed from https://github.com/MODFLOW-USGS/executables.
Testing also requires a binary executable of the last MODFLOW 6 officially released version, compiled in develop mode with the currently configured compiler. To download MODFLOW-related binaries and to rebuild the last official MODFLOW 6 release, execute:

```shell
pytest -v get_exes.py
```

Unless you built and installed MODFLOW 6 binaries with meson, you will also have to execute the following command to build the binaries:

```shell
pytest -v build_exes.py
```

Then the tests can be run with commands similar to these:

```shell
# Build MODFLOW 6 tests
pytest -v

# Build MODFLOW 6 example tests
pytest -v test_z01_testmodels_mf6.py

# Build MODFLOW 5 to 6 converter example tests
pytest -v test_z02_testmodels_mf5to6.py
```

By adding the flag "-n" the tests can even be run in parallel:

```shell
pytest -v -n auto
```


You should execute the test suites before submitting a PR to Github.
All the tests are executed on our Continuous Integration infrastructure and a pull request can only be merged once all tests pass.
