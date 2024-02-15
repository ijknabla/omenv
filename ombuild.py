from __future__ import annotations

import argparse
import os
from asyncio import create_subprocess_exec, gather, run
from asyncio.subprocess import Process
from collections.abc import Sequence
from pathlib import Path
from subprocess import CalledProcessError
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any, NewType

Tag = NewType("Tag", str)

HERE = Path(__file__).parents[0].resolve()


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", default="/opt/OpenModelica")
    parser.add_argument("tag", nargs="*")
    args = parser.parse_args()
    prefix: str = args.prefix
    tags: Sequence[Tag] = args.tag

    result = await gather(
        *(build(tag=tag, prefix=Path(prefix, tag)) for tag in tags), return_exceptions=True
    )
    for exception in result:
        if isinstance(exception, BaseException):
            raise exception


async def build(tag: Tag, prefix: Path) -> None:
    with TemporaryDirectory() as directory:
        src = Path(directory, "src")

        await call(
            "git",
            "clone",
            "--recursive",
            "-b",
            tag,
            "https://github.com/OpenModelica/OpenModelica.git",
            f"{src}",
        )

        for cmake_list_txt in src.rglob("CMakeLists.txt"):
            original_text = text = cmake_list_txt.read_text(encoding="utf-8")

            text = text.replace(
                "https://build.openmodelica.org/omc/bootstrap/sources.tar.gz",
                "https://build.openmodelica.org/old/bootstrap/sources.tar.gz",
            )

            if text != original_text:
                print(f"Overwrite {cmake_list_txt}")
                cmake_list_txt.write_text(text, encoding="utf-8")

        build = Path(directory, "build")
        os.makedirs(build)

        await call(
            "cmake",
            "-DCMAKE_BUILD_TYPE=Release",
            f"-DCMAKE_INSTALL_PREFIX={prefix}",
            f"-S={src}",
            f"-B={build}",
        )

        await call("make", f"-C{build}", "-j4", "install")


if TYPE_CHECKING:
    call = create_subprocess_exec
else:

    async def call(*cmd: str, **kwargs: Any) -> Process:
        process = await create_subprocess_exec(*cmd, **kwargs)
        returncode = await process.wait()
        if returncode:
            raise CalledProcessError(returncode, cmd)
        return process


if __name__ == "__main__":
    run(main())
