#!/usr/bin/env python

""" Generate report in HTML for project selections
"""

import itertools
import sys
import csv
from projectutils import *
import logging
import datetime
from collections import defaultdict
from functools import partial
import jinja2

def valid(choice):
    return choice.isdigit()

def unlist(l):
    """ Take the first element out of a list if there is only one element 
        We assume that the item is indexable
    """
    return l if len(l) > 1 else l[0]

def astuple(l):
    """ Ensure the thing we return is a tuple, 
        either by converting to tuple or by encapsulating the element 
    """ 
    return tuple(l) if type(l) in (list, tuple) else (l,)

def lookuptable(t, keys, values, default=None):
    """ Construct a lookup table from table t, using rows from keys to index the values in values
        The idea is to call lookuptable(t, "Keyrow", "valrow") to build a simple lookup table
        it also allows to use tuples for keys or values or both to build two-d lookups as in
        lookuptable(t, ("Keyrow1", "Keyrow2"), "valrow"), which returns a dictionary with tuple keys.
    """
    if default is not None:
        constructor = partial(defaultdict, lambda: default)
    else:
        constructor = dict
    return constructor([unlist(tuple([row[i] for i in astuple(l)])) for l in [
        keys, values]] for row in t)

def mean(arr):
    return float(sum(arr))/float(len(arr)) if len(arr) != 0 else 0

def photopath(s):
    return '../photos/%s.jpg' % s

moduledir, outdir, outfilename = sys.argv[1:]

outfile = open(outfilename, 'w')

lecttable = table(moduledir, 'lecturers')
lecturers = sorted(lecttable.column('Code'))
maxperlecturer = lookuptable(lecttable, 'Code', 'Max')

projecttable = table(moduledir, 'projects')
projects = sorted(projecttable.column('Code'))
projectdescriptions = lookuptable(projecttable, 'Code', 'Title', default='')
minperproject = lookuptable(projecttable, 'Code', 'Min')
maxperproject = lookuptable(projecttable, 'Code', 'Max')

ignorestudents = table(outdir, 'ignore').column('Number')
studentfilter = lambda row: row['Number'] not in ignorestudents

studenttable = table(moduledir, 'students')
studenttable.filter(studentfilter)
studentnames = lookuptable(studenttable, 'Number', 'Name')
students = studenttable.column('Number')
students.sort(key=lambda s: studentnames[s])
marks = lookuptable(studenttable, 'Number', 'Mark')

choices = lookuptable(table(outdir, 'selections'), ('Number', 'Code'),
                      'Choice', default='.')
assignments = lookuptable(table(outdir, 'assignments'),
                          ('Student', 'Project') , 'Assigned')

# Handle preassignments
preassignedtable = table(moduledir, 'preassigned')

for key in preassignedtable.columns(('Number', 'Code')):
    choices[key] = 'P'

for key in choices:
    if choices[key] == 'Veto':
        choices[key] = 'V'

selected = []
projectsbystudent = defaultdict(lambda: '')
studentsbyproject = defaultdict(lambda: [],
                                [[p, s] for s, p in assignments.keys()
                                 if assignments[s,p] == 1])
nstudentsbyproject = defaultdict(int,
                                 [(p, len(studentsbyproject[p])) for p in projects])

studentsbylecturer = {l: [] for l in lecturers}
choicesbylecturer = {l: [] for l in lecturers}

for s in students:
    for p in projects:
        l = Project(p).lecturer
        if l in choicesbylecturer:
            choicesbylecturer[l].append(choices[(s, p)])
        else:
            choicesbylecturer[l] = [choices[(s, p)]]
        if assignments[(s,p)] == "1":
            projectsbystudent[s] = p
            studentsbyproject[p].append(studentnames[s])
            selected.append(p)
            studentsbylecturer[l].append(s)
nstudentsbyproject = defaultdict(int,
                                 [(p, len(studentsbyproject[p])) for p in projects])

newclass = {True: 'class="newgroup"', 
            False: ""}



# Outputs
def getlect(p):
    return Project(p).lecturer

c = dict((key, len(list(vals))) for (key, vals) in itertools.groupby(projects, getlect))
lecturers = sorted(c.keys())

