# Explicitly Versioned Python
This folder sets up a `explict_python` target, which lets you link against an explicitly specified
(Windows) Python version. `FindPython` is generally not suitable for what we do, since it picks an
arbitrary version on your system, which may not even be the right architecture, and it picks a host
version if cross compiling. This target also adds install rules for the `.dll`s, `.pyd`s, and
`.zip`s which are needed at runtime when running an embedded intepreter.

The simplest way to use this is just to set `EXPLICT_PYTHON_VERSION` to the relevant version, and
`EXPLICT_PYTHON_ARCH` to one of `win32` or `amd64`, before including this folder in CMake.
This requires Python with `requests` to be on your PATH, and, if not running on Windows,
`msiextract` (typically part of an `msitools` package).

When setting the above variables, CMake will automatically run `download.py`. You can instead run it
yourself, and point `EXPLICIT_PYTHON_DIR` at the folder you downloaded. You can also set this as an
enviroment variable, which can be useful if caching it in a container.

The final way to use this is to point `EXPLICIT_PYTHON_DIR` at a standard Windows Python install.
This of course requires you install the development version. Windows installs do not normally come
with a `python3<version>.zip` standard library zip. This is not required to compile, and won't throw
an error, but is needed at runtime. There are three ways you can get it:
- Just zip the `Lib` up folder, and rename it.
- Download the python embeddable package for the same version, and copy the zip from there. This
  version contains precompiled bytecode instead of raw source files. This is what the `download.py`
  script does.
- Create your own compiled zip using `zipfile.PyZipFile`. You have to make sure to do this with the
  exact same Python version.
