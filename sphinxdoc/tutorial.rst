
.. _tutorial:

################
 Tutorial
################

**************************
 Get/Build the Software
**************************

To get started with the software, make a new release directory and add the ParCorAna
package to it. Presently ParCorAna is not part of the ana release. For example, do
these commands::

  newrel ana-current ParCorAnaRel
  cd ParCorAnaRel
  sit_setup

  # now get a kerberos ticket to get code from the repository
  kinit   

  # now identify the most recent tag of ParCorAna
  psvn tags ParCorAna

  # suppose the last tag in the Vnn-nn-nn series is V00-00-25, then do
  addpkg ParCorAna V00-00-25
  scons

.. _configfile:

**************************
 Make a Config File
**************************

One first has to make a configuration file. This is a python file
that defines two dictionaries::

  system_params
  user_params

system_params defines a number of keys that the framework uses. user_params 
is only for the user module, the framework simple passes user_params through to the user module.

The simplest way to do this is to copy the default config file from the ParCorAna package.
From the release directory ParCorAnaRel where you have added the ParCorAna package, do::

  cp data/ParCorAna/default_params.py myconfig.py

Below we go over the config file. See comments in the config file for additional details.

The config file starts by importing modules used later. In particular::

  import numpy as np
  import psana
  import ParCorAna

It then defines the system_params dictionary to fill out::

  system_params={}

DataSource
=============

Next one specifies the datasource psana will read. It is recommended that one do this by 
specifying the run and experiment in separate variables. Then one can reuse those variables 
when specifying the h5output file to save results to.
::

  run = 1437
  experiment = 'xpptut13'
  system_params['dataset'] = 'exp=%s:run=%d' % (experiment, run) 

When doing online monitoring against live data, specify the ffb directory for the data, and
live mode. For example::

  system_params['dataset'] = 'exp=%s:run=%d:live:dir=/reg/d/ffb/xpp/xpptut13' % (experiment, run) 

This will start processing xtc files as soon as they appear on the ffb - usually a few seconds behind the shot.
Further by running with 6 servers on psfehq (see below), one should able read data as fast as it is it written (120hz).

If the DAQ streams for the run are not numbered 0-n, and you are using several servers to keep up with the 
data, you will need to explicitly list the streams. For example, if you are collecting from three DAQ streams
numbered 1,2 and 5, and also recording xtcav and other IOC's in stream 80 and 81 (and you need the IOC data
when deciding what events to include in the G2 calculation) one would do::

  system_params['dataset'] = 'exp=%s:run=%d:live:stream=1,2,5,80,81:dir=/reg/d/ffb/xpp/xpptut13' % (experiment, run) 

Then set numservers (below) to 3 for the three DAQ streams, 1,2 and 5. Note, if you do not need the
IOC streams for the G2 calculation, do not include them. Reading the IOC streams may slow down the servers to the point where they cannot read the data at 120hz.

These parameters::

  system_params['src']       = 'DetInfo(XppGon.0:Cspad.0)'
  system_params['psanaType'] = psana.CsPad.DataV2

tell the framework the source, and psana data type the framework needs to distribute to the workers.
The default values are for xpp tutorial data with full cspad. Because we did an "import psana" at the
top of the config file, we can directly use values like psana.CsPad.DataV2 in the config file.

Psana Configuration
====================

The parameters::

  system_params['psanaOptions']          # dictionary of psana options
  system_params['ndarrayProducerOutKey'] # event key string for ndarray producer output
  system_params['ndarrayCalibOutKey']    # event key string for NDarrayCalib output
  system_params['outputArrayType']       # such as psana.ndarray_float64_3

do the following

 * specify a psana configuration that loads the appropriate ndarray producer psana
   module for the detector data, and optionally (but most always) the NDarrayCalib psana module 
   that calibrates the ndarray
 * specify output keys for the two modules
 * specify the final array type the psana modules output

The framework specifies the psana configuration through a python dictionary rather than a config file.
To simplify the setting of these parameters, default_params.py uses a utilty function makePsanaOptions.
This function automatically figures out the correct psana modules to load and their options based on
the detector type.

