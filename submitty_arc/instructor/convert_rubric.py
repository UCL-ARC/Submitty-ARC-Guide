import json
from argparse import ArgumentParser
from os import write

import yaml

def convert_json(json_rubric):

    with open(json_rubric, 'r') as ff:
        rubric = json.load(ff)

    titles = [f"{i} -- {x['title']}" for i,x in enumerate(rubric)]
    print("\n".join(titles))
    n_sections = input("how many sections do you have? ")
    sections = {f"section{i}": dict() for i in range(int(n_sections))}

    for section, sect_dict in sections.items():
        sect_dict['title'] = input(f"Title for {section}: ")
        sect_dict['description'] = input(f"Description for {section}: ")
        sect_dict['marks'] = int(input(f"Total marks for {section}: "))
        questions = input(f"Which questions numbers from the titles above would go here? input them separated by spaces ")
        quest_index = [int(x) for x in questions.split()]
        for i, qnumber in enumerate(quest_index):
            sect_dict[f'Question {i+1}'] = {
                'title': rubric[qnumber]["title"],
                'marks': rubric[qnumber]["max_value"],
                'manual': rubric[qnumber]["max_value"],
                'auto': 0,
            }

    meta = {"department": "", 'course': "", 'course_code': "", 'lecturers': [], 'title': '', 'description': "", 'dates': {'handed': "", 'deadline': ""}, 'marks': 0, 'submitty_type': 'assignment', 'submitty_id': ''}
    print('provide some extra information about the course:')
    meta['department'] = input('Name of the department: ')
    meta['course'] = input('Name of the course: ')
    meta['course_code'] = input('course code: ')
    meta['lecturers'] = input('lecturers (comma separated): ').split(',')
    meta['title'] = input('Coursework title: ')
    meta['dates']['handed'] = input('handed out date ')
    meta['dates']['deadline'] = input('deadline date ')
    meta['marks'] = int(input("Total marks of the assignment "))
    meta['submitty_id'] = input('submitty id of this coursework ')

    all_together = {'meta': meta, 'sections': sections}
    with open(json_rubric.split('.')[0] + '.yaml', 'w') as ff:
        yaml.safe_dump(all_together, ff)

    print("revise the file and add a description")

def run_it():
    parser = ArgumentParser(description="Converts a json rubric into a yaml one for other programs.")
    parser.add_argument('json_rubric', help='json file exported from submitty')
    # parser.add_argument('--auto_rubric', default=None, help='info file with the auto points')  # TODO
    args = parser.parse_args()

    convert_json(args.json_rubric)

if __name__ == "__main__":
    run_it()
