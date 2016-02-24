#!/usr/bin/python


from random import randint
from Tkinter import *
import tkFileDialog
from tkFileDialog import askdirectory



def generate_dict_with_2d(k=4,l=10):
    # This function is only used for generating a dictionary for the purpose of testing.
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

def tk_ui_for_path(t = "Select the save location"):
    # Uses a Tkinter UI to select a path. 
    # Returns a path name as a string.
    try:
        print t
        # this fails when you don't have a $DISPLAY determined, presumably when you are working on the beaglebone headless?
        root = Tk()
        pth = askdirectory(parent=root, title=t, initialdir = './', mustexist = True)        #tkFileDialog is a part of Tkinter
        root.destroy()
        pth += "/"
        if pth == "/":
            raise Exception('You canceled out of the path selection window!')
    except:
        pth = "./"
    return pth

def user_select_files(message, limit=99):
    # grab the path for each file. This dialog should open in the "root" window of Tk
    # returns a list of file path and name strings
    # information on grabbing multiple files from the UI from: 
    #     https://stackoverflow.com/questions/16790328/open-multiple-filenames-in-tkinter-and-add-the-filesnames-to-a-list
    #     http://www.pythonbackend.com/topic/1354022597
    # define the top-level window for this Tkinter app
    root = Tk()        
    while True:
        get_filenames = tkFileDialog.askopenfilenames(parent=root,title=message)        # I think this is why I currently get the lone window left open...
        # allows this function to be used for multiple or single file selection.
        if len(get_filenames)<=limit:
            break
        else:
            print "file selection is limited to %i files" % limit
    root.destroy()
    # does not address no selection/canceled window
    return get_filenames

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

def dict2csv(my_dict, title="some header", only_export=[''], subscript1="_x", subscript2="_y"):

    # writes a dictionary of 2D lists to csv
    # assumes you have a filename already, likely based on the import filename
    # returns nothing

    # grab the save location from the user
    pth = tk_ui_for_path()

    # build the full file path and add an extension
    full_filename = pth+'/'+my_dict['filename']+'.csv'

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
            it_worked = False            # reset the flag, which checks to make sure at least one dictionary entry is still adding values
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
                print "export complete.\n"
                break

def convert_time(sec):
    """
    Converts seconds (float) to a human readable string

    Currently, it is only used for terminal output, not exporting.

    Parameters:
        None.

    Returns: 
        s: a string in the format mm:ss.0

    Raises:
        None.
    """

    m = int(sec)/60
    sec -= m*60
    s = "%02i:%04.1f" % (m, sec)
    return s

def wait_for_user():
    """ Just a simple break to allow the user to determine when we proceed.
    """

    wait=raw_input("\nHit <ENTER> to being...")    # wait for the user to say "Go"
    print '\nPress Ctrl-C to quit.\n'    

    return

def truncate(f, n):
    """
    Truncates a float to n places (not rounding)
    Source: https://stackoverflow.com/questions/783897/truncating-floats-in-python

    Parameters:
        f: (float) the value to be truncated
        n: (int) the number of places to keep

    Returns:
        (float) the truncated value        

    Raises:
        None.
    """

    # probably should be moved over to modGregory.py
    s = '%.12f' % f
    i, p, d = s.partition('.')

    return float('.'.join([i, (d+'0'*n)[:n]]))



def c_to_f(c):
    """ Takes a celsius (float) and returns a fahrenheit (float)
    """
    return c * 9.0 / 5.0 + 32.0