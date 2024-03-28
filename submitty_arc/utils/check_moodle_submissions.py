from argparse import ArgumentParser
from pathlib import Path
import re
import shutil
import random
import string
import csv

def check_filename(directory, pattern, structure, penalties=None):
    fixid = 0
    for submission in directory.glob('Participant_*_assignsubmission_file/*'):
        if not (match := pattern.match(submission.name)):
            print(f'submission: {submission} needs fixing')
            print("  attempting doing it automatically")
            fix_name(submission, pattern, fixid, penalties)
            fixid += 1
        else:
            print(submission)
            check_repository(submission, structure)



def extract_id(filename):
    moodle_id = r'Participant_([0-9]{7})_'
    moodle_pattern = re.compile(moodle_id)
    if (match := moodle_pattern.search(f"{filename.absolute()}")):
        return int(match.groups()[0])

def fix_name(filename, pattern, fixid=0, penalties=None):
    #extension = r'(\.tar)?\.gz' #r'\.zip' #r'(\.tar)?\.gz'
    extension = r'\.zip' #r'(\.tar)?\.gz'
    extension_pattern = re.compile(extension + '$')
    id_pattern = re.compile(pattern.pattern.replace(extension, ''))
    print(id_pattern.pattern)
    if (match := id_pattern.search(filename.name)):
        new_filename = match.group()
    else:
        new_filename = 'submission'
        #new_filename = ''.join(random.sample(list(string.ascii_uppercase), 4)) +  f'{fixid%10:1d}'

    if (match_ex := extension_pattern.search(filename.name)):
        new_filename += match_ex.group()
        shutil.move(filename, filename.parent / new_filename)
        print(f"  ✅ {filename.name} renamed to {new_filename}")
        penalty = -1
        message = "Submitted a wrong file name or type; fixed automatically."

    else:
        print(f"  ❌ {filename.name} doesn't has a recognised file extension")
        penalty = -3
        message = "Submitted a wrong file name or type; fixed manually."

    if penalties:
        id_submission = extract_id(filename)
        fields = ['id', 'penalty', 'message']
        with open(penalties, 'a') as penalty_file:
            writer = csv.DictWriter(penalty_file, fieldnames=fields)
            entry = {'id': id_submission,
                     'penalty': penalty,
                     'message': message,
                     }
            writer.writerow(entry)

def check_repository(filename, structure):
    import zipfile
    import tarfile
    import tempfile
    import subprocess

    print(filename)
    tempdir = tempfile.TemporaryDirectory()
    if 'zip' in filename.name:
        zf = zipfile.ZipFile(filename)
        zf.extractall(tempdir.name)
    else:
        with tarfile.open(filename) as tar:
            tar.extractall(tempdir.name)

    student_id = filename.stem.split('.')[0]
    repo_dir = Path(tempdir.name) / student_id / structure
    print(student_id)
    if repo_dir.is_dir() and (repo_dir / '.git').is_dir():
        results = subprocess.run(['git', 'diff', '--numstat'], cwd=repo_dir, capture_output=True)
        print("Git numstat diff")
        print(results.stdout.decode())
        print(results.stderr.decode())
    elif repo_dir.is_dir():
        print("No git directory detected")
        lsout = subprocess.run(['ls', '-la'], cwd=repo_dir, capture_output=True)
        print(lsout.stdout.decode())
    else:
        print("No directory as required")
        lsout = subprocess.run(['ls', '-la'], cwd=repo_dir.parent.parent, capture_output=True)
        print(lsout.stdout.decode())

    tempdir.cleanup()


if __name__ == '__main__':
    parser = ArgumentParser(description='Checks moodle submissions to follow a pattern.')
    parser.add_argument('directory', help='directory with the submissions')
    parser.add_argument('--pattern', '-p', default=r"([a-zA-Z]{4}[0-9]{1}|[0-9]{8})(\.tar)?\.gz", help='pattern - use single quotes to pass it')
    parser.add_argument('--structure', '-s', default="repository", help='directory structure after StudentID')
    parser.add_argument('--penalties', '-d', default="", help='penalties file')


    args = parser.parse_args()
    pattern = args.pattern #r"([a-zA-Z]{4}[0-9]{1}|[0-9]{8})(\.tar)?\.gz" # RSVC1.tar.gz or 12345678.tar.gz
    check_filename(Path(args.directory), re.compile(pattern), args.structure, args.penalties)
# FIXME: windows directories may be flagged as incorrect.
