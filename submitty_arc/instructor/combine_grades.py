'''
convention:
*marks* are the possible points one can take
*totals* are the results
'''
import csv
import re
import glob
import json
from pathlib import Path
from argparse import ArgumentParser
import shutil
import random

import jinja2
import yaml

from ..utils.md2tex import mdcomment2tex

ROOT_PKG = Path(__file__).absolute().parent.parent

def set_jinja_latex_env():
    return jinja2.Environment(block_start_string=r'\BLOCK{',
                              block_end_string='}',
                              variable_start_string=r'\VAR{',
                              variable_end_string='}',
                              comment_start_string=r'\#{',
                              comment_end_string='}',
                              line_statement_prefix='%%',
                              line_comment_prefix='%#',
                              trim_blocks=True,
                              autoescape=False,
                              loader=jinja2.FileSystemLoader(ROOT_PKG / 'utils' / 'latex_template'))

def remove_ta_internal_comments(list_comments):
    '''
    Removes TA's internal comments, coded as `%% internal %%`
    '''
    return list(filter(lambda x: x, [re.sub('^-\s*', '', re.sub('%%.+?%%', '', comment).strip()) for comment in list_comments]))

def texify_comments(list_comments):
    return mdcomment2tex(" ".join(remove_ta_internal_comments(list_comments)))


class Question:
    def __init__(self, input_dict, remove_title=""):
        self.title = input_dict.get('title', "")
        title_tex = self.title
        if remove_title:
            title_tex = self.title.replace(remove_title, r"REMOVEME").strip()
        self.title_tex = mdcomment2tex(title_tex)
        self.marks = input_dict.get('marks', 0)
        self.manual = input_dict.get('manual', 0)
        self.auto = input_dict.get('auto', 0)
        self.auto_factor = input_dict.get('auto_factor', 1)
        self.manual_factor = input_dict.get('manual_factor', 1)
        self._comments = []
        self._points_auto = 0
        self._points_manual = 0
        self._conversion = self.marks / (self.manual * self.manual_factor + self.auto * self.auto_factor)

    def set_points(self, auto, manual):
        self._points_auto = auto
        self._points_manual = manual

    @property
    def total_auto(self):
        return (self._points_auto * self.auto_factor) * self._conversion

    @property
    def total_manual(self):
        return (self._points_manual * self.manual_factor) * self._conversion

    @property
    def total(self):
        if self.marks == 0:
            return self.total_manual #  returns penalties that can be < 0
        return max(0, min(self.total_auto + self.total_manual, self.marks))

    def add_comments(self, comments):
        self._comments += comments if type(comments) == list else [comments]

    @property
    def comments(self):
        return texify_comments(self._comments)


class Section:
    def __init__(self, section_dict):
        self.title = mdcomment2tex(section_dict.get("title", "").replace("  ", " "))
        self.description = mdcomment2tex(section_dict.get("description", ""))
        self.marks = section_dict.get("marks", 0)
        self._stitle = section_dict.get("stitle", "").replace("  ", " ")
        remove_title = section_dict.get("remove", '')
        questions = {q: qval for q, qval in section_dict.items() if "Question" in q}  # So the enumerate only counts questions
        self.Questions = {i: Question(q_val, remove_title) for i, q_val in enumerate(questions.values(), start=1)}
        self.__check_marks()

    def __check_marks(self):
        questions_marks = sum([q.marks for q in self.Questions.values()])
        assert self.marks == questions_marks, f"expected total of {self.marks} but got {questions_marks} for section: {self.title}"

    @property
    def total(self):
        total_sections = sum([q.total for q in self.Questions.values()])
        if self.marks == 0:
            return total_sections
        return max(0, min(total_sections, self.marks))


