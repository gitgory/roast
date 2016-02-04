#!/usr/bin/python

import time
import math
import json

# for testing the script when you don't have the beaglebone
USE_FAKE_DATA = True 		
FAKE_DATA_FILENAME = './fake_data.txt'
fake_message = "* FAKE *"		# message to display to printout when using fake data

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
	fake_message = ""		# overwrite previous message so printout shows nothing when printing actual sampled data

VERSION = "16.02.02"	# just YY.MM.DD format to avoid conflicts with file on laptop vs bbb

FILE_TYPE = "csv" # 3-letter extension (string) of the file to export
SAVE_PATH = "./RoastData/" # location of file saves... could be determined programatically
MAX_ATTEMPTS = 3  # number of tries to get a non-NaN temperature reading
VERBOSE = True    # print out any additional comments such as the NaN commentary
BEAN_TEMP = 68    # initial bean temperature (*F)... this only matters to initialize the running average
SMOOTH_OVER = 15 # number of readings to average... changing this does change your curve!
				  # NOTE: this is over the number of readings, not the number of seconds!  See READ_FREQ below.


# events occur every n seconds
READ_FREQ  = 0.1
SMOOTH_FREQ= 0.1
PRINT_FREQ = 1
WRITE_FREQ = 10		# write is functionally a back up frequency

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
#sample['temp_target'] = []	# the target will either be calculated from the profile on the fly or pre-loaded (depending on how you end up dealing with time)
sample['temp_actual'] = []	# the actual, sampled temperate ('F)
sample['temp_smooth'] = []	# the smoothed reading (hopefully less noisy than the actual reading)
#sample['Q_in'] = []		# approximation of heat rate based on duty cycle (setpoint) of the heating element... currently 100% of 0%
#sample['E_heat'] = []		# a fake parameter approximating energy input into the beans, Q_in*dt, right?
#sample['specific_heat']=[]  # totally aspirational, would require knowledge of Qheat or experimentally sampling the bean at various stages (assuming it changes over time)
# each sample will store the sample time and sample value, e.g. sample['temp_actual'] = [[0.00, 68.1], [0.50, 72.0]] to indicate seconds, and temperatures
# this isn't pretty in the export file but that really doesn't need to be human readable.
# it will make it very easy for graphing scatter plots. More imporantely, list indexes won't have to be coordinated across keys/values within the sample dictionary and we can safely ignore NaN values

def get_bean_info():
	# Enter bean information... This can later be replaced with a bean library
	# It returns a dictionary containing information on the bean of interest

	bean = {}

	# Desired information
	# Generating the bean dicionary keys here isn't ideal...
	# they should be identified elsewhere, perferably with the other VARIABLE definitions at the beginning
	info = [['beanName','Ethiopia Sidamo']]
	info += [['run','6']]

	# builds the bean dictionary by requesting values for each of the desired informations
	# this really should be in a while loop with exceptions so as to ensure appropriate values
	for item in info:
		bean[item[0]]=raw_input("Enter the %s (example: %s)... " % (item[0],item[1]))

	# allows a quick bypass of entering information while testing
	if bean['beanName']=="": bean['beanName']='TEST'
	if USE_FAKE_DATA: bean['beanName'] += '_FAKE_DATA'		    
	if bean['run']=="": bean['run']=99						

	# ensures the run is actually a digit... why is this necessary?!? I think it had something to do with the old write to CSV -> excel or something
	bean['run'] = int(bean['run'])

	return bean

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
	m = int(sec)/60
	sec-=m*60
	s="%02i:%04.1f" % (m,sec)
	return s

def check_validity(t):
	# determine if the temperature is a valid value 
	if math.isnan(t):
		return False
	else: return True

def get_valid_reading(MAX_ATTEMPTS, VERBOSE, USE_FAKE_DATA, elapsed):
	# attempts to get a single temperature reading ('F)
	# sensor temperature is vulnerable to NaN so this attempts up to MAX_ATTEMPTS times before giving up
	# returns a temperature in Fahrenheit and a boolean variable indicating if it is true or not
	
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
	# grabs a data point from a time-temp pair list, based on elapsed time
	global fake_data

	i=0
	# we know the fake_data comes sorted chronologically so we'll just step through it ignoring all the time-temp pair that have already passed 
	while fake_data[i][0] < elapsed:
		i += 1
		# WARNING: this loop breaks with a IndexError if you run out of fake data while testing

	# cut the fake_data list short so we don't have to search it all again.
	fake_data = fake_data[i:]
	return fake_data[0][1]

