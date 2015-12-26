#!/usr/bin/env python

""" Generate report in HTML for project selections
"""

# TODO: Use an HTML template engine rather than generating all the HTML yourself
# Probably the django template engine

import itertools
import sys
import csv
from projectutils import *
import quicktag as qt
import logging
import datetime
from collections import defaultdict
from functools import partial

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
outfile.write("""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">

<title>Project assignment results</title>
<meta name="description" content="Project assignment results">
<meta name="author" content="Automatic results generator">

<link href="report.css" rel="stylesheet" type="text/css" >
<script type="text/javascript" src="sorttable.js" ></script>
<script type="text/javascript" src="jquery-2.1.1.min.js" ></script>
<script type="text/javascript" src="jquery.sparkline.min.js" ></script>
<script type="text/javascript" src="jquery.fixedheadertable.min.js"></script>
<script type="text/javascript">
/* <![CDATA[ */
$(function() { $('.bar').sparkline('html', {type: 'bar'});
               /*$('.selectionmatrix').fixedHeaderTable({footer: false, 
                                                       cloneHeadToFoot: false, 
                                                       fixedColumn: true }); */
              });
/* ]]> */
</script>
</head>
<body>
""")

def getlect(p):
    return Project(p).lecturer

c = dict((key, len(list(vals))) for (key, vals) in itertools.groupby(projects, getlect))
lecturers = sorted(c.keys())

outfile.write(str(qt.h1('Selections')))
outfile.write(str(qt.p('Report generated on ' + datetime.datetime.now().strftime('%c'))))
outfile.write("<table class='selectionmatrix'>\n")
outfile.write(str(qt.tag('colgroup', [], {'class': 'names'})))
for l in lecturers:
    outfile.write(str(qt.tag('colgroup', [], {'span': c[l], 'class': 'lect', 'id': 'col_'+l})))
outfile.write("<thead>")
outfile.write(str(qt.tr([qt.th()] + [qt.th(l, {'colspan': c[l]}) for l in lecturers])))
outfile.write(str(qt.tr([qt.th('Project')] \
                        + [qt.th(Project(p).number, {'class': 'sel%s' % (p in selected),
                                                     'title': '%s (%s)' % (','.join(studentsbyproject.get(p, [])), projectdescriptions.get(p, ''))})
                                  for p in projects])))
outfile.write(str(qt.tr([qt.td("Min")] + [qt.td(minperproject[p]) for p in projects])))
outfile.write(str(qt.tr([qt.td("Students")] + [qt.td(nstudentsbyproject[p]) for p in projects])))
outfile.write(str(qt.tr([qt.td("Max")] + [qt.td(maxperproject[p]) for p in projects])))
outfile.write(str("</thead>\n"))
outfile.write("<tbody>")
for s in students:
    n = studentnames[s]
    outfile.write('<tr><th class="names" title="%s - %s">%s</th>' % (s, projectsbystudent[s], n))
    for p in projects:
        key = (s,p)
        if choices[key] == '.':
            tdstyle = 'unselected'
        elif choices[key] == 'V':
            tdstyle = 'veto'
        elif choices[key] == 'P':
            tdstyle = 'preassigned'
        elif int(choices[key]) <= 5:
            tdstyle = 'good'
        elif int(choices[key]) > 7:
            tdstyle = 'bad'
        else:
            tdstyle = 'selected'
            
        if assignments.get(key, '0') == '1':
            tdstyle += 'assigned'
        else:
            tdstyle += 'unassigned'
            
        outfile.write('<td class="%s" title="%s - %s">%s</td>' % (tdstyle, n, p, choices[(s, p)]))
    outfile.write("</tr>\n")
outfile.write("</tbody>")
outfile.write("</table>")


flatmarks = [float(marks[s]) for s in students if s in marks]
classavg = mean(flatmarks)
def markbar(m):
    return str(qt.tag('span', "%s" % ','.join(["%2.1f" % (i-classavg) for i in m]), {'class': 'bar'}))

# About the statistics

section = [qt.h1("Statistics with marks"),
           qt.p("Class average: %2.1f" % classavg),
           qt.p("The bar charts indicate student marks minus class average -- red below class avg and blue above."),
           qt.p("For reference, the whole class looks like this: " + markbar(sorted(flatmarks))),
           qt.p("You can click on the headings to sort the tables.")]

outfile.writelines(map(str, section))

# Assignment histogram
# ======================================================================

outfile.write(str(qt.h2("Assignment breakdown")) + '\n')
outfile.write("<table>\n")
outfile.write(str(qt.tr([qt.th('Choice'), qt.th('N'), qt.th('Marks')])))
choicesbystudent = dict([(s, choices[(s, projectsbystudent[s])]) for s in students])
for choice in ['P'] + range(1, 11) + ['.']:
    m = sorted([float(marks[s]) for s in students
                if choicesbystudent[s] == str(choice)])
    outfile.write(str(qt.tr([qt.td(str(choice)),
                             qt.td(len(m)),
                             qt.td(markbar(m))])))
outfile.write("</table>")
    

# Mark summary per lecturer
# ======================================================================
outfile.write(str(qt.h2("Statistics per lecturer")))
outfile.write("\n<table class='sortable'>\n")
outfile.write(str(qt.tr(qt.th(h) for h in ('Lecturer', 'Avg Mark', 'Breakdown', 'Number', 'Vetos', 'Pre', 'Popularity', 'Students'))))


