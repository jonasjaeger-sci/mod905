#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
"""
Main routine of RETIS program. 

Run RETIS by typing 'python RETIS.py workdir' with 'workdir' the
directory name that contains 
the job specific input called "input.py". 

All job-specific auxilary files need to be present in the working directory.
All output will be generated in this directory as well.
"""
import os, sys
from retis.fileio.filereader import readinputfile
#########################################################################
def getinput(workdir):
    """
    get input parameters
    """
    infile = os.path.join(workdir,'input.py')
    readinputfile(infile)
    return True
#########################################################################
def main(workdir):
    """
    read input, initialize, execute job, and finalize output
    """ 
    print("\n\nStarting Program RETIS.py\n\n")
    #get dictionary with all input parameters
    inputpar = getinput(workdir) 
    #initialization
    print("initialization ...")
    #execpar=exec_class(inputpar) 
    #del inputpar #clear memory
    #Now start our main loop
    print("Start main iteration loop ...")
    #while execpar.ITERATIONSTEP:
    #    execpar.ITERATE()
    #    execpar.OUTPUT()
    #execpar.FINALIZE()

#Start the program by executing main()
if __name__ == "__main__": 
    # check if user correctly typed 'python RETIS.py workdir'
    if len(sys.argv)!= 2:
        print("please type 'python RETIS.py workdir'", file=sys.stderr)
        print("with 'workdir' your working-directory", file=sys.stderr)
        sys.exit()
    workdir = sys.argv[1]
    main(workdir)
