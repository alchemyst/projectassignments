/* attempt to assign students to projects */
set student; # set of students
set project; # set of projects
set lecturer; # set of lecturers

/* is student s assigned to project p? */
var assigned{s in student, p in project} binary;
var students_per_lecturer{l in lecturer};
var Ngood{l in lecturer};

param maxselection >=0;

/* Minimum percentage of "good" students (above class average mark 
 * per lecturer 
 */
param mingood >= 0;

/* pre-assignments */
param preassigned{s in student, p in project} binary;

/* student's preference */
param studpref{s in student, p in project} >= 0;

/* lecturer's preference */
param lectpref{l in lecturer, p in project} >= 0;

/* interpolation constant between lecturer preference function and
student preference, expressed as student weight */
param studentweight <= 1 >= 0; 

/* lecturer's projects */
param belongs{l in lecturer, p in project} binary;

/* maximum projects per lecturer */
param lectmax{l in lecturer} >= 0;

/* mimumum projects per lecturer */
param lectmin{l in lecturer} >= 0;

/* maximum allocation of projects */
param projmax{p in project} >= 0;

/* minimum allocation of projects */
param projmin{p in project} >= 0;

/* take student marks into account */
param mark{s in student} >= 0;

/* linear weighting function markm*mark + c
   set markc to 0 and c to 1 for no effect */
param markc;
param markm;

/* calculated variables */
param nstudents := sum{s in student} 1 ;

param averagemark := sum{s in student} mark[s] / nstudents;

param goodstudent{s in student} := if mark[s] > averagemark then 1 else 0;

/* Goal */
minimize unhappiness: studentweight*(sum{s in student, p in project} assigned[s,p] * (studpref[s,p] * (markm*mark[s] + markc)))
                + (1-studentweight)*(sum{s in student, l in lecturer, p in project} assigned[s,p]*belongs[l,p]*lectpref[l,p]);

/* Checks */
/* Minimum projects > number of students */
check nstudents <= sum{p in project} projmax[p];
check nstudents >= sum{l in lecturer} lectmin[l];
check nstudents <= sum{l in lecturer} lectmax[l];

/* Constraints */
/* Every student assigned only once */
s.t. studentsassigned{s in student}: 
        sum{p in project} assigned[s,p] = 1;
/* pre-assignments */
s.t. preassignments{s in student, p in project}:
        assigned[s,p] >= preassigned[s,p];
/* Projects assigned within their limits */
s.t. projectassigned{p in project} : 
        projmin[p] <= sum{s in student} assigned[s,p] <= projmax[p];
/* Lecturers getting within their limits */
s.t. students_per_lect{l in lecturer}:
     students_per_lecturer[l] = sum{p in project, s in student} if belongs[l, p] then assigned[s,p] else 0;
s.t. lectotal{l in lecturer} : 
        lectmin[l] <= students_per_lecturer[l] <= lectmax[l];
/* Limit worst case selection */
s.t. worstcase{s in student, p in project}:
     studpref[s,p]*assigned[s,p] <= maxselection;
/* Give every lecturer mingood good students */
s.t. ngood{l in lecturer}:
     Ngood[l] = sum{s in student, p in project} belongs[l,p]*assigned[s,p]*goodstudent[s];
s.t. goodstudents{l in lecturer}:
     Ngood[l] >= mingood * students_per_lecturer[l];

solve;

/* stats */
printf "------------ Run inputs ---------\n";
printf "Number of students:            %3i\n", nstudents;
printf "Number of lecturers:           %3i\n", sum{l in lecturer} 1;
printf "Number of projects:            %3i\n", sum{p in project} projmax[p];
printf "Minimum assignments (lectmin): %3i\n", sum{l in lecturer} (lectmin[l]);
printf "Minimum assignments (projmin): %3i\n", sum{p in project} (projmin[p]);
printf "Average mark:                  %2.1f\n", averagemark;
/*
printf "------ Popularity --------\n";
printf "Popularity per lecturer is sum(1/choice)/(total_students*nprojects)*100\n";
printf "Selections are reported as percentages\n";
printf "Per lecturer\n";
printf "\t";
for {i in 1..10} {
    printf "%3i\t", i;
}

printf "Popularity\n";
for {l in lecturer}
{
	printf "%s\t", l;
	for {i in 1..10} {
		printf "%3i\t", 100*(sum{s in student, p in project} 
		       belongs[l,p]*(if studpref[s,p]==i then 1 else 0))/(sum{s in student} 1);
	}
	printf "%6.2f\n", (sum{s in student, p in project} belongs[l,p]*(if studpref[s,p]>0 && studpref[s,p]<=10 then 1/studpref[s,p] else 0))/((sum{p in project} belongs[l,p])*(sum{s in student} 1))*100;
}
printf "Per project\n";
for {p in project}
{
	printf "%s\t", p;
	for {i in 1..10} {
		printf "%3i\t", 100*(sum{s in student} if studpref[s,p]==i then 1 else 0)/(sum{s in student} 1);
	}
	printf "%6.2f\n", (sum{s in student} if studpref[s,p]>0 && studpref[s,p]<=10 then 1/studpref[s,p] else 0)/(sum{s in student} 1)*100;
}
*/
printf "------ Objective --------\n";
printf "Choice  Assigned\n";
for {i in 0..10}
{
	printf "%4i %7i\n", i, sum{s in student, p in project} if assigned[s,p] then if studpref[s,p] == i then 1 else 0 else 0;
}
printf " >10 %7i\n", sum{s in student, p in project} if assigned[s,p] then if studpref[s,p] > 10 then 1 else 0 else 0;
printf "Total unhappiness:   %5i\n", sum{s in student, p in project} assigned[s,p] * studpref[s,p];
printf "Average unhappiness: %5.2f\n", (sum{s in student, p in project} assigned[s,p] * studpref[s,p])/(sum{s in student} 1);
printf "---- Results ----- \n";
printf "Nprojects: Number of projects (including pre-allocations)\n";
printf "Ngood    : Number of good students (with above class average marks)\n";
printf "Lecturer    Nprojects        Ngood\n";
for {l in lecturer}
{
	printf "%s\t%8i\t%8i\n", l, (sum{p in project, s in student} 
            if belongs[l, p] then assigned[s,p] else 0), (sum{s in student, p in project} belongs[l,p]*assigned[s,p]*goodstudent[s]);
}

table assigment_table {s in student, p in project} OUT "CSV" "assignments.csv" :
 s~Student, p~Project, assigned[s,p]~Assigned ;

end;
