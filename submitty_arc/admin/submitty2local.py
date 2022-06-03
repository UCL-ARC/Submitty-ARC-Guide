# dependencies on agile vm: texlive-base texlive-koma-scripts
from argparse import ArgumentParser
from pathlib import Path
import sys
from socket import gaierror
import shutil
import shlex
import subprocess
import glob

import click
from fabric import Connection
import yaml

from ..utils.create_dirs_feedback import generate_dirs

def extract_marks_submitty(course, assignment, instructor, host='submitty',):
    """
    Connects to the submitty server, runs the extractor and downloads the compressed file.
    """

    question = "Has the grade summaries have been generated? Go to Submitty > course > Grade reports -- Generate Grade Summaries "
    check_report = click.prompt(question, default="No", type=click.BOOL)
    if not check_report:
        sys.exit(1)

    # Test ssh access to machine
    try:
        result = Connection(host).run('sudo date', hide=True)
    except gaierror as e:
        print(e)
        sys.exit(1)

    # run submitty extractor
    conn = Connection(host)
    # FIXME Upload submitty_extractor if not in the directory.
    # if conn.sudo(f'test -f /home/{instructor}/submitty_extractor.py', warn=True).failed:
    #     print("file doesn't exits -- uploading it")
    #     c.put...

    # NOTE: change directory under sudo is an open issue: https://github.com/pyinvoke/invoke/issues/459 and 687
    extract = f"python3 submitty_extractor.py -c {course} -a {assignment}"
    result = conn.sudo(f"bash -c 'cd ~ && {extract}'", user=instructor)
    if result.failed:
        print(result.stdout, result.stderr)
        sys.exit(1)


    # Download the tar file for processing
    # Copies file to /tmp/, changes permission to allow downloading by ssh user, and removes
    # NOTE: this is not secure as other users could see the file being created in the /tmp/
    conn.sudo(f'cp /home/{instructor}/results_{course}_{assignment}.tar.bz2 /tmp/')
    conn.sudo(f'chmod 644 /tmp//results_{course}_{assignment}.tar.bz2')
    conn.get(f'/tmp/results_{course}_{assignment}.tar.bz2')
    conn.sudo(f'rm -rf /tmp/results_{course}_{assignment}.tar.bz2')
    conn.sudo(f'rm -rf /home/{instructor}/results_{course}_{assignment}')
    conn.sudo(f'rm -rf /home/{instructor}/results_{course}_{assignment}.tar.bz2')
    print(f"Local file downloaded: results_{course}_{assignment}.tar.bz2")
    shutil.unpack_archive(f"results_{course}_{assignment}.tar.bz2")

def combine_marks(course, assignment):
    default_config = f"assignment_{course}_{assignment}.yml"
    if not Path(default_config).is_file():
        message = f"The config yaml file {default_config} hasn't been found in this directory"
        print(message)
        sys.exit(1)

    cmd = f"grades-combine -r results_{course}_{assignment}/ -c assignment_{course}_{assignment}.yml -o output/{assignment} -s "
    penalties = f"penalties_{assignment}.csv"
    if Path(penalties).is_file():
        cmd += f"-p {penalties}"
    print(f"running: {cmd}")
    combine_run = subprocess.run(shlex.split(cmd), check=True, capture_output=True)
    print(combine_run.stdout.decode())
    print(combine_run.stderr.decode())


def generate_pdfs(course, assignment):
    student_reports = Path(f'output/{assignment}').glob('[0-9]*.tex')
    errors = dict()
    for report in student_reports:
        cmd = f"pdflatex -interaction batchmode {report.name}"
        try:
            output_pdf = subprocess.run(shlex.split(cmd), check=True, capture_output=True, cwd=report.parent)
        except subprocess.CalledProcessError as e:
            errors[report.name] = f"{e}"

    if errors.keys():
        print("❌ Some files failed to compile - revised them manually")
        print(f" cd {report.parent}")
        for l in errors.keys():
            print(f" pdflatex {l}")
        print("some things to check: have a backtick left open? or a maths syntax not between $?")