Generally users will not need to modify the code in default_params.py which reads::

  system_params['ndarrayProducerOutKey'] = 'ndarray'
  system_params['ndarrayCalibOutKey'] = 'calibrated'    # set to None to skip calibration

  system_params['psanaOptions'], \
  system_params['outputArrayType'] = ParCorAna.makePsanaOptions(
                                       srcString=system_params['src'],
                                       psanaType=system_params['psanaType'],
                                       ndarrayOutKey=system_params['ndarrayProducerOutKey'],
                                       ndarrayCalibOutKey=system_params['ndarrayCalibOutKey']
                                     )

However users may want to adjust options to the calibration modules. For example, to add gain, one can add the
following line after the above::

  system_params['psanaOptions']['ImgAlgos.NDArrCalib.do_gain'] = True

default_params.py includes code that allows one to do::

  python default_params.py

to make sure there are no errors in the file, as well as to pretty print the final system_params and
user_params dictionaries. The resulting 'psanaOptions' from the above call to makePsanaOptions are::

  'psanaOptions': {'CSPadPixCoords.CSPadNDArrProducer.is_fullsize': 'True',
                  'CSPadPixCoords.CSPadNDArrProducer.key_out': 'ndarray',
                  'CSPadPixCoords.CSPadNDArrProducer.outkey': 'ndarray',
                  'CSPadPixCoords.CSPadNDArrProducer.outtype': 'float',
                  'CSPadPixCoords.CSPadNDArrProducer.source': 'DetInfo(XppGon.0:Cspad.0)',
                  'ImgAlgos.NDArrCalib.below_thre_value': 0,
                  'ImgAlgos.NDArrCalib.do_bkgd': False,
                  'ImgAlgos.NDArrCalib.do_cmod': True,
                  'ImgAlgos.NDArrCalib.do_gain': False,
                  'ImgAlgos.NDArrCalib.do_mask': False,
                  'ImgAlgos.NDArrCalib.do_nrms': False,
                  'ImgAlgos.NDArrCalib.do_peds': True,
                  'ImgAlgos.NDArrCalib.do_stat': True,
                  'ImgAlgos.NDArrCalib.do_thre': False,
                  'ImgAlgos.NDArrCalib.fname_bkgd': '',
                  'ImgAlgos.NDArrCalib.fname_mask': '',
                  'ImgAlgos.NDArrCalib.key_in': 'ndarray',
                  'ImgAlgos.NDArrCalib.key_out': 'calibrated',
                  'ImgAlgos.NDArrCalib.masked_value': 0,
                  'ImgAlgos.NDArrCalib.outtype': 'float',
                  'ImgAlgos.NDArrCalib.source': 'DetInfo(XppGon.0:Cspad.0)',
                  'ImgAlgos.NDArrCalib.threshold': 0,
                  'ImgAlgos.NDArrCalib.threshold_nrms': 3,
                  'modules': 'CSPadPixCoords.CSPadNDArrProducer ImgAlgos.NDArrCalib'},


One could also modify the above to directly set the psana options.

Note that the psana modules are instructed to the detector data array as float rather than double.
Currently the ParCorAna framework uses float32 for handling the detector data. In the future there
will be an option to support double, and possibly int16.

Worker Storage
================

As mentioned above, ParCorAna requires that the psana calibration module NDArrCalib produce
an ndarray of float as opposed to double. The framework will then scatter arrays of floats 
to the workers. It is reccommended that workers store this data as float32 as well.
This is what is done in default_params.py::

  system_params['workerStoreDtype'] = np.float32

One could set this to np.float64 if one is concerned about precision when accumulating
statistics for the correlation matricies. This is valid concern as one can do 50,000
multiply and adds of the calibrated detector pixels. A worse case upper bound for this 
accumulated result might be 10^14 (assumming 1<<15 is the maximum pixel value), however 
float32 can represent 10^38. 

Presently, using float64 for worker storage is untested, and 
the framework will have to downcast the worker's float64's to float32 in order gather
results for the viewer. That is the viewer will only get float32 results. In the 
future we will make float64 vs. float32 an option for the framework.

Mask File
===========