def popscore(f):
    return 1/f if f > 0 else 1

for l in lecturers:
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
    data = [qt.td(l),
            qt.td('%2.1f' % markavg),
            qt.td(msparkline),
            qt.td(len(m)),
            qt.td('%2.1f' % (float(nvetos)/nprojects)),
            qt.td(preassignments),
            qt.td('%2.1f' % (popularity))]

    photos = []
    for s in studentsbylecturer[l]:
        p = projectsbystudent[s]
        title = ' '.join([studentnames[s], p, choices[(s,p)],
                          projectdescriptions[p]])
        photos.append(qt.tag('img', [], {'src': photopath(s),
                                         'alt': studentnames[s],
                                         'title': title,
                                         'width': '40'}))
    data.append(qt.td(photos))
    outfile.write(str(qt.tr(data)))
    
outfile.write("</table>\n")

# Per project
# ======================================================================
outfile.writelines([str(qt.h2('Statistics per project')),
                    str(qt.p("Here, the bar charts are for all the students who selected the project.")),
                    "<table class='sortable'>"])

breakdownvalues = ['P'] + map(str, range(1, 11)) + ['V']
outfile.write(str(qt.tr(map(qt.th, ['Project','Popularity', 'Marks', 'Breakdown'] \
                                    + breakdownvalues + ['Total']) + [qt.th('Title')])))
for p in projects:
    popularity = sum(popscore(float(choices[(s, p)])) for s in students if choices[(s,p)].isdigit())
    data = [qt.td(p), qt.td('%2.1f' % (popularity))]
    thesemarks = sorted(float(marks[s]) for s in students if choices[(s,p)].isdigit())
    data += [qt.td("%2.1f" % (mean(thesemarks))),
             qt.td(markbar(thesemarks))]
    data += [qt.td(sum([choices[(s, p)]==str(i) for s in students])) for i in breakdownvalues]
    data.append(qt.td(len(thesemarks)))
    data.append(qt.td(projectdescriptions[p]))
    outfile.write(str(qt.tr(data)))
                 
outfile.write("</table>\n")

# ======================================================================
outfile.writelines([str(qt.h2('Student satisfaction')),
                    str(qt.p('Who got their first choice, what were their marks, who got bad choices?')),
                   "<table class='sortable'>",
                   str(qt.tr(qt.th(k) for k in ('Number', 'Name', 'Mark', 'Choice', 'Project')))])
for s in students:
    p = projectsbystudent[s]
    outfile.writelines(str(qt.tr(qt.td(k) for k in (s, studentnames[s], "%2.1f" % float(marks[s]), choices[(s, p)], p))))
outfile.write("</table>\n")

# ======================================================================
outfile.writelines([str(qt.h2('Open projects')),
                    str(qt.p('Which projects can still be assigned without violating constraints'))])

outfile.write('<table>\n')
outfile.write(str(qt.tr([qt.th('Project'), qt.th('Description')])))
outfile.writelines([str(qt.tr([qt.td(p), qt.td(projectdescriptions[p])]))
                    for p in projects
                    if nstudentsbyproject[p] < int(maxperproject[p]) and len(studentsbylecturer[getlect(p)]) < int(maxperlecturer[getlect(p)])])
outfile.write('</table>\n')


# ======================================================================

# outfile.write(str(qt.h2('Choice battles')) + '\n')
# choicesbystudent = {}
# choicelist = []
# for s in students:
#      choicesbystudent[s] = [(choices[(s, p)], p) for p in projects
#                            if choices[(s, p)] in map(str, range(1,11)) and 1 <= int(choices[(s, p)]) <= 10]
#      choicelist.append([choicesbystudent[s], s])

# for c, s in sorted(choicelist):
#     print >> outfile, c,
       

# ======================================================================
#outfile.write(str(qt.h2("Project correspondence")))
#outfile.write(str(qt.p("Of the students who selected project i, what percentage also selected project j?")))
#
#def studentswhochose(p):
#    return set(s for s in students if choices[(s, p)].isdigit())
#
#chosenprojects = [p for p in projects if len(studentswhochose(p)) > 0]
#
#outfile.write("\n<table class=sortable>\n")
#outfile.write(str(qt.tr([qt.th()] + [qt.th(p) for p in chosenprojects])))
#for pi in chosenprojects:
#    studentsi = studentswhochose(pi)
#    ni = len(studentsi)
#    outfile.write("<tr>" + str(qt.th(pi)))
#    for pj in chosenprojects:
#        if ni == 0 or pi is pj:
#            print >> outfile, qt.td('-')
#        else:
#            nij = len(studentsi.intersection(studentswhochose(pj)))
#            print >> outfile, qt.td("%3i" % (100*nij/ni))
#    outfile.write("</tr>\n")
#        
#outfile.write("</table>\n")

#g = nx.Graph()
#for ((s, p), c) in choices.iteritems():
#    if c not in ('.', 'X') and float(c) < 3:
#        g.add_weighted_edges_from([(s, p, 1/float(c))])
#       
#print >> outfile, nx.connected_components(g)

print >> outfile, "</body></html>"

summ = csv.writer(open(os.path.join(outdir, 'summary.csv'), 'w'))
summ.writerow(['Student', 'Name', 'Mark', 'Project Assigned', 'Choice', 'Description'])
for s in students:
    p = projectsbystudent[s]
    summ.writerow([s, studentnames[s], marks[s], p, choices[(s, p)], projectdescriptions[p]])