def new_smoothing(sample_pairs):
	# takes a list of samples in for the format [[time, value], [time, value], ...]
	# performs some smoothing function and returns a single value (not a time, value pair)

	# currently, we just have averaging... obviously this creates a lag
	all_the_values = [x[1] for x in sample_pairs]
	average_value = sum(all_the_values) / float(len(all_the_values))

	# returns a single value
	return truncate(average_value,1)

def get_filename(pth, run, nme):
	filename = "%sRun_%02.i_%s.%s" % (pth, run, nme, FILE_TYPE)
	# is this poor coding to grab the FILE_TYPE variable without passing it in via the function parameters?
	print '\nfilename: "%s"' % filename

	return filename

def get_title(pth, run, nme):
	# prepares a title string
	# ... this should probably be more object oriented...

	# grab the internal temperature reading from the MAX31855 board and convert it to Fahrenheit
	internal = get_ambient_f()

	# return the string
	return "%s\nRun #%02.i,T_amb=%.1f\n" % (nme, run, internal)

def get_preliminary_temps():
	# this just prints the ambient and current bean temperatures

	# get the ambient temperature 
	print "T_ambient = %.1f'F" % get_ambient_f()

	# get a preliminiary bean temperature reading
	temp, temp_is_valid = get_valid_reading(MAX_ATTEMPTS, VERBOSE, USE_FAKE_DATA, 0)

	# remember, the reading could be bad 
	if temp_is_valid: 
		print "T_bean = %.1f'F" % temp
	else: print "WARNING: Thermocouple got an invalid reading!"

	# previously, this all was: 
	#print "\nT_bean = %.1f'F\t Reading is valid: %s" % get_valid_reading(MAX_ATTEMPTS, VERBOSE)

	return

def welcome_message():
	# just prints out pertinent information
	print "="*40
	print "\nversion: %s\n" % VERSION
	if USE_FAKE_DATA: print " * * * * * * USING FAKE DATA * * * * * *\n"

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
	s = '%.12f' % f
	i, p, d = s.partition('.')
	# returns a string
	return float('.'.join([i, (d+'0'*n)[:n]]))


# display any relevant information at the start of the program
welcome_message()

# load up the fake data if we need it
if USE_FAKE_DATA:
	fake_data = load_fake_data()


# initiate bean information... This can later be replaced with a bean library
bean = get_bean_info()

# generate a file name, based on the bean information
# Intentionally not passing it the full bean dictionary so get_filename() doesn't have to have any knowledge of the dictionary
filename = get_filename(SAVE_PATH, bean['run'],bean['beanName'])	# can be re-purposed for the json output

# create file and write bean information and title and column headers to file
f = open(filename,'w')		# soon to be obsolete

# generate a title for the output file, containing bean information
# this will be obsolete when we have a standalone profile/roast viewer
title = get_title(SAVE_PATH, bean['run'], bean['beanName'])
f.write(title)		# soon to be obsolete

# generate column headers for the output file
# as with the bean dictionary keys, data columns to be output should probably be identified early on,
# like with the other VARIABLES at the beginning of the program and not originally mentioned in an output string, here
# this will be obsolete when we have a standalone profile/roast viewer
f.write("elapsed, t_avg(%i), t_bean\n"%(SMOOTH_OVER))		# soon to be obsolete


# final messages
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
			smoothed = new_smoothing(sample['temp_actual'][-SMOOTH_OVER:])

			# add that value to the sample dictionary
			sample['temp_smooth'].append([elapsed_trunc, smoothed])

			# and then schedule the next event
			smooth_next += SMOOTH_FREQ




		# PRINT TO TERMINAL
		# if we have reached the due date for the event
		if elapsed >= print_next:

			# do it
			# prints the desired info from the sample dictionary to the screen, with formatting
			print 'Time: %s\tBean: %.1f\tAverage: %.1f\t%s' % (convert_time(elapsed), sample['temp_actual'][-1][1], sample['temp_smooth'][-1][1], fake_message)

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
			json.dump(sample, open(filename[:-3]+"txt", 'w'))

			# still writing to the csv
			f.write("%s, %.1f, %.1f\n" % (convert_time(elapsed), sample['temp_smooth'][-1][1], sample['temp_actual'][-1][1]))
		
			# and then schedule the next event
			write_next += WRITE_FREQ



except KeyboardInterrupt:
	# this is the soft exit

	# do a final write to the output file so as not to lose the last bit of data that may have accumulated since the last write
	json.dump(sample, open(filename[:-3]+"txt", 'w'))
	print "\ncomplete.\n"
