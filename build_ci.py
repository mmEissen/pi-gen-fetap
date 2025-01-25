from os import path
import subprocess
import os
from typing import Optional
import sys

CACHE_DIR = "/home/momo/usb1/build_cache"
STAGE_COUNT = 4
_WORKING_DIR = path.dirname(__file__)
_PI_WORK_DIR = path.join(_WORKING_DIR, "work", "raspios-bookworm-arm64")

def main():
    if os.geteuid() != 0:
        print("Must be root!")
        exit(1)
    build_image()


def build_image() -> None:
    for stage in range(STAGE_COUNT):
        print(f"Checking stage{stage}")
        print(f"Code is at version {code_version(stage)}, cache is at version {cached_version(stage)}")
        if code_version(stage) == cached_version(stage):
            print(f"Skipping stage{stage}")
            run(["touch", path.join(_WORKING_DIR, f"stage{stage}", "SKIP")])
        else:
            first_stage_to_build = stage
            print(f"Loading stage{stage - 1} as starting point for stage{stage}")
            copy_cache(first_stage_to_build)
            break
    else:
        copy_cache(STAGE_COUNT - 1, STAGE_COUNT - 1)
        first_stage_to_build = STAGE_COUNT

    print("Starting build!")
    execute(["./build.sh"], env={"CLEAN": "1"})

    for stage in range(first_stage_to_build, STAGE_COUNT):
        print(f"Storing rootfs of stage{stage}")
        store_cache(stage)


def copy_cache(target_stage: int, cache_stage: int = -1) -> None:
    if cache_stage < 0:
        cache_stage = target_stage - 1
    if cache_stage < 0:
        return
    stage_dir = path.join(_PI_WORK_DIR, f"stage{target_stage}")
    run(["mkdir", "-p", stage_dir])
    cache_dir = path.join(CACHE_DIR, f"stage{cache_stage}", cached_version(cache_stage))
    run(["cp", "-r", path.join(cache_dir, "rootfs"), stage_dir])


def store_cache(stage: int) -> None:
    # Make sure CACHE_DIR/stage<n>/ exists and is empty
    stage_cache_dir = path.join(CACHE_DIR, f"stage{stage}")
    run(["mkdir", "-p", stage_cache_dir])
    run(["rm", "-rf", path.joint(stage_cache_dir, "*")])

    # Make sure CACHE_DIR/stage<n>/<git-hash> exists
    git_hash = run(["git", "rev-parse", "HEAD"]).strip()
    cache_dir = path.join(stage_cache_dir, git_hash)
    run(["mkdir", "-p", cache_dir])

    # Actually copy the files from the last build to the cache dir
    build_stage_dir = path.join(_PI_WORK_DIR, f"stage{stage}")
    run(["cp", "-r", path.join(build_stage_dir, "rootfs"), cache_dir])


def code_version(stage: int) -> str:
    return run(
        [
            "git",
            "log",
            "-n",
            "1",
            "--pretty=format:%H",
            "--",
            f"stage{stage}",
        ]
    ).strip()


def cached_version(stage: int) -> str:
    stage_cache_dir = path.join(CACHE_DIR, f"stage{stage}")
    content = os.listdir(stage_cache_dir)
    if len(content) != 1:
        return "<cache invalid>"
    return content[0]


def run(command: list[str], env: Optional[dict[str, str]] = None) -> str:
    sys.stdout.flush()
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        check=True,
        text=True,
        env=env,
        cwd=_WORKING_DIR,
    )
    return result.stdout


def execute(command: list[str], env: Optional[dict[str, str]] = None) -> str:
    sys.stdout.flush()
    subprocess.run(
        command,
        check=True,
        env=env,
        cwd=_WORKING_DIR,
    )


if __name__ == "__main__":
    main()
