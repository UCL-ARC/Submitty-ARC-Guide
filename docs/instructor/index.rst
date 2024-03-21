================
Instructor Guide
================

Request and Create Course
=========================


Create assignment
=================


Grade assignments
=================


Release grades
==============

Once the automated and manual grading has been completed in Submitty, we can
proceed to release the grades. We need to extract the marks from submitty,
combine the manual and automated grades according to your needs, generate the
feedback reports and combine them with Moodle's grade list.

Collect marks from Submitty
---------------------------

To be able to collect the combine marks from Submitty, first we need to generate
`Grades summary`_. This is done by clicking "Generate Grade Summaries" under the
:fab:`chart-bar` "Grade Reports" page in the left bar menu for the course you want to collect the
marks from. This button doesn't generate anything "visible", it only will tell
you when was the last time run. In the background, it generates a file for each
submission that we will use to combine marks and generate feedback reports.

.. note::
   If you only need to download the numeric final mark, then generating the
   downloadable CSV Report will provide that for each of the assignments. This
   won't export the feedback or break down of the marks.

Next step is to collect all the details for each gradeable. For that we need to run
a script on the Submitty machine. SSH into it and run ``grades-extractor``.

.. code-block:: bash

   submitty$ grades-extractor -c <coursedirectory> -a <assignment> -o <output>


For example, from your home:

.. code-block:: bash
   submitty:~$ ls
   2324_comp0233_marking@
   submitty:~$ grades-extractor -c 2324_comp0233_marking -a cw01 -o ./results/COMP0233/23-24


This generates a ``results_<year>_<course>_<assignment>.tar.bz2`` file. Download that file locally to
process it.

.. code-block:: bash

   local$ rsync -azvh submitty:~/results_<year>_<course>_<assignment>.tar.bz2 .
   local$ tar jxvf results_<course>_<assignment>.tar.bz2


Now in your local computer you'd have a directory ``results_<course>_<assignment>`` containing
directories for each submission (with the student id), and each containing two files:
``<studentId>_automated.json`` and ``<studentId>_manual.json``.


Combine grades
--------------

To combine the automated and manual grades we need to decide how (i.e., which
questions are "the same", what weight has to be produced to the marks, etc.).
This decision is encoded in the configuration YAML file that you may have used
to generate the rubric, its content is like what's shown below. Note, that some
questions has a ``manual`` or ``auto`` factor. These are the factor multiplied
to the manual or auto marks to obtain the real grade (this is done because
Submitty can only jump on 0.5 steps).

.. code-block:: yaml

   meta:
     department: "Department name"
     course: "Module name"
     course_code: "ModCode001"
     lecturers:
       - "Clare Green"
       - "John Smith"
     title: "Coursework title"
     description: >-
       This assignment ...
     dates:
       handed: May 21st, 2025
       deadline: July 2nd, 2025
     marks: 100
     submitty_type: "assignment"
     submitty_id: cw1
   sections:
     section1:
       title: "First section"
       description: "what's about"
       marks: 10
       stitle: "submitty title"
       remove: "SECT 1" # What to remove from submitty title
       Question 1:
         title: "SECT 1: a. the part of numbers"
         marks: 6
         manual: 6
         auto: 0
       Question 2:
         title: "SECT 1: b. the part of letters"
         marks: 4
         manual: 0
         auto: 4
     section2:
       title: "Second section"
       description: "what's difficult"
       marks: 7
       stitle: "submitty title"
       remove: "SECT 1" # What to remove from submitty title
       Question 1:
         title: "SECT 1: a. the part of numbers"
         marks: 3
         manual: 6
         auto: 0
         manual_factor: 0.5
       Question 2:
         title: "SECT 1: b. the part of letters"
         marks: 4
         manual: 2
         auto: 4
         auto_factor: 0.5

.. note::
   If you don't have a yaml file, you can generate one using ``rubric-convert`` and
   answering its questions. Note that at the moment this only works for the manual parts.


If you've got a ``penalties.csv`` file recording manual interventions (like
fixing git repositories, variables names, etc) to make it run, then that file
should have three columns named: ``submission_id``, ``points`` and ``reason``.
Where the values in ``points`` are "penalties" if they are negative numbers.

With the config file and the optional penalties one we can proceed to combine
the automate and manual grades.

This is done with the ``grades-combine`` command. For example:


.. code-block:: bash

   local$ grades-combine -r results_<year>_<course>_<assignment>/ -c config_<assignment>.yaml -o output -s -p penalties.csv


for example:

.. code-block:: bash

   local$ ls
   5665793  5665795  5665797  5665799  5665801  5665804
   local$ ls ..
   cw1_components.yaml  cw1_penalties.csv  results_2324_ARC0001_cw1
   local$ grades-combine -r . -c ../cw1_components.yaml -o output -s -p ../cw1_penalties.csv
   min2nd_mark=5, fix2nd_mark=6, extra_2nd_mark=0
   local$ ls
   5665793  5665795  5665797  5665799  5665801  5665804  output
   local$ ls output
   5665793.tex  5665795.tex  5665797.tex  5665799.tex  5665801.tex  5665804.tex  results.csv

This command with generate a set of files under the ``output`` directory.
``results.csv`` includes the normalised marks and marks which ones need to be
second marked. Check the output of the command to know how many more needs to be
reviewed. For example:

   min2nd_mark=5, fix2nd_mark=4, extra_2nd_mark=1


This says that there's a minimum of 5 assignments to review, and 4 have been
already fixed (due to the `second marking`_ sampling rules). The process followed
for programming coursework is sampled, check marking and open.


The other output files generated by ``grades-combine`` are the latex files (and
other needed files) to generate the reports.

``greades-combine`` may need to be rerun if the marks have changed during second
marking.

Generate grades
---------------

The next step adds the marks to Moodle's worksheet.

The command to add the marks to the worksheet is as follows:

.. code-block:: bash

   local$ grades-generate "Grades-CourseCode_YY-YY-Coursework X title-id.csv" results.csv


This file will merge the ``results.csv`` obtained before with the worksheet. It
does it into two files, with late submission penalties and without them. The
CS department takes care of the late submissions penalty, so we only need to care
about the ``nopenalty.csv`` file.

.. _Grades summary: https://submitty.org/instructor/course_settings/rainbow_grades/#grades-summaries
.. _second marking: https://www.ucl.ac.uk/academic-manual/chapters/chapter-4-assessment-framework-taught-programmes/section-7-marking-moderation#7.6_