class Assignment:
    def __init__(self, assignment_dict):
        self.meta = assignment_dict['meta']
        self.groups = assignment_dict.get('groups')
        self.Sections = {sect: Section(sect_val) for sect, sect_val in assignment_dict['sections'].items()}
        self.__check_marks()

    def __check_marks(self):
        sections_marks = sum([s.marks for s in self.Sections.values()])
        assert self.meta['marks'] == sections_marks, f"Expected total of {self.meta['marks']} but got {sections_marks} for this assignment"

    def __create_penalty_sect(self, penalty):
        assert len(penalty) == 2, f"The penalties has to contain two elements, the penalty and its reason"
        penalty_section = {'title': "Deductions",
                           "description": "Deductions applied to submission",
                           "Question": {"title": "Reason", "marks": 0, "manual": 1}}
        self.Sections['Penalty'] = Section(penalty_section)
        q = self.Sections['Penalty'].Questions[1]
        q._conversion = 1
        q.set_points(0, float(penalty[0]))
        q.add_comments(penalty[1])

    def load_results(self, auto, manual, penalty=None):
        auto_results = Auto_grad(auto)
        manual_results = Manual_grad(manual, self.meta['submitty_type'], self.meta['submitty_id'])
        assert auto_results.auto_score == manual_results.auto_score, f"The automatic score doesn't match between the auto ({auto_results.auto_score}) and manual ({manual_results.auto_score}) file for student: {manual_results.student}"
        autoscore_set = False

        self.meta['student'] = manual_results.student
        for sect, section in self.Sections.items():
            if section._stitle:
                finds = lambda x: section._stitle in x
                autok = next(filter(finds, auto_results.components.keys()), None)
                if autok:
                    autoscore_set = True
                    autoscore = auto_results.components[autok] / len(section.Questions)
                    del auto_results.components[autok]
                    autok = None

            for quest, question in section.Questions.items():
                if not (section._stitle and autoscore_set):
                    autoscore = 0
                findq = lambda x: question.title in x
                autok = next(filter(findq, auto_results.components.keys()), None)
                manualk = next(filter(findq, manual_results.components.keys()), None)
                if autok:
                    autoscore = auto_results.components[autok]
                    del auto_results.components[autok]
                if manualk:
                    question.set_points(autoscore, manual_results.components[manualk]['score'])
                    question.add_comments(manual_results.components[manualk]['comments'])
                    del manual_results.components[manualk]
                else:
                    raise ValueError(f"Not component found for {question.title}")

        if penalty:
            self.__create_penalty_sect(penalty)

        auto_components = {qtitle:points for qtitle, points in auto_results.components.items() if points != 0}
        assert len(auto_components) == 0, f"Not all auto results have been used: {auto_components=}"
        assert len(manual_results.components) == 0, f"Not all manual results have been used: {manual_results.components=} "
        self.overall_comments = manual_results.comments

    @property
    def total(self):
        sects = sum(section.total for section in self.Sections.values())
        return max(0, min(sects, self.meta['marks']))


    def __repr__(self):
        output = []
        output.append(f"Student: {self.meta['student']}")
        output.append(f"Total: {round(self.total, 2)}/{self.meta['marks']}")
        for sect, section in self.Sections.items():
            output.append(f"    Section: {section.title} -----------------  {round(section.total, 2)}/{section.marks}")
            for quest, question in section.Questions.items():
                output.append(f"           Question: {question.title} -----------------  {round(question.total, 2)}/{question.marks}")
                output.append(f"             {question.comments}")
        return "\n".join(output)

    def to_csv(self, header=False, details=False):
        """
        Generates a row with the total results for each question, useful to collect and analyse stats.
        If used with header will return two rows, one for the header and another for the data.
        If asked for details will show the points for auto and manual for each section.
        """
        # TODO
        raise NotImplementedError


    def to_latex(self, output_prefix='./'):
        """
        The template has been created following the guidance from
        http://eosrei.net/articles/2015/11/latex-templates-python-and-jinja2-generate-pdfs
        and https://miller-blog.com/latex-with-jinja2/
        so the template is "readable" from a Latex text editors
        """
        latex_jinja_env = set_jinja_latex_env()
        template = latex_jinja_env.get_template('student_template.tex')
        with open(Path(output_prefix) / f"{self.meta['student']}.tex", 'w') as texfile:
            texfile.write(template.render(meta=self.meta,
                                          total=round(self.total, 2),
                                          feedback=self.overall_comments,
                                          sections=self.Sections,
                                          ))



class Manual_grad:
    def __init__(self, json_file, assignment_type=None, assignment_id=None):
        with open(json_file) as fjson:
            manual_results = json.load(fjson)
        self.student = manual_results["user_id"]

        if not assignment_type:
            assignment_type = "Homework"
        else:
            assignment_type = assignment_type.capitalize()
        if not assignment_id:
            assignment = 0
        else:
            ids = [x["id"] for x in manual_results[assignment_type]]
            assignment = ids.index(assignment_id)
        assignment = manual_results[assignment_type][assignment]

        overall_comments = assignment.get("overall_comments", [])
        if not overall_comments:
            overall_comments = {"no_comments": ""}
        self.comments = texify_comments(overall_comments.values())
        self.auto_score = assignment.get("autograding_score", 0)
        self.manual_score = assignment.get("tagrading_score", 0)

        self.components = {x["title"]: {'score': x["score"],
                                        'default': x['default_score'],
                                        'comments': [y["note"] for y in x["marks"]],
                                        'add_points': sum([y["points"] for y in x["marks"]]),
                                        'lower_clamp': x['lower_clamp'],
                                        'upper_clamp': x['upper_clamp'],
                                        } for x in assignment["components"]
                           }
        self.__check_manual_addup()
        self.__check_manual_score(json_file)

    def __check_manual_addup(self):
        bad_values = {}
        for comp, values in self.components.items():
            received = values['score']
            total = values['default'] + values['add_points']
            if received != min(max(values['lower_clamp'], total), values['upper_clamp']):
                bad_values[comp] = f"{values['score']} != min( max({values['lower_clamp']}, {values['default']} + {values['add_points']}), {values['upper_clamp']} )"
        if bad_values:
            raise ValueError(f"The following questions for {self.student} have the following incorrect additions:\n{json.dumps(bad_values, indent=4)}")

    def __check_manual_score(self, json_file):
        score = sum([x["score"] for k, x in self.components.items()])
        assert self.manual_score == score, f"The total number of points per component ({score}) doesn't add up to the total ({self.manual_score}); ({json_file})"


