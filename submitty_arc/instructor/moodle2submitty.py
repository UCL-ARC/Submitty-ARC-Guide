import csv
import random
import datetime
from argparse import ArgumentParser
import pandas as pd

from ..utils.user_names import random_capitalise, generate_names_gods


random.seed(24)
# with open('courseid_6297_participants.csv', 'r') as realfile:
#     emails = [row['Email address'] for row in csv.DictReader(realfile)]

def get_n(n, list_names):
    all_names = [x.split()[0] for x in submitty_register]
    if n in all_names:
        i = 0
        while n in all_names:
            n = f"{n}{i}"
            i += 1
    return n


def generate_submitty_file_from_emails(emails):

    names, gods = generate_names_gods()
    submitty_register = []
    mail_list = []
    for n,g,e in zip(names, gods, emails):
        firstn = n.capitalize()
        lastn = g.capitalize()
        usern = get_n(n, submitty_register)
        section = "section1"
        passw = random_capitalise(n) + str(random.randint(0,9))
        preffirst = firstn
        preflast = lastn
        fakee = f'{n}@glaciers.int'
        submitty_register.append(f'{usern}, {firstn}, {lastn}, {fakee}, {section}, {passw}, {preffirst}, {preflast}\n')
        mail_list.append(f'{e} {firstn} {lastn} {usern} {passw}\n')

    with open('submitty_reg.csv', 'w') as sbr:
        sbr.writelines(submitty_register)

    with open('mail_reg.txt', 'w') as mar:
        mar.writelines(mail_list)


def generate_submitty_file_from_worksheet(worksheet):

    today = datetime.datetime.now()

    ids = worksheet['Identifier'].str.replace('Participant ', '').tolist()
    names, gods = generate_names_gods()
    submitty_register = []
    mail_list = []
    for n,g,i in zip(names, gods, ids):
        firstn = n.capitalize()
        lastn = g.capitalize()
        usern = i
        section = "section1"
        passw = str(i) + random_capitalise(n) + str(random.randint(0,100))
        preffirst = firstn
        preflast = lastn
        fakee = f'{i}@glaciers.int'
        submitty_register.append(f'{usern}, {firstn}, {lastn}, {fakee}, {section}, {passw}, {preffirst}, {preflast}\n')

    with open(f'submitty_reg_{today:%Y%m%d}.csv', 'w') as sbr:
        sbr.writelines(submitty_register)


def moodle2submitty(ws_filename):

    df = pd.read_csv(ws_filename)
    generate_submitty_file_from_worksheet(df)


def command():
    parser = ArgumentParser(description='Generates submitty file from moodles input.')
    parser.add_argument('worksheet', help='worksheet file submission')

    args = parser.parse_args()
    moodle2submitty(args.worksheet)
