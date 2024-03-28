================
Maintainer guide
================


Create course
-------------

To create a course we use our admin account. In its home directory there's a
``courses`` directory with a ``course_code/yyyy-yyyy`` directory structure.
For a new course or instance we do as follows:

.. code-block:: bash

   submitty:~$ mkdir -p courses/comp0000/2023-2024


There will be save a yaml file (e.g., ``comp0000_marking.yaml``) with the
details of the course. This will have the following shape:

.. code-block:: yaml

   course: comp0000_marking # Note all lower case!
   semester: 232 # year-semester
   semester_name: spring24 # semester name autumn23/spring24/summer24
   date_start: 2024-01-01
   date_end: 2024-05-10
   section: section1  # which sections to create
   instructor:
     ucasper:  # ucl login name
       firstname: David
       lastname: PS
       email: d.perez-suarez@ucl.ac.uk
       password: # a random generated password
       sshkey: "ssh-rsa ..." # ssh public key to provide ssh access
     <any other instructor>
   ta:  # graders assitants
     ccabcd:
       firstname: Charlie
       lastname: Ab
       email: ccabcd@ucl.ac.uk
       password: # randome password
     <any other ta>



With that file in that folder we can create the course and add the needed accounts to it.
If a user already existed, then their password will be reset to the one in that file.

Now we can execute the script to create the course:


.. code-block:: bash

   submitty:~/courses$ sudo python3 create_course.py comp0000/2023-2024/comp0000_marking.yaml
   To build a section go into ~instructor/2324_comp0000_marking and run:
      ./BUILD_comp0000_marking.sh [exercise]


That will create the course, the users, the folders and the softlinks into the
instructors home directories to build the assignments when updated.

Adding students to the course
-----------------------------

This can be done by the instructor. Check that :ref: `information on the instructor page<addStudents>`



Upload files for a gradeable
----------------------------

Once we've got the files from the assignment, a folder such like the ones in `Submitty-assignments <https://github.com/UCL-ARC/submitty-assignments>`_.
We can upload it to our admin account as:


.. code-block:: bash

   local:~/courses$ rsync -azvhL 01_gradeable submitty:~/courses/comp0000/2023-2024



Normally we will need to build the docker container for that gradeable.

.. code-block:: bash

   submitty:container_mylanguage$ sudo docker build -t submitty/mylanguage_ubuntu22:2024_04 .



The config files (json and any provided script that needs to run when building) needs to be copied to the ``private_course_repositories`` directory as root:


.. code-block:: bash

   submitty:~# cd /var/local/submitty/private_course_repositories/comp0000_marking/232/
   submitty:232# mkdir -p cw1
   submitty:232# cd cw1
   submitty:cw1# cp -r ~apsuarez/courses/comp0000/2023-2024/01_gradeable/container_mylanguage/config .
   submitty:cw1# chown -R ucasper config


From this moment, the gradeable config can be set under the course settings and therefore selected in the gradeable configuration.