You need to provide the framework with a mask file for the detector data. This is a 
numpy array with the same dimensions as the ndarray that the psana ndarray producer 
module creates. This is not necessarily a 2D image that is easy to plot. In addition, 
you should create a testing mask file that includes a very small number of pixels 
(10 to 100) in the mask. The small number of pixels in the test mask file allows one to run 
a simple alternative calculation against the data to validate the calculation done
through the framework, as well as to debug a large part of the code outside the MPI
framework.
::

  system_params['maskNdarrayCoords'] = 'maskfile.npy' # not created yet
  system_params['testMaskNdarrayCoords'] = 'testmaskfile.npy' # not created yet


Number of Servers
===================

The servers are responsible for reading the data, forming and calibrating the detector arrays, and 
scattering these arrays to the workers. When developing, we usuaully specify 
one server. When analyzing data in live mode, we usually specify 6 servers, or however many
DAQ streams there are in the run. The framework sets things up so that each server only processes
one stream. As long as each server can run at 20hz the framework can potentially keep up with live 120hz data. 
If you are analyzing xtcav data, then each server will process 2 or more streams. The framework 
outputs timing at the end which gives us an idea of how fast or slow the servers are.
In live mode, specifying more than 6 servers will not help, rather it will waste too many ranks on servers.

In index mode, specifying more than six servers can help the servers run faster. However usually
the bottleneck will be with the workers, and more than six servers is not neccessary. The framework
outputs timing information at the end of runs that allow one to see what part of the system
is slow. Presently, little testing has been done in index mode. Most testing has been in live mode, or
offline mode with six servers. 

By default, the framework will pick distinct hosts to run the servers on. Distributing the I/O
among several hosts seems to improve performance, but this is debatable.
::

  system_params['numServers'] = 1
  system_params['serverHosts'] = None     # system selects which hosts to use

Times, Delays, update
========================
::

  system_params['times'] = 50000
  system_params['delays'] = ParCorAna.makeDelayList(start=1,
                                                    stop=25000, 
                                                    num=100, 
                                                    spacing='log',  # can also be 'lin'
                                                    logbase=np.e)
  system_params['update'] = 0      # how frequently to update, units are events

These parameters specify how many events we will store, and what the delays are. 
If one stores 50,000 events but there are 100,000 events in the dataset, the 
framework will start overwriting the oldest data at event 50,001. 

Above we are specifying 100 delays that are logarithmically spaced from 1 to 25,000 by
using a utility function in ParCorAna. However one can set their own delays::

  system_params['delays'] =  [    1,    10, 100, 1000]

Periodically, the workers are told that the correlation statistics for their pixels are 
going to be gathered together for the viewer. When 'update' is 0, 
this just happens once at the end. Otherwise 'update' specifies the number of events between
these gathers. If one is analyzing live data and producing plots, one could specify 2400 to get a 
plot for every 20 seconds of data (the frequency of the plots depends on how fast the system is
keeping up with data). . Recent tests (see section ??) with full cspad on the psfehq show that 
gathering results at the viewer typically take 1-2 seconds. In terms of keeping up with live 
data, this slows the worker down some. The viewer presently spends about 16 seconds processing 
the gathered data to form plots. If one asks for plots to frequently, the whole system will 
wait for the viewer to finish its last plots.

The other danger with plotting to frequently, is if one is also writing h5output. Currently, 
both h5output and plots are done with every update to the viewer (in the future this will be
changed). With 100 delays, each update will trigger the equivalent of 600 events worth 
(around 6 seconds) of full cspad to be written to the output file. This could slow things down 
significantly, and cause a lot of output to be created.

User Module
========================
::

  import ParCorAna.UserG2 as UserG2
  system_params['userClass'] = UserG2.G2atEnd

The userClass is where users hook in their worker code. We will be using the example 
class in the ParCorAna package - G2atEnd does a simplified version of the G2 
calculation used in XCS - however the file UserG2.py goes over three ways to do the G2
calculation:

 * **G2atEnd** workers store data during each event, do a O(T*D) calculation during updates (where T is number of times, and D is number of delays)
 * **G2IncrementalAccumulator** workers do O(D) work with each event, doing correlation over all times
 * **G2IncrementalWindowed** workers do O(D) work with each event, doing a windowed correlation, over the last T times

Note - G2IncrementalAccumulator is what has been tested the most for live data analysis - this is
the preferred method to use as it reduces the overall compute time.

More on this in section XXX???

