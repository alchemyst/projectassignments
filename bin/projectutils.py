import os
import csv
import logging

class Project:
    def __init__(self, string):
        self.string = string
        self.lecturer = string.rstrip('0123456789')
        self.number = int(string[len(self.lecturer):])

    def astuple(self):
        return (self.lecturer, self.number)

    def __repr__(self):
        return "%s%i" % self.astuple()

    def __str__(self):
        return self.__repr__()

    def __cmp__(self, other):
        return cmp(self.astuple(), other.astuple())

def commentline(line):
    return not line.startswith('#')
    
class table:
    def __init__(self, dirname, filename):
        fullname = os.path.join(dirname, filename + '.csv')
        self.data = list(csv.DictReader(filter(commentline, open(fullname))))
        
    def column(self, name):
        return [row[name] for row in self.data]
    
    def columns(self, names):
        return [tuple(row[name] for name in names) for row in self.data]
    
    def filter(self, fun):
        self.data = filter(fun, self.data)
    
    def __iter__(self):
        return iter(self.data)

