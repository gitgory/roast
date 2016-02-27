#!/usr/bin/python

# I am running the BBB headless right now so, obviously, I need to run the viewer on the laptop if i want to SEE the graph

import json
# import matplotlib
# Force matplotlib to not use any Xwindows backend.
# see: https://stackoverflow.com/questions/2801882/generating-a-png-with-matplotlib-when-display-is-undefined
# matplotlib.use('Agg')

import matplotlib.pyplot as plt
from Tkinter import *
from modGregory import *

#VERSION = "16.02.06"        # just yy.mm.dd format of last update
variable_locker = []
available_data = []



def read_in_data(filenames):
    """
    Loads json data structures for a list of files into a list.

    It also adds the path and a nickname to to each json structure loaded in, based on filenames.

    Parameters:
        filenames: (tuple) of file names, including file path

    Returns: 
        a list of the the imports from the files in the form: [{'key':value,...},...]

    Raises:
        None.
    """

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

def get_desired_data(all_possible_data):
    """
    Opens a Tk window to allow the user to select the data they are interested in.

    Parameters:
        all_possible_data: (list) of keywords.  Ideally, this could be polled programatically, here,
            and proposed to the user based on whether the items were graphable and in common with all selected files.

    Returns: 
        a list of the keywords for the desired data.

    Raises:
        None.
    """    

    master = Tk()
    global variable_locker

    # Display some instructions in the UI window
    Label(master, text="Select the data series to display").grid(row=0, sticky=W)

    r = 0			# row counter

    # we will create a checkbox for each of the available data sets
    for option in all_possible_data:
        r += 1        # jump down to the next row
        # add a new IntVar to the locker
        variable_locker.append(IntVar())
        # display a checkbox for the option
        Checkbutton(master, text=option, variable=variable_locker[-1]).grid(row=r, sticky=W)

    
    # add some control Buttons
    Button(master, text='Show Graphs', command=master.destroy).grid(row=r+1, sticky=E, pady=4)
        
    mainloop()

    temp_data =[]
    for i in range(len(variable_locker)):
        #print variable_locker[i], " = ", variable_locker[i].get()
        if variable_locker[i].get():
            temp_data.append(all_possible_data[i])
    return temp_data

def graph_roasts(all_roasts, desired_data):
    """
    Creates a matplotlib graph of the desired_data from a list of roasts (json)

    Parameters:
        all_roasts: (list of json objects)
        desired_data: (list) of keywords in the json objects

    Returns: 
        None. Outputs a graph to the screen.

    Raises:
        None.
    """
        
    all_plots = []               # this supposed to be the equivalent of a handle for a plot, but for each plot
    legend_names = []            # collects all the nicknames for display to the legend
    
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
    
    # plot formatting
    plt.ylabel("Temp ('F)")
    plt.xlabel("Time (sec)")
    plt.legend(tuple(legend_names), prop={'size':11}, loc='lower right')

    # output them to a screen
    plt.show()

def generate_title(d):
    """ Creates a header string from important dictionary keys to display on the top of a human-readable *.csv file
    """
    # takes the bean dictionary and creates a title/header for the csv file (returns a string)
    title = "%s\nRun #%02.i,T_ambient = %.f\n\n"%(d['beanName'], d['run'], d['t_ambient'])
    return title

def welcome_message():
	""" Prints an ASCII welcome message.
	"""
    print "\n"*20
    print "\t\t\t************************************"
    print "\t\t\t*        Roast viewer              *"
    print "\t\t\t************************************"
    print "\n"*10
    return



def main():
    #global variable_locker
    global available_data

    welcome_message()

    while True:
        try:
            # get a list of all the files we're reading from (full path)
            print "Choose file(s) to view."
            filez = user_select_files("Choose file(s) to view.")

            # read in all the data from those files
            all_roasts = read_in_data(filez)
            break
            
        except ValueError:
            print "not a valid file type. file must contain a json data type"


    # as long as you actually picked some files, proceed.
    if len(all_roasts)>0:
        available_data = ['temp_actual', 'temp_smooth', 'upper_bound','lower_bound', 'target_temp']            # more could go here but i need error handling for the files that don't have keys with these legend_names

        desired_data = get_desired_data(available_data)


        if raw_input('Export to CSV?  [y/N]  ') in ['Y','y']:
            # ideally, you'd be passing in save location and filenames could be inferred from the roast dictionary
            # and then just notify the user of hte location (like how roast.py chooses the filename with a default save path) 
            for roast in all_roasts:
                t = generate_title(roast)
                try:
                    dict2csv(roast, title=t, only_export=desired_data, subscript1="_sec", subscript2="_val")
                except IOError:
                    # likely the user canceled the save location window
                    print "Invalid location. Canceling"



        if raw_input('Show graph?  [Y/n]  ') in ['Y','y','']:
            graph_roasts(all_roasts, desired_data)
    

    # but if you didn't actually pick any files to view...
    else:
        print "why would you come here if you didn't want to see any roasts?\n"


main()