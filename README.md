# roast


NOTES TO SELF: 
========================================
When it comes adding the PID control, remember that there is a 2-second delay on the smoothing calculation (see SMOOTH_OFFSET).
If you need more responsive PID control, you may need to come up with a better smoothing algorithm.

You are currently outputting to two files: a CSV (the old way, readable in Excel), and TXT (less readable, the standard for the software)... The CSV is nice for now while you are still developing the software (just lower the WRITE_FREQ) but it really should just go away.


QUESTIONS FOR JOHN:
========================================
All of my questions will amount to this: what are the programming best-practices that I've missed?

I'm really confused on when it is okay to use global variables or cheat and grab variables from another namespace (?) and whatnot.  I know there are a lot of strong opinions on this. I think I'm pretty inconsistent about them here. 
The problem really arises when I have multiple, nested functions and the innermost one needs some parameter while the others don't need it. I end up passing a parameter all the way in and returning it all the way out which is a nightmare.

Should everything be in a "main()" ?


