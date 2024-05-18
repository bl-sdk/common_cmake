#!/usr/bin/env python3
import argparse
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import requests

CACHE_FILENAME: str = ".version.toml"


class Arch(Enum):
    win32 = "win32"
    amd64 = "amd64"


@dataclass
class Settings:
    version: str
    arch: Arch
    debug: bool
    stdlib: bool

    def get_default_download_dir(self) -> Path:
        """
        Gets the default dir to download these settings into.

        Returns:
            The path to download into.
        """
        return Path(__file__).resolve().parent / f"py-{self.version}-{self.arch.value}"

    def get_cache_str(self) -> str:
        """
        Converts these settings to the format used in the cache.

        Returns:
            The settings in the cache format.
        """
        # tomllib doesn't support writing yet, but toml is supposed to be the new python config
        # format, so manually recreate it

        # toml bools are supposed to be lowercase
        toml_bool = {True: "true", False: "false"}
        return (
            f'version = "{self.version}"\n'
            f'arch = "{self.arch.value}"\n'
            f"debug = {toml_bool[self.debug]}\n"
            f"stdlib = {toml_bool[self.stdlib]}\n"
        )


def download_file(url: str, path: Path) -> None:
    """
    Downloads a url to disk.

    Args:
        url: The url to download.
        path: The path to download to.
    """
    with requests.get(url, stream=True, timeout=5) as resp, path.open("wb") as file:
        resp.raw.decode_content = True
        shutil.copyfileobj(resp.raw, file)


MSIEXEC_CANT_OPEN_EXIT_CODE = 2203


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
            ret = subprocess.run(
                ["msiexec", f"TARGETDIR={tmp_dir}", "/a", str(msi), "/qn"],
                check=False,
            )
            if ret.returncode == MSIEXEC_CANT_OPEN_EXIT_CODE:
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


def download_stdlib_zip(version: str, arch: Arch, download_dir: Path) -> None:
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
    embed_name = f"python-{version}-embed-{arch.value}.zip"

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


def download(download_dir: Path, settings: Settings) -> None:
    """
    Downloads the python library files.

    Args:
        download_dir: The dir to download into.
        settings: The settings describing what to download.
    """
    shutil.rmtree(download_dir, ignore_errors=True)
    download_dir.mkdir(exist_ok=True)

    msi_url_base = f"https://www.python.org/ftp/python/{settings.version}/{settings.arch.value}/"

    # msis we just extract straight to the download folder
    basic_msis = ["core.msi", "dev.msi"]
    if settings.stdlib:
        basic_msis.append("lib.msi")

    if settings.debug:
        # Include the _d versions
        basic_msis += [msi.removesuffix(".msi") + "_d.msi" for msi in basic_msis]

    for msi_name in basic_msis:
        download_path = download_dir / msi_name

        download_file(msi_url_base + msi_name, download_path)
        extract_msi(download_path, download_dir)

        download_path.unlink()

    if settings.stdlib:
        download_stdlib_zip(settings.version, settings.arch, download_dir)

    (download_dir / CACHE_FILENAME).write_text(settings.get_cache_str())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("version", type=str, help="The version to download.")

    parser.add_argument(
        "arch",
        choices=tuple(x.value for x in Arch),
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
        help=(
            "The directory to download into. When not given, picks a defaults in the same dir as"
            " this script."
        ),
    )
    parser.add_argument(
        "--cache",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "When set, don't redownload if all the settings match those cached in the download dir."
            " Checks version, arch, debug, and stdlib."
        ),
    )

    args = parser.parse_args()

    settings = Settings(
        args.version,
        Arch(args.arch),
        args.debug,
        args.stdlib,
    )

    download_dir: Path | None = (
        settings.get_default_download_dir() if args.dir is None else Path(args.dir).resolve()
    )

    print(settings)

    if args.cache:
        cache_file = download_dir / CACHE_FILENAME
        if not cache_file.exists():
            print("Cache does not exist")
        elif cache_file.read_text() != settings.get_cache_str():
            print("Cache does not match")
        else:
            print("Cached settings are identical, skipping download")
            sys.exit(0)

    print("Downloading...")
    download(download_dir, settings)
