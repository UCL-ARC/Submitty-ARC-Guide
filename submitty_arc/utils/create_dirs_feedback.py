from pathlib import Path
from argparse import ArgumentParser

import pandas as pd

def generate_dirs(input_file, output='./'):
    grades = pd.read_csv(input_file)
    grades.dropna(subset=['Grade'], inplace=True)
    grades['id'] = grades['Identifier'].replace({'Participant ': ''}, regex=True)
    if 'Group' in grades.columns:
        grades['dir'] = grades['Group'] + "-" + grades["Full name"] + "_" + grades['id'] + "_assignsubmission_file_"
    else:
        grades['dir'] = 'Participant_' + grades['id'] + "_assignsubmission_file_"
    # Create feedback directroy
    outdir = Path(output)
    for index, row in grades.iterrows():
        (outdir /  row['dir']).mkdir(parents=True, exist_ok=True)




if __name__ == "__main__":
    parser = ArgumentParser(description="Generates the directories for feedback in group work.")
    parser.add_argument('moodle_csv', help='Moodle grading worksheet')
    parser.add_argument('--outdir', '-o', default='./feedback', help='Output directory')

    args = parser.parse_args()

    generate_dirs(args.moodle_csv, args.outdir)
