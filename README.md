# webrealf
a real time crowd rating website that uses an interactive map 

3 main features

  checking in to places
people can check in to places they are at the system takes this check in and uses that data to estimate crowd level at the exact place the estimation uses a simple bayesian smoothing method every spot has a distintc base crowd score at spesific hours of the day the system shows this base score if there are no checkins as the number of checkins rise the system allows checkins to change the crowd score more therefore creating a solid crowd estimation algorithm 

  the food poll 
the website allows users to vote for the food at the dining hall that day both for lunch and dinner a simple poll with options good and bad if the poll results says food is bad that day it gives a small boost to some of the spots crowd base scores therefore taking the students that eats at other places when food at the dining hall isnt satisfying into account

  rating crowd score 1-10
this feature works completely independent than two other features listed above the feature allows users to rate how crowded a place is on a scale 1 to 10 this is an extra layer of data for the users to find out crowd more effectively alongside the checking in and the food poll 
