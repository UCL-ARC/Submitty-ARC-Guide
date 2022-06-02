from pathlib import Path
from argparse import ArgumentParser
import os
import getpass
import shutil

def list_students(instructor="ucasper", course="mphy0021test", assignment="alchemist"):
    submissions = [p.name for p in Path(f'/home/{instructor}/{course}/submissions/{assignment}/').iterdir()]
    return list(filter(lambda x: instructor not in x, submissions))


def copy_grades(student_id, outdir, instructor="ucasper", course="mphy0021test", assignment="alchemist"):
    basepath = f'/home/{instructor}/{course}/results/{assignment}/{student_id}/'
    directories = [p.name for p in Path(basepath).iterdir()]
    versions = []
    for name in directories:
        try:
            versions.append(int(name))
        except ValueError:
            pass
    submission_dir = Path(basepath) / f'{max(versions)}'
    autograde = submission_dir / 'results.json'

    manual_grade = Path(f'/home/{instructor}/{course}/reports/all_grades/{student_id}_summary.json')


    destination_dir = outdir / student_id
    destination_dir.mkdir()

    shutil.copy(autograde, destination_dir / f'{student_id}_automated.json')
    shutil.copy(manual_grade, destination_dir / f'{student_id}_manual.json')


def run_it():
    parser = ArgumentParser(description="Extracts the files for manual and automatic grading.")
    parser.add_argument('--course', '-c', default='mphy0021', help='Course name as the directory in your home')
    parser.add_argument('--assignment', '-a', default='gamelife', help='assignment you want to collect')
    parser.add_argument('--instructor', '-i', default=getpass.getuser(), help='Instructor user')
    parser.add_argument('--outdir', '-o', default='.', help='where the output directory will be created, it will create a "results_{course}_{assignment}" directory')
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outpath = outdir / f"results_{args.course}_{args.assignment}"
    outpath.mkdir(parents=True)

    students = list_students(args.instructor, args.course, args.assignment)
    for student in students:
        copy_grades(student, outpath, instructor=args.instructor, course=args.course, assignment=args.assignment)

    shutil.make_archive(f"{outpath.name}", 'bztar', outdir, outpath.name)

if __name__ == "__main__":
    run_it()
