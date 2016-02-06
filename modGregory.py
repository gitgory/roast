#!/usr/bin/python3


from random import randint
from Tkinter import *
from tkFileDialog import askdirectory

def generate_dict_with_2d(k=4,l=10):
	# Generates and returns a dictionary with k keys.
	# The value for each key is a two dimensional lists.
	# Each list is l long.
	d={}
	for key in range(k):
		temp_list =[]
		for lst in range(l):
			temp_list.append([lst, randint(1,20)])
		d[chr(key+ord('A'))] = temp_list
	return d

def tk_ui_for_path():
	# Uses a Tkinter UI to select a path. 
	# Returns a path name as a string.
	root = Tk()
	pth = askdirectory(parent=root, title="Select the location")		#tkFileDialog is a part of Tkinter
	root.destroy()
	return pth

def get_str_from_user(message="Enter the filename with suffix:  ", valid_suffix=['csv','txt']):
	# Asks the user for a filename, including suffix
	# Retuns the string of the filename and suffix (no path)
	while True:
		f = raw_input(message)
		if isinstance(f, str) and f[-4] == "." and f[-3:] in valid_suffix:
			return f
		else:
			print("Try again. Remember to include the suffix.")
			continue

def dict2csv(d, title="some header", only_export=[''], subscript1="_x", subscript2="_y"):

	# writes a dictionary of 2D lists to csv
	# assumes you have a filename already, likely based on the import filename
	# returns nothing

	# generate some filename for now
	pth = tk_ui_for_path()
	filename = get_str_from_user(valid_suffix=['csv'])

	full_filename = pth+'/'+filename

	# generate some dictionary for now
	my_dict = d

	# write header information to file
	with open(full_filename, 'w') as f:
		f.write(title+"\n")
		k = only_export
		[f.write("%s%s, %s%s, " % (key, subscript1, key, subscript2)) for key in k]
		f.write('\n')

		# write data to file
		i = 0
		while True:
			s = ""
			it_worked = False			# reset the flag, which checks to make sure at least one dictionary entry is still adding values
										# this is my solution to the possibility that some entries might have different lengths of values
			for key in k:
				try:
					x = str(my_dict[key][i][0])
					y = str(my_dict[key][i][1])
					it_worked = True
				except:
					x = ""
					y = ""
				s += x+", "+y+", "
			f.write(s+"\n")
			i += 1
			if it_worked == False:
				break