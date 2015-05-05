#--------------------------------------------------------------------------
# Description:
#   Test script for ParCorAna
#   
#------------------------------------------------------------------------


#--------------------------------
#  Imports of standard modules --
#--------------------------------
import sys
import os
import logging
#import stat
import tempfile
import unittest
from cStringIO import StringIO
#import subprocess as sb
#import collections
#import math
import numpy as np
import h5py
import glob
import shutil
#-----------------------------
# Imports for other modules --
#-----------------------------
import psana
from AppUtils.AppDataPath import AppDataPath
import psana_test.psanaTestLib as ptl

#import h5py
#import psana_test.psanaTestLib as ptl

import ParCorAna as corAna

### helper function
def runCmd(cmd, verbose=True):
    o,e,retcode = ptl.cmdTimeOutWithReturnCode(cmd)
    if verbose: print "---  ran cmd: %s" % cmd
    if verbose: print "output=%s\n\nerror=%s" % (o,e)
    if verbose: print "return code=%r" % retcode
    return retcode

def removeAllInProgressFromParentDir(fname):
    basedir, basename = os.path.split(fname)
    assert len(basedir)>0 and os.path.exists(basedir)
    inProgressFiles = glob.glob(os.path.join(basedir, "*.inprogress"))
    for inProgress in inProgressFiles:
        os.unlink(inProgress)

def unindent(x):
    def numSpacesStart(ln):
        n=0
        while len(ln)>0 and ln[0]==' ':
            ln = ln[1:]
            n+= 1
        return n
    lns = x.split('\n')
    allLeadingSpaces = [numSpacesStart(ln) for ln in lns if len(ln.strip())>0]
    minLeadingSpaces = min(allLeadingSpaces)
    return '\n'.join([ln[minLeadingSpaces:] for ln in lns])

class ParCorAna( unittest.TestCase ) :

    def setUp(self) :
    	""" 
    	Method called to prepare the test fixture. This is called immediately 
    	before calling the test method; any exception raised by this method 
    	will be considered an error rather than a test failure.  
    	"""
        pass

    def tearDown(self) :
        """
        Method called immediately after the test method has been called and 
        the result recorded. This is called even if the test method raised 
        an exception, so the implementation in subclasses may need to be 
        particularly careful about checking internal state. Any exception raised 
        by this method will be considered an error rather than a test failure. 
        This method will only be called if the setUp() succeeds, regardless 
        of the outcome of the test method. 
        """
        pass

    def test_parseDataSetString(self):
        '''test parseDataSetString function
        '''
        dsOpts = corAna.parseDataSetString('exp=amo123:run=12')
        self.assertEqual(dsOpts['exp'],'amo123')
        self.assertEqual(dsOpts['run'],[12])
        self.assertEqual(dsOpts['h5'],False)
        self.assertEqual(dsOpts['xtc'],True)
        self.assertEqual(dsOpts['live'],False)
        self.assertEqual(dsOpts['shmem'],False)
        
    def test_noConfig(self):
        system_params = {}
        user_params = {}
        test_alt = False
        self.assertRaises(AssertionError, corAna.CommSystemFramework, system_params, user_params, test_alt)

    def test_logger(self):
        msg1 = 'hi there'
        msg2 = 'what?'
        try:
            stdout = sys.stdout
            stderr = sys.stderr
            sys.stdout = StringIO()
            sys.stderr = StringIO()
            self.assertRaises(AssertionError, corAna.makeLogger, False, True, True, True, 0, 'INFO', False)
            l = corAna.makeLogger( False, True, False, False, 0, 'INFO', False)
            l2 = corAna.makeLogger( False, True, False, False, 0, 'INFO', False) # make sure getting another ref doesn't double handlers
            l.info(msg1)
            l.warning(msg2)
        except Exception,e:
            sys.stdout = stdout
            sys.stderr = stderr
            raise e

        stderrLns = [ln for ln in sys.stderr.getvalue().split('\n') if len(ln.strip())>0]
        stdoutLns = [ln for ln in sys.stdout.getvalue().split('\n') if len(ln.strip())>0]
        sys.stderr.close()
        sys.stdout.close()
        sys.stdout = stdout
        sys.stderr = stderr

        self.assertEqual(len(stderrLns),2)
        self.assertEqual(len(stdoutLns),0)

        self.assertTrue(stderrLns[0].find('INFO')>0 and stderrLns[0].find(msg1)>0, msg='log ln=%s does not have INFO nor %s in it' % (stderrLns[0], msg1))
        self.assertTrue(stderrLns[1].find('WARNING')>0 and stderrLns[1].find(msg2)>0, msg='log ln=%s does not have WARNING nor %s in it' % (stderrLns[1], msg2))