def tdstyle(s, p):
    key = (s,p)
    if choices[key] == '.':
        style = 'unselected'
    elif choices[key] == 'V':
        style = 'veto'
    elif choices[key] == 'P':
        style = 'preassigned'
    elif int(choices[key]) <= 5:
        style = 'good'
    elif int(choices[key]) > 7:
        style = 'bad'
    else:
        style = 'selected'

    if assignments.get(key, '0') == '1':
        style += 'assigned'
    else:
        style += 'unassigned'
    return style

flatmarks = [float(marks[s]) for s in students if s in marks]
classavg = mean(flatmarks)
def markbar(m):
    return "<span class='bar'>" + ','.join("%2.1f" % (i-classavg) for i in m)

choicesbystudent = dict([(s, choices[(s, projectsbystudent[s])]) for s in students])

def marksbychoice(choice):
    return sorted([float(marks[s]) for s in students
                   if choicesbystudent[s] == str(choice)])

def popscore(f):
    return 1/f if f > 0 else 1

def statisticsbylecturer(l):
    m = sorted([float(marks[s]) for s in studentsbylecturer[l]])
    markavg = mean(m)
    msparkline = markbar(m)
    vetos = [i for i in choicesbylecturer[l] if i == 'V']
    nvetos = len(vetos)
    projectsbylecturer = [p for p in projects if Project(p).lecturer == l]
    nprojects = len(projectsbylecturer)
    preassignments = sum(1 for key in choices 
                           if choices[key] == 'P' and key[1] in projectsbylecturer)
    nassigned = nprojects - preassignments
    if nassigned > 0:
        popularity = sum([popscore(float(i)) 
                          for i in choicesbylecturer[l] 
                          if valid(i)])/float(nassigned)*10
    else:
        popularity = 0

    return m, markavg, msparkline, preassignments, popularity, nvetos, nprojects

def statisticsbyproject(p):
    popularity = sum(popscore(float(choices[(s, p)])) for s in students if choices[(s,p)].isdigit())
    thesemarks = sorted(float(marks[s]) for s in students if choices[(s,p)].isdigit())
    meanmarks = mean(thesemarks)
    mb = markbar(thesemarks)
    breakdowncounts = [sum(choices[(s, p)]==str(i) for s in students) for i in breakdownvalues]
    return popularity, meanmarks, mb, breakdowncounts

breakdownvalues = ['P'] + [str(i) for i in range(1, 11)] + ['V']

template = jinja2.Template(open('templates/report.html', 'r').read())
templateoutput = template.render(datetime=datetime,
                                 c=c,
                                 projects=projects,
                                 students=students,
                                 studentnames=studentnames,
                                 projectsbystudent=projectsbystudent,
                                 choices=choices,
                                 Project=Project,
                                 selected=selected,
                                 lecturers=lecturers,
                                 studentsbyproject=studentsbyproject,
                                 projectdescriptions=projectdescriptions,
                                 minperproject=minperproject,
                                 nstudentsbyproject=nstudentsbyproject,
                                 maxperproject=maxperproject,
                                 tdstyle=tdstyle,
                                 classavg=classavg,
                                 markbar=markbar,
                                 sorted=sorted,
                                 flatmarks=flatmarks,
                                 choicesbystudent=choicesbystudent,
                                 marksbychoice=marksbychoice,
                                 len=len,
                                 popscore=popscore,
                                 statisticsbylecturer=statisticsbylecturer,
                                 photopath=photopath,
                                 studentsbylecturer=studentsbylecturer,
                                 breakdownvalues=breakdownvalues,
                                 statisticsbyproject=statisticsbyproject,
                                 marks=marks,
                                 float=float,
                                 int=int,
                                 getlect=getlect,
                                 maxperlecturer=maxperlecturer)
outfile.write(templateoutput)

summ = csv.writer(open(os.path.join(outdir, 'summary.csv'), 'w'))
summ.writerow(['Student', 'Name', 'Mark', 'Project Assigned', 'Choice', 'Description'])
for s in students:
    p = projectsbystudent[s]
    summ.writerow([s, studentnames[s], marks[s], p, choices[(s, p)], projectdescriptions[p]])

