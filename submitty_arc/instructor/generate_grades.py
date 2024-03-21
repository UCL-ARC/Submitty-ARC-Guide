import csv
import os
from pathlib import Path
import shutil
import datetime
import re
from argparse import ArgumentParser

#import matplotlib.pyplot as plt
import pandas as pd
import yaml

def get_delay(text):
    days, hours, minutes, seconds = [0] * 4
    if "late" in text:
        delay = text.split('-')[1].strip()
        days_match = re.search(r'(\d{1,3}) day', delay)
        if days_match:
            days = int(days_match.group(1))
        hours_match = re.search(r'(\d{1,2}) hour', delay)
        if hours_match:
            hours = int(hours_match.group(1))
        minutes_match = re.search(r'(\d{1,2}) min', delay)
        if minutes_match:
            minutes = int(minutes_match.group(1))
        seconds_match = re.search(r'(\d{1,2}) sec', delay)
        if seconds_match:
            seconds = int(seconds_match.group(1))
    return datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

def get_workingday_range(start, end, bank_holidays=None):
    diff = end.date() - start.date()
    range_days = set([start.date() + datetime.timedelta(days=n) for n in range(diff.days+1)])

    range_weekend = set(filter(lambda x: f'{x:%a}' in ('Sat', 'Sun'), range_days))
    range_wd = range_days - range_weekend

    if bank_holidays:
        bh = set(bank_holidays)
        range_wd -= bh


    return list(range_wd)


def load_bankholidays():
    bankholidays = Path(__file__).absolute().parent / 'closing_dates.yaml'
    with open(bankholidays, 'r') as bh_f:
        bh_d = yaml.load(bh_f, Loader=yaml.FullLoader)
    daysoff = list()
    for academic_year in bh_d.values():
        for sect in academic_year.values():
            if isinstance(sect, dict):
                start_date = datetime.datetime.strptime(sect['start'], '%d %B %Y')
                diff = datetime.datetime.strptime(sect['end'], '%d %B %Y') - start_date
                daysoff.extend([start_date.date() + datetime.timedelta(days=n) for n in range(diff.days)])
            elif isinstance(sect, list):
                daysoff.extend(list(map(lambda x: datetime.datetime.strptime(x, '%d %B %Y').date(), sect)))
    return set(daysoff)


def get_no_workingdays(start, end, bank_holidays=None):

    if not bank_holidays:
        bank_holidays = load_bankholidays()

    diff = end.date() - start.date()
    range_days = set([start.date() + datetime.timedelta(days=n) for n in range(diff.days+1)])

    range_nwd = set(filter(lambda x: f'{x:%a}' in ('Sat', 'Sun'), range_days))

    if bank_holidays:
        bh = set(bank_holidays)
        bh = range_days.intersection(bh)
        range_nwd |= bh

    return list(range_nwd)



def get_delay_date(submission, due):
    if submission == "-":
        return
    submission = datetime.datetime.strptime(submission, '%A, %d %B %Y, %I:%M %p')
    due = datetime.datetime.strptime(due, '%A, %d %B %Y, %I:%M %p')

    is_delay = submission > due
    if is_delay:
        delay = submission - due
        nwd = get_no_workingdays(due, submission)
        if datetime.timedelta(days=len(nwd)) < delay:
            # We only remove them when it's more than a day
            delay -= datetime.timedelta(days=len(nwd))
    else:
        delay = datetime.timedelta(0)
    return delay

def calculate_penalty(mark, timedelta, level7=True):
    """
    Encoded information from
    https://www.ucl.ac.uk/academic-manual/chapters/chapter-4-assessment-framework-taught-programmes/section-3-module-assessment#3.12
    As module 7

    parameters
    ----------
    mark : float
      mark over 100 points.

    timedelta : datetime.timedelta
      submission delay

    level7 : bool
      whether we use level 7 or not, default: ``True``

    """
    pass_mark = 50 if level7 else 40
    if timedelta <= datetime.timedelta(minutes=30):
        return mark

    elif timedelta <= datetime.timedelta(days=2):
        if mark < pass_mark:
            return mark
        else:
            return max(pass_mark, mark - 10)

    elif timedelta <= datetime.timedelta(days=5):
        if mark < pass_mark:
            return mark
        else:
            return pass_mark

    else:
        return 1

