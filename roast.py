#!/usr/bin/python

import time
import math
import json
from modGregory import tk_ui_for_path

# for testing the script when you don't have the beaglebone
USE_FAKE_DATA = True 		
FAKE_DATA_FILENAME = './fake_data.txt'
FAKE_MESSAGE = "* FAKE *"		# message to display to printout when using fake data

if not USE_FAKE_DATA:
	# none of this will work if you aren't running the script on the beaglebone, so leave it out
	# taken directly from MAX31855 Example
	import Adafruit_GPIO.SPI as SPI
	import Adafruit_MAX31855.MAX31855 as MAX31855

	# BeagleBone Black software SPI configuration.
	# taken directly from MAX31855 Example
	CLK = 'P9_12'
	CS  = 'P9_15'
	DO  = 'P9_23'
	sensor = MAX31855.MAX31855(CLK, CS, DO)
	FAKE_MESSAGE = ""		# overwrite previous message so printout shows nothing when printing actual sampled data

FILE_EXT = ".txt" # 3-letter extension (string) of the save file
MAX_ATTEMPTS = 3  # number of tries to get a non-NaN temperature reading
VERBOSE = True    # print out any additional comments such as the NaN commentary
BEAN_TEMP = 68    # initial bean temperature (*F)... this only matters to initialize the running average
SMOOTH_OVER = 15  # number of readings to average... changing this does change your curve!
				  # NOTE: this is over the number of readings, not the number of seconds!  See READ_FREQ below.


# events occur every n seconds
READ_FREQ  = 0.2
SMOOTH_FREQ= 0.2
PRINT_FREQ = 1
WRITE_FREQ = 20		# write is functionally a back up frequency

# offset them to ensure they happen in the correct order
# and to avoid any potential conflicts
READ_OFFSET  = 0
SMOOTH_OFFSET= 0
PRINT_OFFSET = 0
WRITE_OFFSET = 0

# in this case, it also serves as the start time for the first iteration
read_next  = READ_OFFSET
smooth_next= SMOOTH_OFFSET
print_next = PRINT_OFFSET
write_next = WRITE_OFFSET

# this is the dictionary (soon to be JSON object) that will store all sampled data
# you don't need to print or write it all, but here, it is, nonetheless
sample = {}
sample['fileext'] = FILE_EXT
sample['temp_actual'] = []	# the actual, sampled temperate ('F)
sample['temp_smooth'] = []	# the smoothed reading (hopefully less noisy than the actual reading)
sample['starting_wt'] = 0	# the weight of the green beans at the start of the roast (grams)
#sample['temp_target'] = []	# the target will either be calculated from the profile on the fly or pre-loaded (depending on how you end up dealing with time)
#sample['Q_in'] = []		# approximation of heat rate based on duty cycle (setpoint) of the heating element... currently 100% of 0%
#sample['E_heat'] = []		# a fake parameter approximating energy input into the beans, Q_in*dt, right?
#sample['specific_heat']=[]  # totally aspirational, would require knowledge of Qheat or experimentally sampling the bean at various stages (assuming it changes over time)
# each sample will store the sample time and sample value, e.g. sample['temp_actual'] = [[0.00, 68.1], [0.50, 72.0]] to indicate seconds, and temperatures
# this isn't pretty in the export file but that really doesn't need to be human readable.
# it will make it very easy for graphing scatter plots. More imporantely, list indexes won't have to be coordinated across keys/values within the sample dictionary and we can safely ignore NaN values

def get_bean_info():
	# It returns a dictionary containing information on the bean of interest
	# In the future, this function will just import from a bean library.
	# Currently it prompts the user for bean information.

	# Generating the bean dicionary keys HERE isn't ideal...
	# they should be identified elsewhere, preferably with the other VARIABLE definitions at the beginning
	bean = {}
	bean['beanName']=raw_input("Enter the name of the bean (example: Ethiopia Sidamo)  ")

	# allows a quick bypass of entering information while testing
	if bean['beanName'] == "":
		bean['beanName'] = 'TEST'
	if USE_FAKE_DATA:
		bean['beanName'] += '_FAKE_DATA'		    

	return bean

def get_sample_info():
	# This is information specific to the roast
	# It returns a dictionary that will be used to record this roast in progress


	# Desired information
	# Generating the sample dicionary keys HERE isn't ideal...
	# they should be identified elsewhere, perferably with the other VARIABLE definitions at the beginning
	sample = {}
	sample['t_ambient'] = get_ambient_f()


	sample['starting_wt'] = raw_input("Enter the starting weight in grams (example: 80)... ")
	sample['run'] = raw_input("Enter the Run # (example: 5)... ")

	# allows a quick bypass of entering information while testing		    
	if sample['run']=="":
		sample['run']=99
	if sample['starting_wt']=="":
		sample['starting_wt']=99

	# converts the run entry from a string to a digit. It's just more predictable that way.  Later processes anticipate this to be a digit.
	sample['run'] = int(sample['run'])
	sample['starting_wt'] = int(sample['starting_wt'])

	return sample

def c_to_f(c):
	# takes a celsius (float) and returns a fahrenheit (float)
	return c * 9.0 / 5.0 + 32.0

