#!/usr/bin/python

import time
import math
import json
# from modGregory import tk_ui_for_path
from modGregory import *

# Use fake data for testing the script when you don't have the beaglebone.
USING_FAKE_DATA = True
FAKE_DATA_FILENAME = './fake_data.txt'
FAKE_MESSAGE = "* FAKE *"    # Display this message when using fake data.
fake_data = []               # Not a constant but must be initiated early because it is actually
                             # assigned a meaningful value inside of a function and a global var

if not USING_FAKE_DATA:

    # None of the following will work if you aren't running the script on the beaglebone,
    # so leave it out. Taken directly from MAX31855 Example on Adafruit.com
    import Adafruit_GPIO.SPI as SPI
    import Adafruit_MAX31855.MAX31855 as MAX31855

    # BeagleBone Black software SPI configuration.
    # Taken directly from MAX31855 Example on Adafruit.com
    CLK = 'P9_12'
    CS  = 'P9_15'
    DO  = 'P9_23'
    sensor = MAX31855.MAX31855(CLK, CS, DO)
    
    # Overwrite the previous message so printout shows nothin when printing
    # actual sampled data. Avoids conoditional statement in loop later.
    FAKE_MESSAGE = ""

FILE_EXT = ".txt" # Extension (string) of the save file. Soon to be ".json"
MAX_ATTEMPTS = 3  # Number of tries to get a non-NaN temperature reading
VERBOSE = True    # Allow additional comments such as the NaN commentary?
BEAN_TEMP = 68    # Initial bean temperature (*F). Only used to initialize a running average.
SMOOTH_OVER = 15  # The number of readings to average over. Changing this DOES change your curve!
                  # This is number of readings, not the number of seconds!  See READ_FREQ below.

# events occur every n seconds
READ_FREQ  = 0.2
SMOOTH_FREQ= 0.2
PRINT_FREQ = 1
WRITE_FREQ = 30   # write is functionally a back up frequency

# offset them to ensure they happen in the correct order and to avoid any potential conflicts
READ_OFFSET  = 0
SMOOTH_OFFSET= 0
PRINT_OFFSET = 0
WRITE_OFFSET = 4    # while testing, you'll want to see the data before the first WRITE_FREQ trigger

# DEFINITIONS FOR CLARITY:
# 'bean'   = the characteristics of the green beans, ex: Sidamo
# 'sample' = the data read by a sensor in [[time, value],...] pairs, ex: [[10.0, 99.5],...] 
# 'batch'  = specific to the particular run, ex: batch #21, 80g
#             NOTE: sampled data is stored in the batch dictionary
# 'roast'  = the big picture, the process, or possibly interchangeable with 'batch'
# 'profile'= the desired temperature over the course of the roast... a profile is no different in format from a batch
#             in fact, a batch could be used as a profile



def load_fake_data():
    """
    Pre-loads the fake data set into a 2D list.
    Fake data is is for testing the script without a beaglebone.

    Parameters:
        FAKE_DATA_FILENAME
        fake_data (global): previously an empty [], 

    Returns: 
        None.
        Alters the (global) fake_data to be a 2D list.

    Raises:
    """

    global fake_data

    print "getting fake data from %s" % FAKE_DATA_FILENAME

    # fake data is stored in the same file format as regular roasts. Currently it only includes entries for temp_actual readings (time and temp pairs)
    fake = json.load(open(FAKE_DATA_FILENAME))

    # data is stored as unicode strings
    use_this_data = []
    for k in fake.keys():
        use_this_data += [[float(x),float(y)] for [x,y] in fake[k]]

    fake_data = use_this_data
    return

def welcome_message():
    """Displays to terminal any pertinent information at the start of the script.
    """

    print "\n"
    print "="*42
    
    if USING_FAKE_DATA: print " * * * * * * USING FAKE DATA * * * * * *\n"

    return

