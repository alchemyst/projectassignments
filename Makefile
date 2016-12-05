model = assignment.mod
#module = csc411_2013
outdir = $(module)/output
out = $(outdir)/selections

ifndef module
$(error You need to define the module environment variable to point to the directory that you want to build)
endif

# These are all the "Inputs" into the system expressed as CSV files in the module directory
moduletables := $(foreach table,lecturers students projects preassigned parameters,$(module)/$(table).csv)
# These are the "Output" tables
outputtables := $(foreach table,assignments selections,$(outdir)/$(table).csv)

#selections = $(module)/selections/*.xls

all: $(outdir)/report.html $(outdir)/upload.csv

$(out).csv: $(module)/selections.csv
	[ -e $(outdir) ] || mkdir $(outdir)
	cp $^ $@

# Mathprog data file
$(out).dat: $(out).csv $(moduletables) bin/makedata.py
	bin/makedata.py $(module) $(outdir) $@

# Result of assignment run
$(outdir)/assignments.csv: $(out).dat $(model)
	glpsol --model $(model) --data $(out).dat --log $(outdir)/runlog.txt
	mv assignments.csv $@

# File for upload to website
$(outdir)/upload.csv: $(outdir)/assignments.csv
	echo Student ID,Project ID > $@
	grep '1$$' $< | tr -d \" | cut -d , -f 1,2 >> $@

# Reporting
$(outdir)/report.html: templates/report.html $(out).csv $(moduletables) $(outputtables) bin/report.py
	bin/report.py $(module) $(outdir) $@
	cp wwwbase/* $(outdir)

# Phony targets: really just actions rather than actual targets

clean:
	-rm $(outdir)/*

executable:
	-chmod +x bin/*

selections:
	bin/downloadmailattachments.py $(module)/selections

missing:
	cut -d , -f 4 $(module)/preassigned.csv | cat - $(outdir)/selections.csv | cut -d , -f 1 | grep -v -f - $(module)/students.csv | cut -d , -f 1,2,3 | tr -d \" | column -t -s, | nl

analysis:
	bin/analyse $(out).dat $(outdir)/analysis.dat

#.INTERMEDIATE:

.PHONY: clean executable selections missing analysis