# # Organise feedback
# # create feedback directory
# feedback = Path("feedback")
# feedback.mkdir(parents=True, exist_ok=True)
# submissions = Path("./assignment01")

# for submis in submissions.iterdir():
#     if submis.is_dir():
#         student = (feedback / submis.name)
#         student.mkdir(parents=True, exist_ok=True)
#         shutil.copy("grades01/{}.pdf".format(submis.name.split('_')[1]), student)

def runall(moodle_csv, marks_csv, due_date=None, outdir='.', group=False):
    '''

    parameters
    ----------
    moodle_csv : str

      Grades file downloaded from moodle (it includes the delay counted
      accounting for the exceptions - need to be added to moodle first on...) # FIXME add how!

    marks_csv : str

       marks file with three colunms: student id, mark, mark over 100.

    due_date : str

       date the assignment is due. If overrides have been applied to moodle it's not needed.

    outdir : str

       place where to store it.

    group : bool

       If instead of using student Ids we are using groups ids.

    '''
    original = pd.read_csv(moodle_csv)
    if 'Due date' not in original.columns:
        original['Due date'] = due_date
    generated = pd.read_csv(marks_csv) #names=['id', 'mark', 'grade'])

    moodle_column = 'Identifier'
    if group:
        moodle_column = 'Group'
        replacement = {'wg': 'Working Group ', 'aud': 'Aud'}
        generated['student_id'] = generated['student_id'].replace(replacement, regex=True)

    # extract the correct grade column
    final_grade = 'total grade' if 'total grade' in generated.columns else 'grade'

    # convert marks to dictionary:
    grades = {v['student_id']: round(v[final_grade],1) for idx, v in generated.iterrows()}

    # Update original grades
    if group:
        original['Grade'] = original.apply(lambda row: grades.get(row[moodle_column]), axis=1)
    else:
        original['Grade'] = original.apply(lambda row: grades.get(int(row['Identifier'].split()[1])), axis=1)

    no_penalty = Path(outdir) / f'{moodle_csv[:-4]}_nopenalty.csv'
    with_penalty = Path(outdir) / f'{moodle_csv[:-4]}_penalty.csv'
    original.to_csv(no_penalty, index=False, quoting=csv.QUOTE_NONNUMERIC)


    def set_marks(row):
        student_id = int(row['Identifier'].split()[1])
        if student_id in grades:
            mark = grades.get(student_id)
        elif 'Group' in row.index:
            mark = grades.get(row['Group'])
        else:
            if not "No submission" in row['Status']:
                print(f"📢 {student_id} doesn't has a grade")
            return None
        delay_c = get_delay(row['Status'])
        delay = get_delay_date(row['Last modified (submission)'], row['Due date'])
        print(delay_c, "=====", delay, "===", delay_c == delay)
        if mark:
            return round(calculate_penalty(mark, delay), 1)

    original['Grade'] = original.apply(set_marks, axis=1)
    original.to_csv(with_penalty, index=False, quoting=csv.QUOTE_NONNUMERIC)

    # fig = plt.figure()
    # original.hist(['Grade'], bins=50)
    # plt.show()


def run_it():
    parser = ArgumentParser(description="Generates the grades of all the students applying the correct penalty.")
    parser.add_argument('moodle_csv', help='Moodle grading worksheet')
    parser.add_argument('marks_csv', help='Marks result before any penalty - the file needs a `student_id` and `grade` columns')
    parser.add_argument('--outdir', '-o', default='.', help='where the resultant grading worksheet will be saved')
    parser.add_argument('--group', '-g', action="store_true", help='Set if this is a group assignment')
    parser.add_argument('--due', '-d', help='Sets the due date')
    args = parser.parse_args()

    runall(args.moodle_csv, args.marks_csv, outdir=Path(args.outdir), group=args.group, due_date=args.due)

if __name__ == "__main__":
    run_it()

# python generate_grades ./Grades-MPHY0021_19-20-A Data Clustering Problem-1600913.csv ./all_marks.csv

# original_file = './assignment01/Grades-MPHY0021_19-20-A Travel Planner package-1592599.csv'
# marks_csv = 'grades01/all_marks.csv'
# original_file = './Grades-MPHY0021_19-20-A Travel Planner package-1592599.csv'
# original_file = './Grades-MPHY0021_19-20-A Data Clustering Problem-1600913.csv'
# marks_csv = './all_marks.csv'
# duedate = 'Tuesday, 3 March 2020, 11:59 PM'