def fill_moodle_report(course, assignment, groups=False):

    output_dir = Path(f'output/{assignment}')
    default_config = f"assignment_{course}_{assignment}.yml"
    with open(default_config, 'r') as yamlf:
        config = yaml.load(yamlf, Loader=yaml.FullLoader)
        deadline = config['meta']['dates']['deadline']

    question = "Has the grading worksheet from moodle? Go to Moodle > course > Assignment -- Grading action: Download Grading worksheet"
    check_report = click.prompt(question, default="No", type=click.BOOL)
    if not check_report:
        sys.exit(1)

    possible_files = {f'{i}': x for i, x in enumerate(sorted(list(Path('./').glob('*.csv'))), start=1)}
    message = [f"These are the csv files found in this directory"] + [f"{key} - {value}" for key,value in possible_files.items()] + [f"Select the correct grading worksheet for the {assignment} assignment "]
    run_process = click.prompt('\n'.join(message), default='1',
                               type=click.Choice(list(possible_files.keys())), show_choices=False)

    grading_worksheet = possible_files[run_process]

    results_file = output_dir / 'results.csv'
    if not results_file.is_file():
        print(f"Results file not found at {results_file}")
        sys.exit(1)
    cmd =  f'grades-generate "{grading_worksheet}" "{results_file}" -d "{deadline}"'
    if groups:
        cmd += '-g'
    print(f"Running: {cmd}")
    combine_run = subprocess.run(shlex.split(cmd), check=True, capture_output=True)
    print(combine_run.stdout.decode())
    print(combine_run.stderr.decode())

    # Compile feedback
    worksheet_marks = Path(grading_worksheet.stem + '_penalty.csv')
    generate_dirs(worksheet_marks, output=f'feedback/{assignment}')
    pdf_reports = output_dir.glob('[0-9]*.pdf')
    for report in pdf_reports:
        output = next(Path(f'feedback/{assignment}').glob(f'*{report.stem}*'))
        shutil.copy(report, output)

    shutil.make_archive(f"{grading_worksheet.stem}", 'zip', root_dir=f'feedback/{assignment}')
    print(f"To release the marks, upload the '{worksheet_marks}' and '{grading_worksheet.stem}.zip' files to moodele")
    print(f"Release the marks following the moodle instructions: https://wiki.ucl.ac.uk/display/MoodleResourceCentre/2.+Moodle+Assignment")


def command():

    parser = ArgumentParser(description="Runs all the commands from submitty to pdf.")
    parser.add_argument('course', help='Course name as registered in submitty.')
    parser.add_argument('assignment', help='Assignment id as registered in submitty.')
    parser.add_argument('--host', default='submitty', help='submitty host machine to ssh in.')
    parser.add_argument('--instructor', '-i', default='ucasper', help='user from where to run the submitty extractor.')
    args = parser.parse_args()


    steps  =  {f"{i}": x for i,x in enumerate(['Collect from submitty', 'Combine marks', 'Generate pdfs', 'Generate moodle report'], start=1)}
    text_choices = ["Select which bit to run:",] + [f"{key} - {value}" for key,value in steps.items()] + ["(defaults 0, all)"]

    run_process = click.prompt("\n".join(text_choices), default='0',
                               type=click.Choice(["0"] + list(steps.keys())), show_choices=False)

    if run_process == "0":
        run_process = list(steps.keys())
    else:
        run_process = [run_process]

    if "1" in run_process:
        extract_marks_submitty(args.course, args.assignment, args.instructor, host=args.host)

    if "2" in run_process:
        combine_marks(args.course, args.assignment)

    if "3" in run_process:
        generate_pdfs(args.course, args.assignment)

    if "4" in run_process:
        fill_moodle_report(args.course, args.assignment)

if __name__ == '__main__':

    command()
