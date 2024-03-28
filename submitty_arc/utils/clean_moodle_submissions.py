from argparse import ArgumentParser
from pathlib import Path
import re
import shutil
import random
import string
import csv

def clean_submission(directory, patterns, structure):
    for submission in directory.glob('Participant_*_assignsubmission_file/*'):
        print(submission)
        clean_repository(submission, structure, patterns)


def clean_repository(filename, structure, patterns):
    import zipfile
    import tarfile
    import tempfile
    import subprocess
    import os
    import fnmatch

    print(filename)
    tempdir = tempfile.TemporaryDirectory()
    if 'zip' in filename.name:
        zf = zipfile.ZipFile(filename)
        zf.extractall(tempdir.name)
        compress = 'zip'
    else:
        with tarfile.open(filename) as tar:
            tar.extractall(tempdir.name)
        compress = 'tar'

    student_id = filename.stem.split('.')[0]
    repo_dir = Path(tempdir.name) / student_id / structure
    print(student_id)

    # clean repository
    if repo_dir.is_dir() and (repo_dir / '.git').is_dir():
        results = subprocess.run(['git', 'reset', '--hard', 'HEAD'], cwd=repo_dir, capture_output=True)
        print("Git remove what's not committed")

    # remove files required:
    for pattern in patterns:
        print(f"Removing directory {pattern}")
        l = [x.unlink() for x in filter(lambda x: x.is_file(), Path(tempdir.name).glob(f"**/{pattern}/**/*"))]
        print(f".... {len(l)} files removed")
        print(f"Removing file {pattern}")
        l = [x.unlink() for x in filter(lambda x: x.is_file(), Path(tempdir.name).glob(f"**/{pattern}"))]
        print(f".... {len(l)} files removed")
        print(f"Removing directory {pattern}")
        l = [os.rmdir(x) for x in sorted(filter(lambda x: x.is_dir(), Path(tempdir.name).glob(f"**/{pattern}/**/*")), reverse=True)]
        print(f".... {len(l)} directories removed")

    if repo_dir.is_dir() and (repo_dir / '.git').is_dir():
        if (repo_dir / "matplotplusplus").is_dir():
            print("Git remove and commit matplotplusplus docs/exs")
            results = subprocess.run(['git', 'add', '-A'], cwd=repo_dir / "matplotplusplus", capture_output=True)
            results = subprocess.run(['git', 'commit', '-m', '🧑‍🏫 Cleaning up'], cwd=repo_dir / "matplotplusplus", capture_output=True)
            print(results.stdout.decode())
            print(results.stderr.decode())
        print("Git add removed files")
        results = subprocess.run(['git', 'add', '-A'], cwd=repo_dir, capture_output=True)
        print(results.stdout.decode())
        print(results.stderr.decode())
        print("Git commit clean")
        results = subprocess.run(['git', 'commit', '-m', '🧑‍🏫 Cleaning up'], cwd=repo_dir, capture_output=True)
        print(results.stdout.decode())
        print(results.stderr.decode())

    import shlex
    import shutil
    # Repack it
    if compress == 'zip':
        rezip = subprocess.run(shlex.split(f"zip -r {filename.name} {student_id}"), cwd=tempdir.name, capture_output=True)
        # move file:
        newzip = (Path(tempdir.name) / filename.name)
        if newzip.is_file():
            # newzip.replace(filename.absolute()) # only works in the same filesystem
            shutil.move(newzip, filename.absolute())
    else:
        retar = subprocess.check_output(f"tar -C {tempdir.name} -zcf {filename}  {student_id}", shell=True)
        # FIXME

    print(f"I'm going to wait - look at {tempdir.name}")
    #breakpoint()
    tempdir.cleanup()


if __name__ == '__main__':
    parser = ArgumentParser(description='Cleans moodle submissions of unneeded artefacts.')
    parser.add_argument('directory', help='directory with the submissions')
    parser.add_argument('--patterns', '-p', nargs='*', default=r"[Bb]uild", help='pattern - use single quotes to pass it')
    parser.add_argument('--structure', '-s', default="repository", help='directory structure after StudentID')


    args = parser.parse_args()
    patterns = args.patterns #r"([a-zA-Z]{4}[0-9]{1}|[0-9]{8})(\.tar)?\.gz" # RSVC1.tar.gz or 12345678.tar.gz
    clean_submission(Path(args.directory), patterns, args.structure)
# FIXME: windows directories may be flagged as incorrect.