H5Output
=============
The system will optionally manage an h5output file. This is not a file for collective MPI
writes. Within the user code, only the viewer rank can write to the file. The viewer
will receive an open group to the file at run time. 

Set h5output to None if you do not want h5 output - important to speed up online monitoring with 
plotting.

The system will recognize %T in the filename and replaces it with the current time in the format
yyyymmddhhmmss. (year, month, day, hour, minute, second). It will also recognize %C for a three
digit one up counter. When %C is used, it looks for all matching files on disk, selects the
one with the maximum counter value, and adds 1 to that for the h5output filename.

Testing is built into the framework by allowing one to run an alternative calculation
that receives the same filtered and processed events at the main calculation. When the
alternative calcuation is run, the framework uses the testh5output argument for the
filename.
::

  system_params['h5output'] = 'g2calc_%s-r%4.4d.h5' % (experiment, run)
  system_params['testh5output'] = 'g2calc_test_%s-r%4.4d.h5' % (experiment, run)

example of using %T and %C, note the %% in the value to get one % in the string after 
expanding experiment and run::

  system_params['h5output'] = 'g2calc_%s-r%4.4d_%%T.h5' % (experiment, run)
  system_params['h5output'] = 'g2calc_%s-r%4.4d_%%C.h5' % (experiment, run)

For re-running the analysis, set the below to True to overwrite existing h5 files::

  system_params['overwrite'] = False   

While the analysis is running, it adds the extension .inprogress to the output file.
The framework will never overwrite a .inprogress file, even if 'overwrite' is True.
If analysis crashed due to an error, these leftover files need to be manually removed.

Note: for using making use of the testing in the framework, (discussed later) use of 
the %C or %T options in the h5output and testH5output filenames will brake the ability 
of the framework to identify output files to compare. One could still run the compare 
tool to directly compare these output files.

Debugging/Develepment Switches
=====================================
::

  system_params['verbosity'] = 'INFO'
  system_params['numEvents'] = 0
  system_params['testNumEvents'] = 100

These options are useful during development or debugging. Setting the verbosity to
DEBUG greatly increases the amount of output. It can trigger additional runtime checks.
Typically it is only the first worker that outputs a message, as all the workers do the same 
thing.

One can also limit the number of events processes, and specify the number of event to process
during testing (for both the main code, and the alternative calculation). 


User Parameters
====================
The user_params dictionary is where users put all the options that the G2 calculation
will use.


Color/Bin/Label File
----------------------
This is a parameter that the UserG2 needs - a file that labels the detector pixels
and determines which pixels are averaged together for the delay curve. It bins the pixels
into groups. In this package, we call this a 'color' file following conventions in MPI
for grouping different ranks. More on this in the next section::

  user_params['colorNdarrayCoords'] = 'colorfile.npy' # not created yet

Note that the color 0 is ignored in the color file - no delay curve is produced for color 0.
Only colors 1 and above are used. If the framework observes many pixels with color 0 that
are included in the mask file - it will warn you in case you want to prepare a new mask to
exclude those pixels from worker calculations.

Fine Color/Bin/Label File
-----------------------------
This is a another parameter that the UserG2 needs. It is a color file that is used to 
replace sets of pixels with their average value before forming the final delay curve. 
This is applied to the IP and IF matricies before forming the final G2 curves. Note, 
these modified IP and IF matrices are used for calculating the G2 delay curves, 
however the modified IP/IF are not saved to the hdf5 file::

  user_params['colorFineNdarrayCoords'] = 'fineColorfile.npy' # not created yet

As with the color file, color 0 is ignored. Moreover, one should ensure that any pixel with a 
color that is nonzero, has a finecolor that is nonzero as well. 

Filtering Parameters
-----------------------
Often G2 calculations need to adjust/filter the data. The UserG2 module sets several 
parameters that it makes use of::

  user_params['saturatedValue'] = (1<<15)
  user_params['LLD'] = 1E-9
  user_params['notzero'] = 1E-5
  user_params['ipimb_threshold_lower'] = .05
  user_params['ipimb_srcs'] = []

Workers use saturatedValue to identify saturated pixels. Note - in practice, you want to pick a value
that works with the calibrated data - 1<<15 is the saturation value for the raw detector data, but 
workers receive calibrated data.