class Cspad2x2( unittest.TestCase ) :
    '''Test on small cspad2x2
    '''
    def setUp(self) :
    	""" 
    	Method called to prepare the test fixture. This is called immediately 
    	before calling the test method; any exception raised by this method 
    	will be considered an error rather than a test failure.  
    	"""
        dataDir = os.path.join(ptl.getMultiFileDataDir(), 'test_013_xcsi0314')
        experiment = 'xcsi0314'
        run = 178  

        maskColorDir = os.path.join(dataDir, 'maskColorDir')
        maskFileBaseName = '%s-r%d_XcsEndstation_0_Cspad2x2_0_mask_ndarrCoords.npy' % (experiment, run)
        testMaskFileBaseName = '%s-r%d_XcsEndstation_0_Cspad2x2_0_testmask_ndarrCoords.npy' % (experiment, run)
        colorFileBaseName =  '%s-r%d_XcsEndstation_0_Cspad2x2_0_color_ndarrCoords.npy' % (experiment, run)
        maskFile = os.path.join(maskColorDir, maskFileBaseName)
        testMaskFile = os.path.join(maskColorDir, testMaskFileBaseName)
        colorFile = os.path.join(maskColorDir, colorFileBaseName)

        assert os.path.exists(maskFile), "mask file %s doesn't exist" % maskFile
        assert os.path.exists(testMaskFile),  "test maskfile %s doesn't exist" % testMaskFile
        assert os.path.exists(colorFile),  "color file %s doesn't exist" % colorkFile

        numServers = 1
        
        # make a random directory for the testing that we will remove when done
        destDirBase = AppDataPath(os.path.join("ParCorAna","testingDir")).path()
        assert len(destDirBase)>0, "did not find testingDir base dir in the ParCorAna data dir"
#        tempDestDir = tempfile.mkdtemp(dir=destDirBase)
        tempDestDir = os.path.join(destDirBase, "mytest")   # DVD REMOVE
        if not os.path.exists(tempDestDir): os.mkdir(tempDestDir)
        h5outputBaseName = 'g2calc_cspad2x2_%%s_%s-r%4.4d.h5' % (experiment, run)  # has %%s for for testName
        testH5outputBaseName = 'test_' + h5outputBaseName
        h5outputFile = os.path.join(tempDestDir, h5outputBaseName)
        testH5outputFile = os.path.join(tempDestDir, testH5outputBaseName)
        removeAllInProgressFromParentDir(h5outputFile)
        userClass = '--TESTS-MUST-FILL-THIS-IN--'
        testName = '--TESTS-MUST-FILL-THIS-IN--'
        numTimes = 100  # test data only has 60 events
        delays = [1, 2, 3, 5, 7, 10, 15, 23, 34, 50]
        self.formatDict = locals().copy()

        self.numEvents = 60     # There are 60 events in the test data.
        # these 60 events go from fiducials 33132 -> 33312, they go by 3 *except* that they skip 
        # fiducial 33300. So as 120hz counter times, these go from 1 to 61 and they skip 57. 
        # the number of delay counts we'll get will be 60-delay for delays > 4
        # and 59-delay for delays <=4.
        def expectedDelay(delay):
            if delay > 4: return 60 - delay
            return 59-delay
        self.expectedCounts = [expectedDelay(delay) for delay in delays]
        # Here are commands to see this:
