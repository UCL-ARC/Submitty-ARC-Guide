================
Instructor Guide
================

Requests and Create Course
==========================


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
"Grade Reports" page in the left bar menu for the course you want to collect the
marks from. This button doesn't generate anything "visible", it only will tell
you when was the last time run. In the background, it generates a file for each
submission that we will use to combine marks and generate feedback reports.

.. note::
   If you only need to download the numeric final mark, then generating the
   downloadable CSV Report will provide that for each of the assignments. This
   won't export the feedback or break down of the marks.

Next step is to collect all the details for each gradeable. For that we need to run
a script on the Submitty machine. SSH into it and run ``grades_extractor``.

.. code-block:: bash

   submitty$ grades_extractor -c <coursename> -a <assignment>


This generates a ``results_<assignment>.tar.bz2`` file. Download that file locally to
process it.

.. code-block:: bash

   local$ rsync -azvh submitty:~/results_<assignments>.tar.gz .
   local$ tar jxvf results_<assignment>.tar.bz2


Now in your local computer you'd have a directory ``results_<assignment>`` containing
directories for each submission (with the student id), and each containing two files:
``<studentId>_automated.json`` and ``<studentId>_manual.json``.






.. _Grades summary: https://submitty.org/instructor/course_settings/rainbow_grades/#grades-summaries
