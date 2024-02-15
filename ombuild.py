import argparse
import os
from asyncio import create_subprocess_exec, run
from pathlib import Path

HERE = Path(__file__).parents[0].resolve()


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("tag")
    args = parser.parse_args()
    tag: str = args.tag

    src = HERE / "src" / tag
    build = HERE / "build" / tag
    install = HERE / tag

    os.makedirs(src.parents[0], exist_ok=True)
    git_clone = await create_subprocess_exec(
        "git",
        "clone",
        "--recursive",
        "-b",
        tag,
        "https://github.com/OpenModelica/OpenModelica.git",
        f"{src}",
    )
    await git_clone.wait()

    for CMakeList in src.rglob("CMakeLists.txt"):
        CMakeList.write_text(
            CMakeList.read_text().replace(
                "https://build.openmodelica.org/omc/bootstrap/sources.tar.gz",
                "https://build.openmodelica.org/old/bootstrap/sources.tar.gz",
            )
        )

    os.makedirs(build, exist_ok=True)

    cmake_cmd = [
        "cmake",
        "-DCMAKE_BUILD_TYPE=Release",
        f"-DCMAKE_INSTALL_PREFIX={install}",
        f"-S={src}",
        f"-B={build}",
    ]

    cmake_process = await create_subprocess_exec(*cmake_cmd)
    await cmake_process.wait()

    make_process = await create_subprocess_exec("make", f"-C{build}", "-j4", "install")
    await make_process.wait()


if __name__ == "__main__":
    run(main())