#        eventCountCmd = 'psana -m PrintEventId %s/e*-r%4.4d*.xtc | grep fiducials | grep -v "fiducials=131071" | wc' % (self.dataDir, self.run)
#        evtCountOut, evtCountErr = ptl.cmdTimeOut(eventCountCmd)
#        numEventsFromCmd = int(evtCountOut.split()[0])
#        self.assertEqual(numEvents, numEventsFromCmd, "ran cmd=%s expected to get %d events, but got %d" % (eventCountCmd, numEvents, numEventsFromCmd))


        self.tempDestDir = tempDestDir
        self.dataDir = dataDir
        self.run = run

        self.configFileContent='''
        import psana
        import numpy as np
        import ParCorAna as corAna

        system_params = {{}}
        system_params['dataset']   = 'exp={experiment}:run={run}:dir={dataDir}'
        system_params['src']       = 'DetInfo(XcsEndstation.0:Cspad2x2.0)'
        system_params['psanaType'] = psana.CsPad2x2.ElementV1 
        system_params['ndarrayProducerOutKey'] = 'ndarray'
        system_params['ndarrayCalibOutKey'] = 'calibrated'
        system_params['psanaOptions'], system_params['outputArrayType'] = \\
                corAna.makePsanaOptions(srcString=system_params['src'],
                                   psanaType=system_params['psanaType'],
                                   ndarrayOutKey=system_params['ndarrayProducerOutKey'],
                                   ndarrayCalibOutKey=system_params['ndarrayCalibOutKey'])

        system_params['workerStoreDtype']=np.float32
        system_params['maskNdarrayCoords'] = '{maskFile}'
        system_params['testMaskNdarrayCoords'] = '{testMaskFile}'
        system_params['numServers'] = {numServers}
        system_params['serverHosts'] = None  # None means system selects which hosts to use (default). 
        system_params['times'] = {numTimes}
        system_params['update'] = 0
        system_params['delays'] = {delays}
        testName = '{testName}'
        system_params['h5output'] = '{h5outputFile}' % testName
        system_params['testH5output'] = '{testH5outputFile}' % testName
        system_params['overwrite'] = True
        system_params['verbosity'] = 'INFO'
        system_params['numEvents'] = 0
        system_params['testNumEvents'] = 0


        import ParCorAna.UserG2 as UserG2
        system_params['userClass'] = {userClass}

        user_params = {{}}
        user_params['colorNdarrayCoords'] = '{colorFile}'
        user_params['saturatedValue'] = (1<<15)
        user_params['LLD'] = 1E-9
        user_params['notzero'] = 1E-5
        user_params['psmon_plot'] = False
        '''

    def tearDown(self) :
        """
        Method called immediately after the test method has been called and 
        the result recorded. This is called even if the test method raised 
        an exception, so the implementation in subclasses may need to be 
        particularly careful about checking internal state. Any exception raised 
        by this method will be considered an error rather than a test failure. 
        This method will only be called if the setUp() succeeds, regardless 
        of the outcome of the test method. 
        """
        pass
