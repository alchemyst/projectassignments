Project Assignment Tool
Author: Carl Sandrock

1. Introduction

This directory contains tools to assign students to projects.  To use
it, you need to have the following tools installed:
- GNU make
- glpk (this is what ends up solving the question).
- python
- jinja2 for html report templating

I have set up some conventions for naming projects so that the system
can infer information from the project names.  Each project consists
of letters followed by numbers.  The letters are assumed to be names
or initials of the project leaders and the numbers are assumed to give
the project number.  The numbers do not have to be in any particular
order and may have gaps, although there is an option to use the order
of projects to infer a "lecturer preference".

When you get the project, make sure that all the executables are
runnable, by running

$ make executable 


2. The process

In overview, the assignment process is
- Place constraints on assignments for lecturers and projects
- Get choices from students 
- Compile choices into one table
- Solve the linear programming problem
- Post process the data

2.0 Set up information files

All of the project's files will live in "module directory".  Choose a
name that makes sense to you.  I use modulename_year.  All the files
you read about here will be relative to the module directory.  The
students selections will go in the "selections" directory and the output
of the program will go in the "output" directory.

You can use the "modulebase" directory as a template.  It already has
the right directories and a couple of example files in it.  The CSV python
module is used to parse these files, so they should be fine to edit
with spreadsheet programs.  The CSV files are referred to as "tables",
as there is a long-term plan to move this information to a database.

Module tables:
Table name	Required fields		Example content
lecturers	Code,Min,Max		PV,1,2
students	Number,Name,Mark	s29232232,POGGENPOEL K,90
projects	Code,Min,Max,Title	PV1,0,1,"Short title"
preassigned	Code,Number		PV1,s29232232

parameters is a special table that contains Name,Value fields for
internal parameters of the program.  Look at assignment.mod for
details on what they mean.

Example:
Name,Value
markc,1
markm,0.01
studentweight,0.95

Output tables:
selections
assignments

2.1 Fill in information

Edit the CSV files constraints.dat so that they reflect the
constraints and paramaters correctly.

2.2 Get choices from students

You can use the website to generate these files as well.

TODO: Update this document to reflect the correct workflow from the website.

To get choices from students, you modify the projectchoices.xls file
from the template.  Important points to remember are that the checks
in the spreadsheet use named ranges -- you need to define these ranges
correctly in the spreadsheet for it to work.  I also recommend that
you protect the spreadsheet to avoid accidental changes.  Don't bother
with a protect password -- you can crack it in minutes and you'll
probably forget it.

Now, each student fills in this file and hands it in in some way.  You
then place one file per student sXXXX.xls in the "selections"
directory.

If you want to rename directories created by a ClickUP zip file,
download the class list from the class tool and save it somewhere.
Now go into selections and execute "../bin/renamefromfile somewhere".
This should rename from the long directory names to student number
based directory names.

You can also have them send an e-mail, which you can download by doing 
make selections.  Modify the file bin/downloadmailattachments.py to
change how the mails are handled.

2.3 Solve the linear programming problem and postprocess the data

Run 

$ module=XXX make

This will compile all the selections, solve the problem and
do post processing, placing the result in assignments.csv.  A nice
report is in report.html.

3. Analysis

# FIXME: Not working at the moment
The "analyse" script does parameter sweeps to determine the average
unhappiness of the students with various parameters designed to meet
the needs of the lecturers.