def generate_batch_dict():
    """
    Initiates all the basic elements of the dictionary to record the roast event

    Parameters:
        BEAN_TEMP
        SMOOTH_OVER

    Returns: 
        temp_dict: (dict) containing all the basic bits of information required for the roast, 
            or at least all the keys initiated.

    Raises:
        None.
    """

    temp_dict = {}

    # Temperature sensors reading will store the sample time and sample value:
    # e.g. batch['temp_actual'] = [[0.00, 68.1], ...] to indicate seconds, and temperatures.
    # This isn't pretty in the export file but that really doesn't need to be human readable.
    # It will make it very easy for graphing scatter plots.
    # More imporantely, list indexes won't have to be coordinated across keys/values
    # within the batch dictionary and we can safely ignore NaN values
    temp_dict['temp_actual'] = []    # the actual, sampled temperate ('F)
    temp_dict['temp_smooth'] = []    # the smoothed reading (hopefully less noisy than the actual reading)

    # the following are aspirational (future implementations) sensors and calculations:
    #temp_dict['temp_target'] = []   # the target will either be calculated from the profile on the fly or pre-loaded (depending on how you end up dealing with time)
    #temp_dict['Q_in'] = []          # Approx. of heat rate based on duty cycle of the heating element.Currently its either 100% or 0%
    #temp_dict['E_heat'] = []        # a fake parameter approximating energy input into the beans, Q_in*dt, right?
    #temp_dict['specific_heat']=[]   # would require knowledge of Qheat or experimentally sampling the bean at various stages (assuming it changes over time)

    # pre-fill the temperature readings with enough values so we can start smoothing
    # right away (at time 0:00)... assumes beans start at room temperature
    for i in range(SMOOTH_OVER):
        temp_dict['temp_actual'].append([0.0, BEAN_TEMP])

    temp_dict['filepath'] = tk_ui_for_path()  # have the user enter the save location for this batch

    # pull all the information about this particular bean and roast so it can be added into the batch roast file
    temp_dict.update(get_bean_info())
    temp_dict.update(get_batch_info())
    temp_dict.update(generate_filename(temp_dict))

    temp_dict['comments'] = raw_input("Enter optional roast comments or <Enter> to continue:  ")+" "

    return temp_dict

def load_roast_profile():
    """
    Allows user to select a pre-existing roast profile to guide the roast.

    Parameters:

    Returns:

    Raises:
    """

    # profile data is stored in the same file format as regular roasts - it may even be a regular roast
    print "Select desired roast profile."
    profile_file_path = user_select_files("Select desired roast profile.")
    prof = json.load(open(profile_file_path))

    # data is stored as unicode strings
    use_this_data = []
    for k in prof.keys():
        use_this_data += [[float(x),float(y)] for [x,y] in prof[k]]
    print use_this_data
    return use_this_data



def get_bean_info():
    """
    Grabs information about the bean, including name, but potentially order date, region, etc.

    Parameters:
        USING_FAKE_DATA

    Returns: 
        A dictionary containing information on the bean of interest.
        In the future, this function will just import from a bean library.
        Currently it prompts the user for bean information.

    Raises:
        None
    """

    # Generating the bean dicionary keys HERE isn't ideal. They should be identified elsewhere,
    # preferably with the other VARIABLE definitions at the beginning
    bean = {}
    bean['beanName']=raw_input("Enter the name of the bean (example: Ethiopia Sidamo)  ")

    # allows a quick bypass of entering information while testing
    if bean['beanName'] == "":
        bean['beanName'] = 'TEST'
    if USING_FAKE_DATA:
        bean['beanName'] += '_FAKE_DATA'            

    return bean