#        shutil.rmtree(self.tempDestDir, ignore_errors=True)  DVD REMOVE


    def test_FilesSame(self):
        '''
        check that the input files haven't changed
        '''
        md5sums={'maskColorDir/xcsi0314-r178_XcsEndstation_0_Cspad2x2_0_color_ndarrCoords.npy':     'dad6ebe25b364eeea4114c036b54ea4c',
                 'maskColorDir/xcsi0314-r178_XcsEndstation_0_Cspad2x2_0_mask_ndarrCoords.npy':      '9b8ade01f93fc087228c15cad9944856', 
                 'maskColorDir/xcsi0314-r178_XcsEndstation_0_Cspad2x2_0_testmask_ndarrCoords.npy':  '282715e77fb5e4247a6b0851f3b244ea', 
                 'e524-r0178-s00-c00.xtc':                                                          'b73a43ee4393c8c793d430f951cad021', 
                 'e524-r0178-s01-c00.xtc':                                                          'eee2248370bef1a94202d5d6afd89799', 
                 'e524-r0178-s02-c00.xtc':                                                          'd340d899c5ab36f34b75df419af3b711', 
                 'e524-r0178-s03-c00.xtc':                                                          '111d1ab55c6bbb685bea7d5501587e1d', 
                 'e524-r0178-s04-c00.xtc':                                                          '18fcbc6eec20d2a94f31750f49dc1bda', 
                'e524-r0178-s05-c00.xtc':                                                           '9d87909f0c613ca6433fc94d0985521d' 
        }
        for fname, prev_md5 in md5sums.iteritems():
            fullFname = os.path.join(self.dataDir,fname)
            assert os.path.exists(fullFname)
            cur_md5 = ptl.get_md5sum(fullFname)
            self.assertEqual(cur_md5, prev_md5, msg="md5 has changed for %s. old=%s new=%s" % \
                             (fullFname, prev_md5, cur_md5))
        
    def writeConfigFile(self, configname):
        configFileName = os.path.join(self.tempDestDir, configname)
        configFile = file(configFileName, 'w')
        configFile.write(unindent(self.configFileContent.format(**self.formatDict)))
        configFile.close()
        return configFileName

    def checkDelays(self, h5fileName, delays, expectedCounts):
        h5file = h5py.File(h5fileName,'r')
        systemDelays = list(h5file['system/system_params/delays'][:])
        userDelays = list(h5file['user/G2_results_at_000060/delays'][:])
        self.assertListEqual(delays, systemDelays, msg='delays written to config != system delays')
        self.assertListEqual(systemDelays, userDelays, msg="in h5 output file, system and user section do not have same delays")
        counts = list(h5file['user/G2_results_at_000060/delay_counts'][:])
        self.assertEqual(len(counts), len(expectedCounts))
        self.assertListEqual(counts, expectedCounts, msg="delay counts wrong.\nAns=%r\nRes=%r\nDly=%r" % \
                             (expectedCounts,  counts, list(delays)))

    def test_G2atEnd(self):
        self.formatDict['userClass']='UserG2.G2atEnd'
        testName = 'atEnd'
        self.formatDict['testName'] = testName
        configFileName = self.writeConfigFile('config_G2atEnd.py')

        cmd = 'mpiexec -n 4 parCorAnaDriver --test_main -c ' + configFileName
        self.assertEqual(0, runCmd(cmd, verbose=True), msg="Error running %s" % cmd)

        # check delays
        h5outputFile = self.formatDict['h5outputFile'] % testName
        self.checkDelays(h5outputFile , self.formatDict['delays'], self.expectedCounts)

        cmd = 'parCorAnaDriver --test_alt -c ' + configFileName
        self.assertEqual(0, runCmd(cmd, verbose=True), msg="Error running %s" % cmd)

        cmd = 'parCorAnaDriver --cmp -c ' + configFileName
        self.assertEqual(0, runCmd(cmd, verbose=True), msg="error running %s - files must differ" % cmd)
        
    def test_G2IncrementalAccumulator(self):
        self.formatDict['userClass']='UserG2.G2IncrementalAccumulator'
        testName = 'incrAccum'
        self.formatDict['testName'] = testName
        configFileName = self.writeConfigFile('config_G2IncrementalAccumulator.py')

        cmd = 'mpiexec -n 4 parCorAnaDriver --test_main -c ' + configFileName
        self.assertEqual(0, runCmd(cmd, verbose=True), msg="Error running %s" % cmd)

        # check delays
        h5outputFile = self.formatDict['h5outputFile'] % testName
        self.checkDelays(h5outputFile, self.formatDict['delays'], self.expectedCounts)

        cmd = 'parCorAnaDriver --test_alt -c ' + configFileName
        self.assertEqual(0, runCmd(cmd, verbose=True), msg="Error running %s" % cmd)

        cmd = 'parCorAnaDriver --cmp -c ' + configFileName
        self.assertEqual(0, runCmd(cmd, verbose=True), msg="error running %s - files must differ" % cmd)
        
    def test_G2Window(self):
        self.formatDict['userClass']='UserG2.G2IncrementalWindowed'
        testName = 'windowa'
        self.formatDict['testName'] = testName
        self.formatDict['numTimes'] = 20   # 60 events, so we will get a smaller window
        delays = self.formatDict['delays']
        self.assertListEqual(delays,[1,2,3,5,7,10,15,23,34,50])        
        # ---  the twenty fiducials we will have will effectively look like
        # 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 -- 18 19 20 21
        self.expectedCounts = [ 18, 17, 16, 15, 13, 10, 5, 0, 0, 0]
        configFileName = self.writeConfigFile('config_G2windoweda.py')

        cmd = 'mpiexec -n 4 parCorAnaDriver --test_main -c ' + configFileName
        self.assertEqual(0, runCmd(cmd, verbose=True), msg="Error running %s" % cmd)

        # check delays
        h5outputFile = self.formatDict['h5outputFile'] % testName
        self.checkDelays(h5outputFile, self.formatDict['delays'], self.expectedCounts)

        cmd = 'parCorAnaDriver --test_alt -c ' + configFileName
        self.assertEqual(0, runCmd(cmd, verbose=True), msg="Error running %s" % cmd)

        cmd = 'parCorAnaDriver --cmp -c ' + configFileName
        self.assertEqual(0, runCmd(cmd, verbose=True), msg="error running %s - files must differ" % cmd)
        
        # we expect windowed incremental to produce the same result as G2 at end with a small numTimes
        self.formatDict['userClass']='UserG2.G2atEnd'
        self.formatDict['testName'] = 'windowedb'
        configFileName = self.writeConfigFile('config_G2windowedb.py')

        cmd = 'mpiexec -n 4 parCorAnaDriver --test_main -c ' + configFileName
        self.assertEqual(0, runCmd(cmd, verbose=True), msg="Error running %s" % cmd)

        h5A = h5outputFile
        h5B = self.formatDict['h5outputFile'] % testName
        cmd = 'cmpParCorAnaH5OutputPy %s %s' % (h5A, h5B)
        print "running cmd=%s" % cmd
        o,e,retcode = ptl.cmdTimeOutWithReturnCode(cmd)
        print "stdout=%s\nstderr=%s" % (o,e)
        self.assertEqual(0, retcode, msg="comparing windowed to atEnd with numTimes=%d failed" % self.formatDict['numTimes'])
        

if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0], '-v'])