class Auto_grad:
    def __init__(self, json_file):
        with open(json_file) as fjson:
            auto_results = json.load(fjson)
        self.auto_score = auto_results["automatic_grading_total"]
        self.components = {x["test_name"].replace("  ", " "): x['points_awarded'] for x in auto_results["testcases"]}
        self.__check_auto_score()

    def __check_auto_score(self):
        score = sum(x for x in self.components.values())
        assert self.auto_score == score, f"The total number of points per component ({score}) doesn't add up to the total ({self.auto_score})"


def generate_tex_styles(config, outdir='./'):
    latex_jinja_env = set_jinja_latex_env()

    config['meta']['description_tex'] = mdcomment2tex(config['meta']['description'])

    if not Path(outdir).exists():
        Path(outdir).mkdir()

    for template in ['ucl_mark.sty', 'assignment_details.tex']:
        style = latex_jinja_env.get_template(template)
        with open(Path(outdir) / template, 'w') as texfile:
            texfile.write(style.render(meta=config['meta']))

    for extra_file in glob.glob(latex_jinja_env.loader.searchpath[0] + '/*[pdf,lco]'):
        extra_file = Path(extra_file)
        shutil.copyfile(extra_file, Path(outdir) / extra_file.name)



def generate_marks_students(results_path, yamlconfig, outdir='./', penalties=None, second_mark=False):
    """
    Assuming we have a directory with: path/student_id/{automated,manual}.json
    Iterate over them all and produce latex files and a single CSV
    """

    results_path = Path(results_path)
    with open(yamlconfig, 'r') as yamlf:
        config = yaml.load(yamlf, Loader=yaml.FullLoader)

    csvout = Path(outdir) / 'results.csv' #FIXME add course name + date
    generate_tex_styles(config, outdir)

    penalties_dict = {}
    if penalties:
        with open(penalties, 'r') as penalties_file:
            penalties_reader = csv.reader(penalties_file, delimiter=',')
            for row in penalties_reader:
                penalties_dict[row[0]] = tuple(row[1:])

    grades = {}
    for i,student_id in enumerate(results_path.iterdir()):
        # skip if one of the directories is the output directory.
        if results_path / student_id == Path(outdir):
            continue
        if student_id.is_dir():
            student = student_id.name
            penalty = penalties_dict.get(student, None)
            std_assignment = Assignment(config)
            std_assignment.load_results(student_id / f'{student}_automated.json',
                                        student_id / f'{student}_manual.json',
                                        penalty=penalty)
            grades[student] = round(std_assignment.total, 2)
            std_assignment.to_latex(output_prefix=csvout.parent)
        # if i > 2:
        #     break

    # sort by grades
    if second_mark:
        grades_sorted = dict(sorted(grades.items(), key=lambda x: x[1]))
        min2nd_mark = max(5, round(len(grades_sorted) * 0.1))
        fix2nd_mark = len(list(filter(lambda x: needs_second_mark(x), grades_sorted.values())))
        extra_2nd_mark = max(min2nd_mark - fix2nd_mark, 0)
        print(f"{min2nd_mark=}, {fix2nd_mark=}, {extra_2nd_mark=}")

        sample = [""]
        extra_2nd_mark = False
        if extra_2nd_mark:
            sample = random.sample([x[0] for x in filter(lambda x: not needs_second_mark(x[1]),
                                                         grades_sorted.items())],
                                   extra_2nd_mark)

        with open(csvout, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["student_id", "grade", "2Nd grade", "2nd grade - maybe"])
            writer.writerows(map(lambda x: (*x,
                                            "Yes" if needs_second_mark(x[1]) else "",
                                            "Maybe" if x[0] in sample else ""
                                            ),
                                 grades_sorted.items()))


def needs_second_mark(mark):
    return mark < 50 or round(mark) in [59, 60, 69, 70, 55, 65, 85]



# TODO
# Include Overall comments (feedback?)
# Include overall penalties
#

def run_it():
    parser = ArgumentParser(description="Combines the grades of all the students with the right weighting.")
    parser.add_argument('--resultsdir', '-r', default='mphy0021', help='Directory with all the students results')
    parser.add_argument('--config', '-c', default='gamelife', help='assignment you want to collect')
    parser.add_argument('--outdir', '-o', default='.', help='where the output directory will be created')
    parser.add_argument('--penalties', '-p', default=None, help="csv file with id, penalty to apply and comment")
    parser.add_argument('--second_mark', '-s', action="store_true", help="Set to create a results.csv table with who needs to be second marked")
    args = parser.parse_args()

    print(args.penalties)
    generate_marks_students(args.resultsdir, args.config, outdir=Path(args.outdir),
                            penalties=args.penalties, second_mark=args.second_mark)

if __name__ == "__main__":
    run_it()