def get_ambient_f():
	# returns the ambient temperature reading at the MAX31855 chip
	if USE_FAKE_DATA:
		return 68.1
	else: 
		return c_to_f(sensor.readInternalC())

def convert_time(sec):
	# converts seconds (float) to a human readable mm:ss string
	# this is only used in the terminal output, not for exporting
	m = int(sec)/60
	sec -= m*60
	s = "%02i:%04.1f" % (m, sec)
	return s

def check_validity(t):
	# determine if the temperature is a valid value 
	if math.isnan(t):
		return False
	else:
		return True

def get_valid_reading(MAX_ATTEMPTS, VERBOSE, USE_FAKE_DATA, elapsed):
	# attempts to get a single temperature reading ('F)
	# sensor temperature is vulnerable to NaN so this attempts up to MAX_ATTEMPTS times before giving up
	# returns a temperature in Fahrenheit (float) and a boolean variable indicating if it is true or not
	# is it good practice to be passing in these constants or no?
	
	if USE_FAKE_DATA:
		# get fake data
		temp = get_fake_data_point(elapsed)
		return temp, True 		# WARNING: this assumes you have valid data... you aren't testing what happens when you get a NaN...
								# It might be of value to allow the fake data to contain NaN and then pass it through the rest of the get_valid_reading function
								# so you can imitate more accurately actual readings from a sensor... you can test how your system handles NaN without BBB

	else:
		# get real data
		# reset counters and flags
		temp_is_valid = False			
		read_attempt = 0	

		while temp_is_valid is not True and (read_attempt < MAX_ATTEMPTS):

			# increase the counter
			read_attempt += 1

			# read the sensor
			temp = c_to_f(sensor.readTempC())

			# check that it is valid... the whole check_validity code is so short it could be included here
			# but it might be useful elsewhere in the program too, so i'll leave it as a function and call it.
			temp_is_valid = check_validity(temp)

			# if you failed to get a good reading and you care to hear about it...
			if temp_is_valid is not True and VERBOSE==True:
				print "failed attempt", read_attempt, "... Received:", temp

		# if you did have errors but want to know that you got a good value on subsequent checks
		# this message is not necessary for operation, just intermediate-term error-checking
		if temp_is_valid and read_attempt > 1 and VERBOSE==True:	
			print "passed on attempt", read_attempt,"with value:", temp

		# in theory, the thermocouple is only accurate to 6 degrees, so there is no point in keeping 10 decimal places
		if temp_is_valid:
			temp = truncate(temp, 1)
		else:
			pass

		# return the reading and whether it is valid or not (True/False)
		return temp, temp_is_valid

def get_fake_data_point(elapsed):
	# returns a data point from a time-temp pair list, based on elapsed time
	# maybe you should just pass it in instead of using global?
	global fake_data

	i=0
	# we know the fake_data comes sorted chronologically so we'll just step through it ignoring all the time-temp pair that have already passed 
	while fake_data[i][0] < elapsed:
		i += 1
		# WARNING: this loop breaks with a IndexError if you run out of fake data while testing

	# cut the fake_data list short so we don't have to search it all again.
	fake_data = fake_data[i:]
	return fake_data[0][1]

def smooth_data(sample_pairs):
	# takes a list of samples in for the format [[time, value], [time, value], ...]
	# performs some smoothing function and returns a single value (not a time, value pair)

	# currently, we just have averaging... obviously this creates a lag
	all_the_values = [x[1] for x in sample_pairs]
	average_value = sum(all_the_values) / float(len(all_the_values))

	# returns a single value
	return truncate(average_value,1)

def generate_filename(run, nme):
	# returns a string to be used as a file name; no path, no extension
	filename = "Run_%02.i_%s" % (run, nme)
	# WARNING: this is a little deceptive because we are printing out the file with ext but only returning the filename (no ext)
	print '\nsaving file as: "%s.%s"' % (filename, FILE_EXT)

	return filename

def get_preliminary_temps():
	# this just prints the ambient and current bean temperatures to show the user that everything is working

	# get the ambient temperature 
	print "T_ambient = %.1f'F" % get_ambient_f()

	# get a preliminiary bean temperature reading
	temp, temp_is_valid = get_valid_reading(MAX_ATTEMPTS, VERBOSE, USE_FAKE_DATA, 0)

	# remember, the reading could be bad 
	if temp_is_valid: 
		print "T_bean = %.1f'F" % temp
	else:
		print "WARNING: Thermocouple got an invalid reading!"

	return

def welcome_message():
	# just prints out any pertinent information
	print "\n"
	print "="*42
	
	# print "\nversion: %s\n" % VERSION
	
	if USE_FAKE_DATA: print " * * * * * * USING FAKE DATA * * * * * *\n"

	return

def start_sequence():
	# all the messages that happen before we get going... also allows for the user to begin on command
	# display the current temperatures before we get going
	get_preliminary_temps()

	# wait for the user to say "Go"
	wait=raw_input("\nHit <ENTER> to being...")

	# final messages as we start
	print '\nPress Ctrl-C to quit.\n'

	return