Workers use notzero to replace negative, 0, and small positive numbers in the worker data.

Servers use ipmb_srcs and ipimb_threshold_lower to look for low values in ipimb's. When a low value is
identified, the server does not send the data to the workers. It is skipped.


Plotting
----------
The UserG2 module uses the psmon package to plot.
This is the preffered method to plot for online monitoring where the analysis job
runs on a batch farm. The 'psmon_plot' parameter turns plotting on, and the 'plot_colors'
param allows one to specify a subset of colors to plot (otherwise all colors are plotted).
For now we set this value to False. Using psmon for plotting
will be covered in section XXX???
::

  user_params['psmon_plot'] = False
  user_params['plot_colors'] = None

There are also some options for debugging:
::

  user_params['print_delay_curves'] = False
  user_params['debug_plot'] = False
  user_params['iX'] = None
  user_params['iY'] = None

The first just prints statistics about the delay curves in the text output of the program.
'debug_plot' will bring up a plot of the gathered G2 and IF matricies for a few delays.
It will plot it in image space using the ndarray to image conversation matricies iX and
iY (discussed below).


***************************
 Create a Mask/Color File
***************************
The system requires a mask file that identifies the pixels to process.
Reducing the number of pixels processed can be the key to fast feedback during an experiment.
A userClass for correlation analysis will typically use two 'color' files to label
pixels to average together. The first, a coarser one, is used to average pixels for the
final delay curves. The second, a finer one, is used to replace sets of pixels with their
average value before forming the delay curves. In addition to the mask file for analyzing data, 
users should produce a testmask file for testing their compution. 
This file should only compute on a few (10-100) pixels.


The ParCorAna package provides a tool to make mask and color files in the numpy ndarray
format required. To read the tools help do::

  parCorAnaMaskColorTool -h

(Another tool to look at is roicon, also part of the analysis release). The command::

  parCorAnaMaskColorTool --start -d 'exp=xpptut13:run=1437' -t psana.CsPad.DataV2 -s 'DetInfo(XppGon.0:Cspad.0)' -n 300 -c 6 --finecolor 18

Will produce a mask, testmask, color and fineColor file suitable for this tutorial::

  xpptut13-r1437_XppGon_0_Cspad_0_mask_ndarrCoords.npy  
  xpptut13-r1437_XppGon_0_Cspad_0_testmask_ndarrCoords.npy  
  xpptut13-r1437_XppGon_0_Cspad_0_color_ndarrCoords.npy 
  xpptut13-r1437_XppGon_0_Cspad_0_finecolor_ndarrCoords.npy 

