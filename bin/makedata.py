#!/usr/bin/env python

""" 
Generate the .dat file for project assignments 
Input parameters: module directory, output directory and output filename
"""

import sys
import os
import csv
import getopt
import logging
from projectutils import *

logging.basicConfig(level=logging.DEBUG)

defaultpref = '999'
vetopref = '999'
# Exclude "Unresponsive" students who haven't made selections or preassignments?
# WARNING: This may not be supported downstream
onlyresponders = False


#Create the data section of the file
#The following things have to be generated:
#
#$ egrep '^(set|param)' assignment.mod
#
#set student; # set of students
#set project; # set of projects
#set lecturer; # set of lecturers
#param preassigned{s in student, p in project} binary;
#param studpref{s in student, p in project} >= 0;
#param lectpref{l in lecturer, p in project} >= 0;
#param studentweight <= 1 >= 0; 
#param belongs{l in lecturer, p in project} binary;
#param lectmax{l in lecturer} >= 0;
#param lectmin{l in lecturer} >= 0;
#param projmax{p in project} >= 0;
#param projmin{p in project} >= 0;
#param mark{s in student} >= 0;
#param markc;
#param markm;


# TODO: Extract to ampltools
class amplbase:
    def __len__(self):
        return len(self.values)

class ampldata(amplbase):
    def __init__(self, values=[]):
        self.values = values
        
    def add(self, value):
        self.values.append(value) 

    def addmany(self, values):
        self.values += values
        
    def __str__(self):
        s = "data;"
        for value in self.values:
            s += "\n\n" + str(value) + "\n"
        s += "\n" + "end;\n"
        return s

class amplset(amplbase):
    def __init__(self, name, values=[]):
        self.name = name
        self.values = set(values)

    def add(self, value):
        self.values.add(value)
        
    def addmany(self, values):
        self.values += values
    
    def filter(self, fun):
        self.values = filter(fun, self.values)
    
    def __str__(self):
        return "set " + self.name + " := " +  " ".join(self.values) +  " ;"

class amplparam(amplbase):
    def __init__(self, name, values=[], default=None):
        self.name = name
        self.values = values[:]
        self.default = default

    def add(self, value):
        self.values.append(value)
        
    def filter(self, fun):
        self.values = filter(fun, self.values)
    
    def inferdefault(self):
        """ make default equal to the most common value """
        assert self.default is None, "Will not override default"
        counter = {}
        maxc = 0
        for record in self.values:
            v = record[-1]
            counter[v] = counter.get(v, 0) + 1
            if counter[v] > maxc:
                maxc = counter[v]
                self.default = v
            
    def __str__(self):
        s = "param " + self.name
        if self.default is not None:
            s += " default " + str(self.default) 
        if len(self.values) == 1: # single parameter
            newline = ''
        else:
            newline = '\n'
        s += " := " + newline
        for record in sorted(map(tuple, self.values)):
            if record[-1] != self.default:
                s += " ".join(str(r) for r in record) + newline
        s += ";"
        return s

def fromtable(thetable, items):
    outputs = []
    for constructor, name, fields in items:
        outputs.append([constructor(name), fields])
    for record in thetable:
        for element, fields in outputs:
            if type(fields) is str:
                element.add(record[fields])
            else:
                element.add([record[f] for f in fields])
            
    return [element for element, fields in outputs]

if __name__ == '__main__':
    moduledir, outdir, outfile = sys.argv[1:]
    
    data = ampldata()

    # Process lecturers
    lecturer, lectmin, lectmax = fromtable(table(moduledir, 'lecturers'),
                                           ((amplset, 'lecturer', 'Code'),
                                            (amplparam, 'lectmin', ('Code', 'Min')),  
                                            (amplparam, 'lectmax', ('Code', 'Max'))))
    lectmin.inferdefault()
    lectmax.inferdefault()

    # Process students file
    student, mark = fromtable(table(moduledir, 'students'),
                              ((amplset, 'student', 'Number'),
                               (amplparam, 'mark', ('Number', 'Mark'))))
    mark.default = 0
    
    # Process projects table
    project, projmin, projmax = fromtable(table(moduledir, 'projects'),
                                          ((amplset, 'project', 'Code'),
                                           (amplparam, 'projmin', ('Code', 'Min')),
                                           (amplparam, 'projmax', ('Code', 'Max'))))
    projmin.inferdefault()
    projmax.inferdefault()
    
    logging.info('Building inferred values (belongs and lectpref)')
    
    belongs = amplparam('belongs', default=0)
    lectpref = amplparam('lectpref', default=0)
    for proj in sorted(project.values):
        lect, pref = Project(proj).astuple() 
        belongs.add([lect, proj, 1])
        lectpref.add([lect, proj, pref])
    
    # keep track of which students "responded" by selections or preassignments

    responders = set()

    # Process selections
    studpref = amplparam('studpref', default=defaultpref)
    for row in table(outdir, 'selections'):
        choice = row['Choice']
        if choice == 'Veto': choice = vetopref
        studpref.add((row['Number'], row['Code'], choice))
        responders.add(row['Number'])
    
    # Process preallocation table
    preassigned = amplparam('preassigned', default=0)
    for row in table(moduledir, 'preassigned'):
        preassigned.add([row['Number'], row['Code'], 1])
        existingentries = set('-'.join(v[0:2]) for v in studpref.values) 
        if row['Number'] + '-' + row['Code'] not in existingentries:
            studpref.add([row['Number'], row['Code'], 0])
        responders.add(row['Number'])
        
    # take out the unresponsives
    if onlyresponders:
        logging.info('Removing unresponsives')
        logging.debug('%i students before cull, %i responders' % (len(student), len(responders)))
        setfilter = lambda item: item in responders
        parfilter = lambda item: item[0] in responders

        for struct in (mark, studpref):
            struct.filter(parfilter)
        ignored = set(student.values).difference(responders) 
        student.filter(setfilter)
        logging.info('%i students after cull' % len(student))
    else:
        ignored = []
        
    ignorefile = csv.writer(open(os.path.join(outdir, 'ignore.csv'), 'w'))
    ignorefile.writerows([item] for item in ['Number'] + list(ignored))
   
    # Add to data object to get order right
    
    # Sets
    data.add(student)
    data.add(project)
    data.add(lecturer)

    # matrices
    data.add(preassigned)
    data.add(studpref)
    data.add(lectpref)
    data.add(belongs)
    
    # marks
    data.add(mark)
   
    # min and max
    data.add(lectmin)
    data.add(lectmax)
    data.add(projmin)
    data.add(projmax)
    
    # single parameters 
    for row in table(moduledir, 'parameters'):
        data.add(amplparam(row['Name'], [[row['Value']]]))

    logging.info('Writing data file')
    open(outfile, 'w').write(str(data))
    
