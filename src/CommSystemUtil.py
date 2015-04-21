'''Utility functions for CommSystem
'''
import math
import logging

def checkCountsOffsets(counts, offsets, n):    
    '''Makes sure that the counts and offsets partition n. 
    
    Throws an exception if there is a problem

    Examples:
      >>> checkCountsOffsets(counts=[2,2,2], offsets=[0,2,4], n=6)
      # this is correct. 
      >>> checkCountsOffsets(counts=[2,2,2], offsets=[0,2,4], n=7)
      # incorrect, throws assert
      >>> checkCountsOffsets(counts=[2,2,2], offsets=[2,4,6], n=6)
      # incorrect, ect
    '''
    assert sum(counts)==n, 'counts=%r offsets=%r do not partition n=%d' % (counts, offsets, n)
    assert offsets[0]==0, 'counts=%r offsets=%r do not partition n=%d' % (counts, offsets, n)
    assert len(counts)==len(offsets), 'counts=%r offsets=%r do not partition n=%d' % (counts, offsets, n)
    for i in range(1,len(counts)):
        assert offsets[i]==offsets[i-1]+counts[i-1], 'counts=%r offsets=%r do not partition n=%d' % (counts, offsets, n)
    assert offsets[-1]+counts[-1]==n, 'counts=%r offsets=%r do not partition n=%d' % (counts, offsets, n)

def divideAmongWorkers(dataLength, numWorkers):
    '''partition the amount of data as evenly as possible among the given number of workers.

    Examples: 
      >>> divideAmongWorkers(11,3) 
      returns offsets=[0,4,8]
              counts=[4,4,3]    
    '''
    k = int(math.floor(dataLength / numWorkers))
    r = dataLength % numWorkers
    offsets=[]
    counts=[]
    nextOffset = 0
    for w in range(numWorkers):
        offsets.append(nextOffset)
        count = k
        if r > 0: 
            count += 1
            r -= 1
        counts.append(count)
        nextOffset += count
    checkCountsOffsets(counts, offsets, dataLength)
    return offsets, counts            
 
loggers = {}
   
def makeLogger(isTestMode, isMaster, isViewer, isServer, rank, lvl='INFO', propagate=False):
    '''Returns Python logger with prefix identifying master/viewer/server/worker & rnk

    If isTestMode is true, returns logger with 'noMpi' prefix.

    Args:
     isTestMode (bool): True if this is test mode. only additional parameter used
                        is lvl in this case.
     isMaster (bool): True if this is logger for master rank
     isViewer (bool): True if this is logger for viewer rank
     isServer (bool): True is this logger is for server rank
     rank (bool): rank to report
     lvl (str): logging level
     propogate (bool): True is logging message should propogage to parent

    Return:
      (logger): python logging logger is returned with formatting describing role in framework, and time of logged messages.
    '''
    numLevel = None
    if hasattr(logging,lvl.upper()) and isinstance(getattr(logging, lvl.upper()), int):
        numLevel = getattr(logging, lvl.upper())
    else:
        validLevels = ','.join([attr for attr in dir(logging) if attr.isupper() and isinstance(getattr(logging, attr),int)])
        raise ValueError("invalid verbosity/logging level=%s. valid levels are: %s" % (lvl, validLevels))
    global loggers

    loggerName = None
    if isTestMode:
        loggerName = 'testmode'
    else:
        assert int(isMaster) + int(isViewer) + int(isServer) in [0,1], "more than one of isMaster, isViewer, isServer is true"
        if isMaster:
            loggerName = 'master-rnk:%d' % rank
        elif isViewer:
            loggerName = 'viewer-rnk:%d' % rank
        elif isServer:
            loggerName = 'server-rnk:%d' % rank
        else:
            loggerName = 'worker-rnk:%d' % rank

    logger = loggers.get(loggerName,None)
    if logger is not None:
        return logger

    logger = logging.getLogger(loggerName)
    logger.setLevel(numLevel)
    logger.propagate=propagate
    ch = logging.StreamHandler()
    ch.setLevel(numLevel)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s' )
    ch.setFormatter(formatter)
    logger.handlers = []
    logger.addHandler(ch)
    loggers[loggerName]=logger
    return logger

def checkParams(system_params, user_params):
    expectedSystemKeys = set(['dataset',
                              'src',
                              'psanaType', 
                              'ndarrayProducerOutKey',
                              'ndarrayCalibOutKey', 
                              'psanaOptions',
                              'outputArrayType', 
                              'workerStoreDtype',
                              'maskNdarrayCoords',
                              'testMaskNdarrayCoords',
                              'numServers', 
                              'serverHosts',
                              'times', 
                              'update',
                              'delays',
                              'h5output', 
                              'testH5output',
                              'overwrite',
                              'verbosity', 
                              'numEvents', 
                              'userClass',
                              'testNumEvents'])

    undefinedSystemKeys = expectedSystemKeys.difference(set(system_params.keys()))
    newSystemKeys = set(system_params.keys()).difference(expectedSystemKeys)
    assert len(undefinedSystemKeys)==0, "Required keys are not in system_params: %r" % \
        (undefinedSystemKeys,)
    if len(newSystemKeys)>0 and MPI.COMM_WORLD.Get_rank()==0:
        sys.stderr.write("Warning: unexpected keys in system_params: %r\n" % (newSystemKeys,))