Note that our input will be ndarr files, not image files. The mask file is only  0 or 1. It is 1
for pixels that we **INCLUDE**. The color file uses 6 colors (since we gave the -c 6 option to the tool. 
The finecolor file will have 18 colors (since we used the --finecolor 18 option).
As an example, these colors bin pixels based on intensity. In practice users will want to bin pixels
based on other criteria.

Conversion from images to ndarrays is made possible by geometry files. If a geometry file is not present 
for your experiment, one should be deployed into the calibration area. One can also specify a geometry 
file with the -g file. 

Often people will edit image files to produce the mask and color file. These need to then be converted
back to ndarrays. The help for parCorAnaMaskColorTool explains how to do this. One issue with this though,
is that sometimes the geometry files map two ndarray pixels to the same image pixel, and do not map some
of the ndarray pixels to any image pixel. This means that the ndarray mask or color file produced from the
image file will have a few imperfections. For the cspad in the xpp tutorial data, the number of such pixels 
is quite small. The tool reports on this pixels. It also reports on the location of the 10 pixels chosen
for the mask.

Once you have modified these files, or produced similarly formatted files you are ready for the 
next step.

Add to Config
==================

Now in myconfig.py, set the mask, testmask, and color file::

  system_params['maskNdarrayCoords'] = 'xpptut13-r1437_XppGon_0_Cspad_0_mask_ndarrCoords.npy'
  system_params['testMaskNdarrayCoords'] = 'xpptut13-r1437_XppGon_0_Cspad_0_testmask_ndarrCoords.npy'
  user_params['colorNdarrayCoords'] = 'xpptut13-r1437_XppGon_0_Cspad_0_color_ndarrCoords.npy'
  user_params['colorFineNdarrayCoords'] = 'xpptut13-r1437_XppGon_0_Cspad_0_finecolor_ndarrCoords.npy'

Note that the last two parameters is to the user_params - the framework knows nothing about the coloring.
It is scattering detector data, and collecting delay curves - the UserG2 viewer code makes use of the
colorings to form these final delay curvers.

********************
Check Config File
********************

Once you have modified the config file, it is a good idea to check that it runs as python code, i.e, that
all the imports work and the syntax is correct::

  python myconfig.py

The __main__ body for the config file first does a pretty-print of the two dictionaries defined. It then
tries to find the mask and color files, and does some validity checks on them.

.. _runlocal:

***********************************
Run Software 
***********************************

Now you are ready to run the software. To test using a few cores on your local machine, do::

  mpiexec -n 4 parCorAnaDriver -c myconfig.py -n 100

This should run without error. Even though we are only running on 100 events, the viewer will be
gathering 100 (delays) * 32 * 388 * 185 (cspad dimensions) * 4 (float64) or close to 1GB.

***********************************
Results
***********************************
You can get a listing of what is in the output file by doing::

  h5ls -r g2calc_xpptut13-r1437.h5

The h5 file contains two groups at the root level::

  /system
  /user

In /system, one finds::

  /system/system_params    Dataset 
  /system/user_params      Dataset

  /system/system_params/maskNdarrayCoords Dataset 
  /system/user_params/color_ndarrayCoords Dataset
  /system/user_params/colorFine_ndarrayCoords Dataset

The first two are the system_params and user_params dictionaries from the config file.

The latter three are the mask, color and finecolor ndarrays specified in the system_params
and user_params.

In /user one finds whatever the user viewer code decides to write. The example 
UserG2 module writes, for example::

  /user/G2_results_at_539  Group
  /user/G2_results_at_539/G2 Group
  /user/G2_results_at_539/G2/delay_000001 Dataset {32, 185, 388}
  /user/G2_results_at_539/G2/delay_000002 Dataset {32, 185, 388}
  ...
  /user/G2_results_at_539/IF Group
  /user/G2_results_at_539/IF/delay_000001 Dataset {32, 185, 388}
  /user/G2_results_at_539/IF/delay_000002 Dataset {32, 185, 388}
  ...
  /user/G2_results_at_539/IP Group
  /user/G2_results_at_539/IP/delay_000001 Dataset {32, 185, 388}
  /user/G2_results_at_539/IP/delay_000002 Dataset {32, 185, 388}

*******************
Plotting
*******************
To do plots, set the following in the config file::

  user_params['psmon_plot'] = True

When plotting, you may not want to produce the h5output as well. If so, also set::

  system_params['h5output'] = None

When running with the psmon_plot parameter to True, In the output, one should see outupt similar to::

  2015-05-08 14:39:16,214 - viewer-rnk:2 - INFO - Run cmd: psplot --logx -s psana1501 -p 12301 MULTI

The command::

  psplot --logx -s psana1501 -p 12301 MULTI

or something similar is what one runs to see the plots. The host (psana1501 in above) will be 
different when you run. It is the host that the viewer is on. The port can be changed by setting
the option::

  user_params['psmon_port'] = 12301

in the config file.

You may not want to use the --logx option if the delays are linearly spaced.

The viewer always runs on rank 0, so one can do ::

  bjobs -w

To see what host you are launched on.

.. _runonbatch:

*****************************
Running on the Batch System
*****************************
When running on the batch system, for example online monitoring in xcs, one would do something like::

  bsub -q psfehpriorq -I -n 150 parCorAnaDriver -c myconfig.py

The -I option means interactive, so that the program output will go to the screen. This will let
you see the psplot command. However all you need to know is what host the viewer is on, and this is
typically the first host. Doing::
  
 bjobs -w

Will show you what the first host is as well.

*****************************
Timing
*****************************
To see if you can keep up with live data, look at the output messages. You will see lines like

TODO

*****************************
Testing
*****************************
see the testing page

*****************************
UserG2
*****************************
see the :ref:`usercode` section of the :ref:`framework` page.

..  LocalWords:  ParCorAna ParCorAnaRel cd kerboses
