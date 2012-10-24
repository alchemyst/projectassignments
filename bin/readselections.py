#!/usr/bin/env python
import sys
import xlrd
import csv
import os
import getopt

maxchoice = 10
vetovalue = "Veto"

def isnumeric(selection):
    return type(selection) is not str

def clean(selection):
    return int(selection) if selection <= maxchoice else vetovalue

def checkselections(selections):
    message = ''
    # All numbers
    numbers = range(1, maxchoice+1)
    counts = [len([i for i in selections if isnumeric(i) and i == n]) for n in numbers]
    missing = [numbers[i] for i, c in enumerate(counts) if c == 0]
    if missing:
        message += ' Missing: ' + ' '.join(map(str, missing))
    dups = [numbers[i] for i, c in enumerate(counts) if c > 1]
    if dups:
        message += ' Duplicate: ' + ' '.join(map(str, dups))
    message += ' Vetos: ' + str(len([i for i in selections if i > maxchoice]))
    # No repeats
    # Number of vetos
    return message

optlist, args = getopt.getopt(sys.argv[1:], 'o:')
options = dict(optlist)

outfilename = options.get('-o', 'selections.csv')
outfile = csv.writer(file(outfilename, 'w'))
outfile.writerow(('Number', 'Code', 'Choice'))

for f in args:
    if not os.path.exists(f): continue
    print f, "...",
    student = os.path.basename(f).split('.')[0].lower()
    data = xlrd.open_workbook(f).sheet_by_index(0)
    # FIXME: location shouldn't be so brittle
    valid, version = (data.cell_value(3, 1), data.cell_value(0, 5))
    print student, valid, version, data.nrows, "rows", 
    selections = []
    for i in range(21, data.nrows):
        selection = data.cell_value(i, 1)
        project = data.cell_value(i, 0).strip()
        if isnumeric(selection):
            selections.append(selection)
            outfile.writerow((student, project, clean(selection)))
    print checkselections(selections),
    print "done"
    