def load_fake_data():
	# fake data is for testing without the beaglebone
	# returns a LIST
	print "getting fake data from %s" % FAKE_DATA_FILENAME

	# fake data is stored in the same file format as regular roasts. Currently it only includes entries for temp_actual readings (time and temp pairs)
	fake = json.load(open(FAKE_DATA_FILENAME))

	# data is stored as unicode strings
	use_this_data = []
	for k in fake.keys():
		use_this_data += [[float(x),float(y)] for [x,y] in fake[k]]

	return use_this_data

def truncate(f, n):
	# takes a float, returns a float, truncated to n places
	# just taken from https://stackoverflow.com/questions/783897/truncating-floats-in-python
	# probably should be moved over to modGregory.py
	s = '%.12f' % f
	i, p, d = s.partition('.')
	# returns a string
	return float('.'.join([i, (d+'0'*n)[:n]]))




# display any relevant information at the start of the program
welcome_message()

# have the user enter the save location for this roast
sample['filepath'] = tk_ui_for_path()

# load up the fake data if we need it
if USE_FAKE_DATA: fake_data = load_fake_data()

# pull all the information about this particular bean and roast into the sample roast file
sample.update(get_bean_info())
sample.update(get_sample_info())


# generate a file name, based on the bean information
# Intentionally not passing it the full bean dictionary so generate_filename() doesn't have to have any knowledge of the dictionary
filename = generate_filename(sample['run'],sample['beanName'])	# can be re-purposed for the json output

# store the filename in the bean dictionary... seems risky to let the key and variable name be the same...
sample['filename'] = filename

# generate the full file and path name, for use with the json dumps, not necessary to store in sample dictionary since all the individual parts are already there and can be inferred
full_filename = sample['filepath']+sample['filename']+sample['fileext']

# any final messages and go!
start_sequence()






# pre-fill the sampled temperature with enough values so we can start smoothing right away (at time 0:00)
for i in range(SMOOTH_OVER): sample['temp_actual'].append([0.0, BEAN_TEMP])		# assumes beans start at room temperature

# grab the current time for later elapsed time calculations
t_initial = time.time()

# and we're up and running...
try:
	#the try statement allows for a soft exit via Ctrl+C
	while True:
		# determine how much time has elapsed (seconds)
		elapsed = time.time() - t_initial

		# we don't need all that accuracy when storing data so we'll truncate it
		elapsed_trunc = truncate(elapsed,3)


		# four events happen in this loop: READ, SMOOTH, PRINT, and WRITE
		# the basic flow goes like this:
		# if we have reached or passed the due date (total elapsed time in seconds) for the event:
			# do it
			# then determine the next time this event will be run



		# READ SENSORS
		# if we have reached the due date for the event
		if elapsed >= read_next:
			
			# do it
			# grab the temperature from the sensor
			temp, temp_is_valid = get_valid_reading(MAX_ATTEMPTS, VERBOSE, USE_FAKE_DATA, elapsed)
			
			# write it to the sample dictionary
			if temp_is_valid:
				sample['temp_actual'].append([elapsed_trunc, temp])
			else:
				# we're fine just ignoring bad readings, the time-series approach for storing samples facilitates this
				pass

			# and then schedule the next event
			read_next += READ_FREQ




		# SMOOTHING DATA
		# the sensor reading is really noisy and jumps around a lot. It's not reliable to use for controlling yet.  It must be smoothed my some means.
		# if we have reached the due date for the event
		if elapsed >= smooth_next:
			
			# do it
			# send the last x time-and-temperature pairs to the smoothing function
			smoothed = smooth_data(sample['temp_actual'][-SMOOTH_OVER:])

			# add that value to the sample dictionary
			sample['temp_smooth'].append([elapsed_trunc, smoothed])

			# and then schedule the next event
			smooth_next += SMOOTH_FREQ




		# PRINT TO TERMINAL
		# if we have reached the due date for the event
		if elapsed >= print_next:

			# do it
			# prints the desired info from the sample dictionary to the screen, with formatting
			print 'Time: %s\tBean: %.1f\tAverage: %.1f\t%s' % (convert_time(elapsed), sample['temp_actual'][-1][1], sample['temp_smooth'][-1][1], FAKE_MESSAGE)

			# and then schedule the next event
			print_next += PRINT_FREQ





		# WRITE TO FILE
		# this is the export file.  If you knew that the program wouldn't crash, you could just do this once, at the end.  
		# Until, then, it "backs up" the sample dictionary on the WRITE_FREQ interval
		# if we have reached the due date for the event
		if elapsed >= write_next:
			
			# do it
			# writes the data to a file
			# this really should use the WITH statement
			# from: https://stackoverflow.com/questions/11026959/python-writing-dict-to-txt-file-and-reading-dict-from-txt-file
			json.dump(sample, open(full_filename, 'w'))

			# and then schedule the next event
			write_next += WRITE_FREQ



except KeyboardInterrupt:
	# this is the soft exit

	# do a final write to the output file so as not to lose the last bit of data that may have accumulated since the last write
	json.dump(sample, open(full_filename, 'w'))
	print "\ncomplete.\n"
