#!/usr/bin/python

# I am running the BBB headless right now so, obviously, I need to run the viewer on the laptop if i want to SEE the graph

import json
# import matplotlib
# Force matplotlib to not use any Xwindows backend.
# see: https://stackoverflow.com/questions/2801882/generating-a-png-with-matplotlib-when-display-is-undefined
# matplotlib.use('Agg')

# a change

import matplotlib.pyplot as plt
from Tkinter import *
import tkFileDialog

VERSION = "16.02.04"		# just yy.mm.dd format of last update


def user_select_files(message):
	# grab the path for each file. This dialog should open in the "root" window of Tk
	# returns a list of file path and name strings
	# information on grabbing multiple files from the UI from: 
	# 	https://stackoverflow.com/questions/16790328/open-multiple-filenames-in-tkinter-and-add-the-filesnames-to-a-list
	# 	http://www.pythonbackend.com/topic/1354022597
	# define the top-level window for this Tkinter app
	root = Tk()		
	get_filenames = tkFileDialog.askopenfilenames(parent=root,title=message)		# I think this is why I currently get the lone window left open...
	return get_filenames

def read_in_data(filenames):
	# given a list of filenames, this returns a list. Each entry is a dictionary representing the data from the files
	all_together =[]
	for f in filenames:
		temp_dict={}
		#locate the actual filename w/o the path --> that becomes the nickname
		i = f.rfind('/')
		nickname = f[i+1:]
		# ad some basic data 
		temp_dict = {'path' : f, 'nickname' : nickname}
		# then, read in the contents of the file
		sample_in = json.load(open(f))
		# add those contents to our basic data
		temp_dict.update(sample_in)
		# collect all these individual samples in one big roast list
		all_together.append(temp_dict)

	print "\n# of roasts imported = %i\n"% len(all_together)

	return all_together

def var_states():
	# this function does not work right now. it does not return 1 (True) values for checked boxes
	# i really don't understand what's the issue.
	global variable_locker
	global available_data

	for i in range(len(available_data)):
		print available_data[i], variable_locker[i].get()
	# exit the Tk window
	master.quit()

def get_desired_data(all_possible_data):
	# this function does not work right now. it does not return 1 (True) values for checked boxes
	# i really don't understand what's the issue.
	# IDEALLY, it takes a list of strings which are the names of available series in the roast files that can be graphed
	master = Tk()
	global variable_locker

	# Display some instructions in the UI window
	Label(master, text="Select the data series to display").grid(row=0, sticky=W)


	# count rows for placing items in the Tk window
	r = 0

	# we will create a checkbox to allow the user to select each piece of data they are interested in
	for option in all_possible_data:
		# jump down to the next row
		r += 1
		# add a new IntVar to the locker
		variable_locker.append(IntVar())
		# display a checkbox for the option
		Checkbutton(master, text=option, variable=variable_locker[-1]).grid(row=r, sticky=W)

	
	# add some Buttons
	# This one just exits the window
	Button(master, text='Cancel', command=master.quit).grid(row=r+1, sticky=E, pady=4)
	# this one passes data via the var_states()
	Button(master, text='Show Graphs', command=var_states).grid(row=r+1, sticky=W, pady=4)
	#Button(master, text='Show Graphs', command=master.quit).grid(row=r+1, sticky=W, pady=4)
	# initialize the Tk window?
	
	
	mainloop()

	temp_data =[]
	for i in range(len(variable_locker)):
		print variable_locker[i], " = ", variable_locker[i].get()
		if variable_locker[i].get():
			temp_data.append(all_possible_data[i])
	return temp_data

	# and we're out of the Tk window now

def get_desired_data_TEMP(all_possible_data): 
	# it takes a list of strings which are the names of available series in the roast files that can be graphed
	# user selects which series they desire and it returns a list of those series names (strings)
	# this is an intermediate step to determine the data series's the user wants to plot.  It is text-entry based until we can get the UI checkboxes working.

	for i in range(len(all_possible_data)):
		print "%i)   %s" % (i, all_possible_data[i])


	desired_series = []


	while True:
		# get the user's preferences
		
		user_selection = raw_input("Select desired data series (leave blank to continue):  ")
		if user_selection == "": break
		try:
			user_selection = int(user_selection)
			desired_series.append(all_possible_data[user_selection])
		except (SyntaxError, ValueError):
			# didn't enter an integer
			print "Invalid entry -- <leave blank to continue> "
			continue
		except IndexError:
			# its outside of the bounds of the options
			print "Value out of range"
			continue

	# strip out any duplicates
	desired_series = list(set(desired_series))

	return desired_series

def graph_roasts(all_roasts, desired_data):
		
	all_plots = []				# this supposed to be the equivalent of a handle for a plot, but for each plot
	legend_names = []			# collects all the nicknames for display to the legend
	# import that data

	for roast in all_roasts:
		for series in desired_data:
			x = []
			y = []
			for i in roast[series]:
				x.append(i[0])
				y.append(i[1])
			all_plots.append(plt.plot(x, y))
			legend_names.append(roast['nickname']+" "+series)

	plt.ylabel("Temp ('F)")
	plt.xlabel("Time (sec)")
	plt.legend(tuple(legend_names), prop={'size':11}, loc='lower right')

	# I'd like to be able to manually change the colors... but this isn't the way
	#all_plots[1].set_color('red')



	# output them to a screen
	plt.show()

def export_to_csv(all_roasts, desired_data):
	print "yeah, there's nothing here yet..."





# get a list of all the files we're reading from (full path)
filez = user_select_files("Choose a file")

# read in all the data from those files
all_roasts = read_in_data(filez)

available_data = ['temp_actual', 'temp_smooth']			# more could go here but i need error handling for the files that don't have keys with these legend_names


# currently not working, bypassed below
# When it works it should allow creation of the desired_data list via checkboxes in Tkinter

# variable_locker = []				
# desired_data = get_desired_data(available_data)		
# for i in range(len(variable_locker)):
# 	print variable_locker[i], " = ", variable_locker[i].get()



# get_desired_data is not working right now so this is the temporary solution to getting the data series the user wants
desired_data = get_desired_data_TEMP(available_data)

print "desired_data = ", desired_data

user_choice = raw_input('Export to CSV?  [N/y]')
if user_choice in ['Y','y']:
	export_to_csv(all_roasts, desired_data)

graph_roasts(all_roasts, desired_data)


