#!/usr/bin/python

import json

# new
profile = {}

# set the basic profile.  Likely this won't have to be more than a dozen points.
# CURRENTLY THIS IS THE SETPOINTS FOR ETHIOPIA SIDAMO ROAST #18 FOR RIKKI
# foreseeable problem: can't compare this with actual roasts because it is called 'target_temp', not 'temp_actual' or whatever...
profile['target_temp'] = [[0.0, 70.0], [30.0, 190.0], [60.0, 257.0],[90.0, 299.0], [120.0, 328.0], [150.0, 349.0], [180.0, 369.0], [210.0, 385.0], [240.0, 397.0], [270.0, 413.0], [300.0, 426.0], [330.0, 436.0], [360.0, 445.0], [390.0, 456.0], [420, 465.0], [430, 467.0]]

# set bounds of acceptable temperatures
# this is a really basic way to do this. In the future, you may want to have a large window at first and narrow it down as you go along
# or perhaps, you want to re-set the offset as you go depending on the progress of the roast... include some executable code in the profile?

lower_offset = 6.0
lower_bound = [[x, y-lower_offset] for [x,y] in profile['target_temp']]
profile['lower_bound'] = lower_bound



def upper_offset(x):
	return min(4+(2000./(x+1)),100)

upper_bound = [[x, y+upper_offset(x)] for [x,y] in profile['target_temp']]
profile['upper_bound'] = upper_bound



# modify could just start a new profile and suggest the previous numbers?
# do you want to forever have reference to the values you set?  For example, what if you made a profile, roasted it, then modified the profile. Do you want to have the ability to look up the original profile? Should it be written in with the roast history or just referenced?
# keep all profiles then?  Keep version along with roast? 

profile_name = raw_input('Enter the profile name:  ')
full_filename = './profiles/' + profile_name
json.dump(profile, open(full_filename, 'w'))