def get_batch_info():
    """
    Grab information on this particular roasting event.

    Parameters:
        None.

    Returns: 
        temp_dict: a dictionary with info specific to the batch (run)

    Raises:
        None.
    """
    # This is information specific to this particular batch
    # It returns a dictionary that will be used to record this roast in progress


    # Desired information
    # Generating the batch dicionary keys HERE isn't ideal...
    # they should be identified elsewhere, perferably with the other VARIABLE definitions at the beginning
    temp_dict = {}
    temp_dict['t_ambient'] = get_ambient_f()

    temp_dict['starting_wt'] = raw_input("Enter the starting weight in grams (example: 80)... ")
    temp_dict['run'] = raw_input("Enter the Run # (example: 5)... ")

    # allows a quick bypass of entering information while testing            
    if temp_dict['run']=="":
        temp_dict['run']=99
    if temp_dict['starting_wt']=="":
        temp_dict['starting_wt']=99

    # converts the run entry from a string to a digit. It's just more predictable that way.  Later processes anticipate this to be a digit.
    temp_dict['run'] = int(temp_dict['run'])
    temp_dict['starting_wt'] = int(temp_dict['starting_wt'])

    return temp_dict

def generate_filename(original_dict):
    """
    Creates a dictionary containing a file name (str) based on bean
    information and a full file name (including path and extension)

    Parameters:
        original_dict: (dict), assumed to contain bean information already
        FILE_EXT

    Returns: 
        temp_dict: a dictionary, to be used with .update()

    Raises:
        None.
    """
    temp_dict = {}
    temp_dict['fileext'] = FILE_EXT
    filename = "Batch_%02.i_%s" % (original_dict['run'],original_dict['beanName'])

    temp_dict['filename'] = filename
    temp_dict['full_filename'] = original_dict['filepath']+temp_dict['filename']+temp_dict['fileext']

    # WARNING: this is a little deceptive because we are printing out the file
    # with ext but only returning the filename (no ext)
    print '\nsaving file as: "%s%s"' % (filename, FILE_EXT)

    return temp_dict

def display_preliminary_temps():
    """
    Prints ambient and current bean temperatures (Fahrenheit) to show that everything is working.

    Parameters:
        None.

    Returns:
        None.

    Raises:
        None. Though, perhaps the warning message when temp_is_valid == False could be an exception.
    """

    # get the ambient temperature 
    print "T_ambient = %.1f'F" % get_ambient_f()

    # get a preliminiary bean temperature reading
    temp, temp_is_valid = get_valid_reading(0)

    # remember, the reading could be bad 
    if temp_is_valid: 
        print "T_bean = %.1f'F" % temp
    else:
        print "WARNING: Thermocouple got an invalid reading!"

def get_ambient_f():
    """
    Grabs the ambient temperature reading (Fahrenheit) at the MAX31855 chip

    Parameters:
        USING_FAKE_DATA

    Returns:
        (float) representing a temperature (Fahrenheit)
        
    Raises:
        None.
    """

    if USING_FAKE_DATA:
        return 68.1
    else:
        return c_to_f(sensor.readInternalC())

def check_validity(t):
    """ Determine if the temperature is a valid value
    """

    if math.isnan(t):
        return False
    else:
        return True

