from pathlib import Path

import yaml

from ..combine_grades import Question, Section, Assignment, Manual_grad, Auto_grad, remove_ta_internal_comments, texify_comments

TEST_DATA = Path(__file__).parent / 'data'
yaml_question_sample="""
title: "My question"
marks: 2
manual: 5
auto: 3
auto_factor: 3
manual_factor: 2
"""

yaml_section_sample="""
title: "section title"
description: "some short description"
marks: 5
stitle: "some general name"
Question 1:
  title:  "title question 1"
  marks: 2
  manual: 7
  auto: 3
Question 2:
  title:  "title question 2"
  marks: 3
  manual: 2
  auto: 1
"""

def test_question_init():
    data = yaml.load(yaml_question_sample, Loader=yaml.SafeLoader)
    myQuestion = Question(data)
    assert myQuestion.title == "My question"

def test_question_total():
    data = yaml.load(yaml_question_sample, Loader=yaml.SafeLoader)
    myQuestion = Question(data)
    assert myQuestion.total == 0
    myQuestion.set_points(2, 4)
    assert myQuestion.total_auto == 6 * 2/19
    assert myQuestion.total_manual == 8 * 2/19
    assert myQuestion.total == 14 * 2/19
    myQuestion.set_points(3, 5)
    assert myQuestion.total == 2

def test_question_comments():
    data = yaml.load(yaml_question_sample, Loader=yaml.SafeLoader)
    myQuestion = Question(data)
    comments = ["Very good", "nice!", "Great"]
    myQuestion.add_comments(comments[:2])
    myQuestion.add_comments(comments[-1])
    assert myQuestion.comments == " ".join(comments)

def generate_data():
    comments = ["Very good", "nice!", "Great"]
    input_comments = comments[:]
    input_comments[0] = comments[0] + "%% This took a 50% of the points %%"
    input_comments[1] =  "%% This not %%" + comments[1] + "%% This not %%"
    input_comments[2] =  "- " + comments[2][0:3] + "%% This not %%" + comments[2][3:]
    return comments, input_comments

def test_question_clean_comments():
    data = yaml.load(yaml_question_sample, Loader=yaml.SafeLoader)
    myQuestion = Question(data)
    comments, input_comments = generate_data()
    myQuestion.add_comments(input_comments[:2])
    myQuestion.add_comments(input_comments[-1])
    assert myQuestion.comments == " ".join(comments)

def test_remove_ta_comments():
    comments, input_comments = generate_data()
    input_comments += ["-  %% this is something %%  ", "- " ]
    assert remove_ta_internal_comments(input_comments) == comments

def test_section_init():
    data = yaml.load(yaml_section_sample, Loader=yaml.SafeLoader)
    mySection = Section(data)
    assert mySection.title == "section title"
    assert mySection.Questions[1].manual == 7
    assert mySection.Questions[1].title == 'title question 1'
    assert mySection.total == 0

def test_assignment_init():
    with open(TEST_DATA / 'config_marks.yaml', 'r') as ff:
        data = yaml.load(ff.read(), Loader=yaml.SafeLoader)
    myAssignment = Assignment(data)
    assert len(myAssignment.Sections) == 3
    assert {'git', 'load', 'evolution'} == set(myAssignment.Sections)

def test_assignment_load_results():
    with open(TEST_DATA / 'config_marks.yaml', 'r') as ff:
        data = yaml.load(ff.read(), Loader=yaml.SafeLoader)
    myAssignment = Assignment(data)
    myAssignment.load_results(TEST_DATA / 'sample_automated_results.json', TEST_DATA / 'sample_manual_summary.json')
    assert myAssignment.meta['student'] == "2681653"
    lines_output = f"{myAssignment!r}".splitlines()
    assert len(lines_output) == 2 + 10 + 7 # 2 titles, 3 sections, 7 subsections, 7 comments
    #assert False


def test_manual_grad_init():
    mgrad = Manual_grad(TEST_DATA / 'sample_manual_summary.json')
    assert mgrad.student == "2681653"
    assert mgrad.manual_score == -4
    assert mgrad.auto_score == 5
    assert mgrad.comments == "Variable names are not meaningful"
    #assert mgrad.components == {"Git": 5}

def test_auto_grad_init():
    agrad = Auto_grad(TEST_DATA / 'sample_automated_results.json')
    assert len(agrad.components) == 6

def test_texify_comments():
    nocomments = {"no_comments": ""}
    assert texify_comments(nocomments.values()) == ''
    assert not texify_comments(nocomments.values())


# FIXME why I get many decimals?
