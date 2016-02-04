#!/usr/bin/python

# I am running the BBB headless right now so, obviously, I need to run the viewer on the laptop if i want to SEE the graph

import json
# import matplotlib
# Force matplotlib to not use any Xwindows backend.
# see: https://stackoverflow.com/questions/2801882/generating-a-png-with-matplotlib-when-display-is-undefined
# matplotlib.use('Agg')

import matplotlib.pyplot as plt

VERSION = "16.01.31"		# just yy.mm.dd format of last update

# select file(s) to view
filenames = ["./fake_data.txt"]
nicknames = ["Profile_01"]

# select property(s) to view
k = ["temp_smooth", "temp_actual"]
#k = ["temp_smooth"]

all_plots = []
legend_names = []
# import that data

for f in filenames:
	sample_in = json.load(open(f))

	for series in k:
		x = []
		y = []
		for i in sample_in[series]:
			x.append(i[0])
			y.append(i[1])
		all_plots.append(plt.plot(x, y))
		legend_names.append(f+" "+series)

plt.ylabel("Temp ('F)")
plt.xlabel("Time (sec)")
plt.legend(tuple(legend_names), prop={'size':11}, loc='lower right')
#all_plots[1].set_color('red')



# output them to a screen
plt.show()