def get_valid_reading(elapsed):
    """
    Attempts to get a single temperature reading ('F).
    If we are using fake data, it re-directs to the get_fake_data_point function.

    Sensor temperature is vulnerable to NaN so this attempts
    up to MAX_ATTEMPTS times before giving up, indicated by returning temp_is_valid == False.

    Parameters:
        elapsed: (float) time in seconds since start
        USING_FAKE_DATA
        MAX_ATTEMPTS
        VERBOSE

    Returns: 
        (temp, temp_is_valid)
            temp: (float) a temperature in Fahrenheit
            temp_is_valid: (bool) indicating if the reading can be trusted.

    Raises:
        None.
    """

    
    if USING_FAKE_DATA:
        # get fake data
        temp = get_fake_data_point(elapsed)
        return temp, True         # WARNING: this assumes you have valid data... you aren't testing what happens when you get a NaN...
                                  # It might be of value to allow the fake data to contain NaN and then pass it through the rest of the get_valid_reading function
                                  # so you can imitate more accurately actual readings from a sensor... you can test how your system handles NaN without BBB

    else:
        # get real data
        # reset counters and flags
        temp_is_valid = False            
        read_attempt = 0    

        while temp_is_valid is not True and (read_attempt < MAX_ATTEMPTS):

            read_attempt += 1

            temp = c_to_f(sensor.readTempC())    # read the sensor

            # check that it is valid. the whole check_validity code is so short
            # that it could be included here but it might be useful elsewhere
            # in the program too, so i'll leave it as a function and call it.
            temp_is_valid = check_validity(temp)

            # if you failed to get a good reading and you care to hear about it...
            if temp_is_valid is not True and VERBOSE==True:
                print "failed attempt", read_attempt, "... Received:", temp

        # if you did have errors but want to know that you got a good value on subsequent checks
        # this message is not necessary for operation, just intermediate-term error-checking
        if temp_is_valid and read_attempt > 1 and VERBOSE==True:    
            print "passed on attempt", read_attempt,"with value:", temp

        # in theory, the thermocouple is only accurate to 6 degrees
        # so there is no point in keeping 10 decimal places
        if temp_is_valid:
            temp = truncate(temp, 1)

        # return the reading and whether it is valid or not (True/False)
        return temp, temp_is_valid

def get_fake_data_point(elapsed):
    """
    Grabs a data point from a time-temp pair list, based on elapsed time.

    Parameters:
        elapsed: (float) time in seconds since start        
        FAKE_DATA

    Returns: 
        (float) representing a temperature in Fahrenheit

    Raises:
        IndexError: after running out of fake data
    """

    global fake_data

    i=0
    # we know the fake data comes sorted chronologically so we'll just step through it, 
    # ignoring all the time-temp pair that have already passed 
    try:
        while fake_data[i][0] < elapsed:
            i += 1
    except IndexError:
        print "Came to the end of the fake data."

    # cut the fake list short so we don't have to search it all again.
    # this won't fly anymore if you remove the global functionality.
    fake_data = fake_data[i:]
    return fake_data[0][1]

def smooth_data(sampled_pairs):
    """
    Performs some smoothing function and returns a single value (not a time, value pair)

    Currently, it is just an average.  Obviously this creates a lag.

    Parameters:
        sampled_pairs: a 2D list in for the format [[time, value], [time, value], ...]

    Returns: 
        

    Raises:
    """
    
    all_the_values = [x[1] for x in sampled_pairs]
    average_value = sum(all_the_values) / float(len(all_the_values))

    # returns a single value
    return truncate(average_value,1)

def calc_loss_percent(wt_start, wt_finish):
    """
    Calculates the percentage of change.

    Parameters:
        wt_start: (float) the initial weight
        wt_finish: (float) the fial weight
        
    Returns: 
        percent_loss: (float) in the format XX.X the range (0,100)

    Raises:
        None.
    """

    d_mass = wt_finish - wt_start
    loss = 100*d_mass/wt_start
    percent_loss = truncate(loss,1)

    return percent_loss

def closing_sequence(original_dict):
    """
    Creates a dictionary with specific user inputs and calculations.

    BEWARE: if you are using this to update another dictionary, know that ".update()" overwrites any common keys

    Parameters:
        original_dict: (dict) the batch dictionary
            (This is only used to poll 'starting_wt' so far)
        
    Returns: 
        temp_dict: (dict) the additional items which can then be used to update the primary (batch) dictionary

    Raises:
        ValueError: if an non-numerical number is entered as the final weight.
    """

    temp_dict={}
    # determine final weight of the beans
    while True:
        try:
            final_comments = raw_input("Enter optional roast comments or <Enter> to continue:  ")
            if final_comments: 
                temp_dict['comments'] = original_dict['comments'] + final_comments

            query = raw_input("Enter the final weight in grams (example: 80)... ")
            if query == "":
                # enters an a nonsense value for rapid testing/bypass
                query = original_dict['starting_wt']

            temp_dict['final_wt'] = float(query)
            loss_percent = calc_loss_percent(original_dict['starting_wt'], temp_dict['final_wt'])

            print "mass loss: %.f%%" % loss_percent
            temp_dict['percent_loss'] = loss_percent

            break
        except ValueError:
            print "Invalid entry. Enter a number."
            continue

    return temp_dict



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    
   
