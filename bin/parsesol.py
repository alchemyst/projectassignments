#!/usr/bin/env python

import sys
import re

f = open(sys.argv[1])
assignedre = re.compile('.*assigned\[(.*),(.*)\].*\*\s*1')
while True:
    try:
        firstline = f.next()
        if " assigned" in firstline:
            assignedline = firstline.strip() + f.next()
            match = assignedre.match(assignedline)
            if match:
                print '\t'.join(match.groups())
    except StopIteration:
        break
    
