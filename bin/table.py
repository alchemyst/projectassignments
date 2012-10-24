#!/usr/bin/python

import sys

onezero = {True: "1", False: "0"}

assignmentfile = file(sys.argv[1])
projectfile = file(sys.argv[2])

assignments = dict([line.strip('\n').split('\t') for line in assignmentfile])
allprojects = [i.strip() for i in projectfile.readline().split('\t')[1:]]

print "Proj\t" + "\t".join(allprojects)

for key in sorted(assignments.keys()):
    print key + "\t" + "\t".join([onezero[assignments[key]==p]
                                  for p in allprojects])

assignmentfile.close()
projectfile.close()