if __name__ == "__main__":
    # initiate the first due dates.  This could be done earlier on but then we tend
    # to get UnboundLocalError due to the += assignment that thappens for each event.
    # alternatively, they could all be marked global but that seems sketchy too.
    read_next  = READ_OFFSET
    smooth_next= SMOOTH_OFFSET
    print_next = PRINT_OFFSET
    write_next = WRITE_OFFSET

    if USING_FAKE_DATA: load_fake_data()    



    welcome_message()
    batch = generate_batch_dict()
    profile = load_roast_profile()
    display_preliminary_temps()
    wait_for_user()





    # and we're up and running...
    t_initial = time.time()

    #the try statement allows for a soft exit via Ctrl+C
    try:
        while True:
            # determine how much time has elapsed (seconds)
            elapsed = time.time() - t_initial

            # we don't need all that accuracy so we'll work with a truncated version of it
            elapsed_trunc = truncate(elapsed,3)


            # four events happen in this loop: READ, SMOOTH, PRINT, and WRITE
            # the basic flow goes like this:
            # if we reached or passed the due date (total elapsed time in seconds) for the event:
                # do it
                # then determine the next time this event will be run



            # READ SENSORS
            if elapsed >= read_next:

                # grab the temperature from the sensor
                temp, temp_is_valid = get_valid_reading(elapsed)
                
                # write it to the batch dictionary
                if temp_is_valid:
                    batch['temp_actual'].append([elapsed_trunc, temp])
                else:
                    # we're fine just ignoring bad readings,
                    # the time-series approach for storing batchs facilitates this
                    pass

                read_next += READ_FREQ


            # SMOOTHING DATA
            # the sensor reading is really noisy and jumps around a lot.
            # It's not reliable to use for controlling yet.  It must be smoothed my some means.
            if elapsed >= smooth_next:
                
                # send the last x time-and-temperature pairs to the smoothing function
                smoothed = smooth_data(batch['temp_actual'][-SMOOTH_OVER:])

                # add that value to the batch dictionary
                batch['temp_smooth'].append([elapsed_trunc, smoothed])

                smooth_next += SMOOTH_FREQ


            # PRINT TO TERMINAL
            if elapsed >= print_next:

                # prints the desired info from the batch dictionary to the screen, with formatting
                print 'Time: %s\tBean: %.1f\tAverage: %.1f\t%s' % (convert_time(elapsed), batch['temp_actual'][-1][1], batch['temp_smooth'][-1][1], FAKE_MESSAGE)

                print_next += PRINT_FREQ


            # WRITE TO FILE
            # this is the export file.  If you knew that the program wouldn't crash, you could just
            # do this once, at the end.   Until then, it "backs up" the batch dictionary on
            # the WRITE_FREQ interval if we reached the due date for the next event.
            if elapsed >= write_next:

                # this really should use the WITH statement
                # from: https://stackoverflow.com/questions/11026959/python-writing-dict-to-txt-file-and-reading-dict-from-txt-file
                json.dump(batch, open(batch['full_filename'], 'w'))

                # and then schedule the next event
                write_next += WRITE_FREQ


    except KeyboardInterrupt:
        # this is the soft exit
        print "\n"
        pass



    # add post-roast data, calculations, and comments
    batch.update(closing_sequence(batch))

    # do a final write to the output file so as not to lose the last bit of data that may have
    # accumulated since the last write and post-roast additions as well as the closing_sequence().
    json.dump(batch, open(batch['full_filename'], 'w'))
    print "\ncomplete.\n"



