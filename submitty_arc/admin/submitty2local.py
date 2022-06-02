# dependencies on agile vm: texlive-base texlive-koma-scripts
import sys
from socket import gaierror

import click
from fabric import Connection

SUBMITTY_HOST = 'submitty'
SUBMITTY_INSTRUCTOR = 'ucasper'
course = 'phas0100test'
assignment = 'test02'

def extract_marks_submitty():
    """
    Connects to the submitty server, runs the extractor and downloads the compressed file.
    """
    # Test ssh access to machine
    try:
        result = Connection(SUBMITTY_HOST).run('sudo date', hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        print(msg.format(result))
    except gaierror as e:
        print(e)
        sys.exit(1)

    # run submitty extractor
    conn = Connection(SUBMITTY_HOST)
    # FIXME Upload submitty_extractor if not in the directory.
    # if conn.sudo(f'test -f /home/{SUBMITTY_INSTRUCTOR}/submitty_extractor.py', warn=True).failed:
    #     print("file doesn't exits -- uploading it")
    #     c.put...

    # NOTE: change directory under sudo is an open issue: https://github.com/pyinvoke/invoke/issues/459 and 687
    extract = f"python3 submitty_extractor.py -c {course} -a {assignment}"
    result = conn.sudo(f"bash -c 'cd ~ && {extract}'", user=SUBMITTY_INSTRUCTOR)
    if result.failed:
        print(result.stdout, result.stderr)
        sys.exit(1)


    # Download the tar file for processing
    # Copies file to /tmp/, changes permission to allow downloading by ssh user, and removes
    # NOTE: this is not secure as other users could see the file being created in the /tmp/
    conn.sudo(f'cp /home/{SUBMITTY_INSTRUCTOR}/results_{course}_{assignment}.tar.bz2 /tmp/')
    conn.sudo(f'chmod 644 /tmp//results_{course}_{assignment}.tar.bz2')
    conn.get(f'/tmp/results_{course}_{assignment}.tar.bz2')
    conn.sudo(f'rm -rf /tmp/results_{course}_{assignment}.tar.bz2')
    print(f"Local file downloaded: results_{course}_{assignment}.tar.bz2")
    shutil.unpack_archive(f"results_{course}_{assignment}.tar.bz2")



if __name__ == '__main__':

    question = "Has the grade summaries have been generated? Go to Submitty > course > Grade reports -- Generate Grade Summaries "
    check_report = click.prompt(question, default="No", type=click.BOOL)

    if not check_report:
        sys.exit(1)

    extract_marks_submitty()
