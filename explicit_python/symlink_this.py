import platform
import sys
from pathlib import Path


def main() -> None:
    """Main entry point."""
    if platform.system() != "Windows":
        raise RuntimeError(
            "This script only works on Windows, due to assumptions about the install layout.",
        )

    this_dir = Path(__file__).resolve().parent

    # Recommended over `platform.architecture()[0] == "64bit"`
    is_64_bit = sys.maxsize > 2**32

    dest = this_dir / ("x64" if is_64_bit else "x86")

    # This is what won't work cross platform
    # On Windows, the include and lib dirs both just exist in the same dir as the executable

    # It's trivial enough to find the include dir, `sysconfig.get_path("include")`
    # The static libs are more difficult - and given we're only building against Windows for now
    #  anyway, not going to put in the effort to work it out yet
    py_install_dir = Path(sys.executable).parent

    if dest.exists():
        dest.rmdir()
    dest.symlink_to(py_install_dir, True)


if __name__ == "__main__":
    main()
