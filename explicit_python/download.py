#!/usr/bin/env python3
import argparse
import platform
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

import requests

__all__: tuple[str, ...] = (
    "get_default_download_dir",
    "download",
    "ArchInfo",
    "ARCHITECTURES",
)


@dataclass
class ArchInfo:
    py_name: str
    folder_name: str


ARCHITECTURES: tuple[ArchInfo, ...] = (
    ArchInfo("win32", "x86"),
    ArchInfo("amd64", "x64"),
)


def get_default_download_dir(arch: ArchInfo) -> Path:
    """
    Gets the default download directory for the given architecture.

    Returns:
        The download directory.
    """
    return Path(__file__).resolve().parent / arch.folder_name


def download_file(url: str, path: Path) -> None:
    """
    Downloads a url to disk.

    Args:
        url: The url to download.
        path: The path to download to.
    """
    with requests.get(url, stream=True) as resp, path.open("wb") as file:
        resp.raw.decode_content = True
        shutil.copyfileobj(resp.raw, file)


def extract_msi(msi: Path, extract_dir: Path) -> None:
    """
    Extracts all the files installed in an msi.

    Args:
        msi: The msi to extract.
        extract_dir: The directory to extract into.
    """
    if platform.system() == "Windows":
        # msiexec doesn't like extracting to the same dir the file is in, so extract to a temp dir
        with tempfile.TemporaryDirectory() as tmp_dir:
            ret = subprocess.run(["msiexec", f"TARGETDIR={tmp_dir}", "/a", str(msi), "/qn"])
            if ret.returncode == 2203:
                print("Do you have permission to write to the output dir?")
            ret.check_returncode()

            # When using /a, msiexec also adds an extracted msi which we don't want
            for extracted_msi in Path(tmp_dir).rglob("*.msi"):
                extracted_msi.unlink()

            shutil.copytree(tmp_dir, extract_dir, dirs_exist_ok=True)
    else:
        subprocess.run(
            ["msiextract", "-C", str(extract_dir), str(msi)],
            check=True,
            stdout=subprocess.DEVNULL,
        )


def download_stdlib_zip(version: str, arch: ArchInfo, download_dir: Path) -> None:
    """
    Downloads the embedded standard library zip for the given version/arch.

    We can't compile it ourselves as the python we're running in may not be the same as what we're
    downloading.

    Args:
        version: The version to download.
        arch: The architecture to download.
        download_dir: The directory to download into.
    """

    embed_url_base = f"https://www.python.org/ftp/python/{version}/"
    embed_name = f"python-{version}-embed-{arch.py_name}.zip"

    embed_download_path = download_dir / embed_name
    download_file(embed_url_base + embed_name, embed_download_path)

    with zipfile.ZipFile(embed_download_path, "r") as file:
        for inner in file.infolist():
            if not inner.filename.endswith(".zip"):
                continue
            file.extract(inner, download_dir)

            if args.debug:
                # Debug mode needs a different filename, but is otherwise identical
                extracted_file = download_dir / inner.filename
                debug_copy = download_dir / (extracted_file.stem + "_d.zip")
                shutil.copy(extracted_file, debug_copy)

    embed_download_path.unlink()


def download(
    version: str,
    arch: ArchInfo,
    stdlib: bool,
    debug: bool,
    download_dir: Path,
) -> None:
    """
    Downloads the python library files.

    Args:
        version: The version to download.
        arch: The architecture to download.
        stdlib: If to include the standard library (including dlls + zip).
        debug: If to include debug libraries.
        download_dir: The dir to download into.
    """
    shutil.rmtree(download_dir, ignore_errors=True)
    download_dir.mkdir(exist_ok=True)

    msi_url_base = f"https://www.python.org/ftp/python/{version}/{arch.py_name}/"

    # msis we just extract straight to the download folder
    basic_msis = ["core.msi", "dev.msi"]
    if stdlib:
        basic_msis.append("lib.msi")

    if debug:
        # Include the _d versions
        basic_msis += [msi.removesuffix(".msi") + "_d.msi" for msi in basic_msis]

    for msi_name in basic_msis:
        download_path = download_dir / msi_name

        download_file(msi_url_base + msi_name, download_path)
        extract_msi(download_path, download_dir)

        download_path.unlink()

    if stdlib:
        download_stdlib_zip(version, arch, download_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("version", type=str, help="The version to download.")

    PY_ARCH_LOOKUP = {a.py_name: a for a in ARCHITECTURES}

    parser.add_argument(
        "arch",
        choices=PY_ARCH_LOOKUP.keys(),
        help="The architecture to download.",
    )

    parser.add_argument(
        "--debug",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include the debug files. Defaults on.",
    )
    parser.add_argument(
        "--stdlib",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include the standard library (including dlls + zip). Defaults on.",
    )
    parser.add_argument(
        "--dir",
        help="The base directory to download into (not including the architecture dir).",
    )

    args = parser.parse_args()
    arch = PY_ARCH_LOOKUP[args.arch]

    download_dir: Path | None = args.dir
    if download_dir is None:
        download_dir = get_default_download_dir(arch)

    download(args.version, arch, args.stdlib, args.debug, download_dir)
