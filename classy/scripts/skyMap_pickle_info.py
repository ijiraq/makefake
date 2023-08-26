import lsst, logging
from lsst import log
import pickle, sys
l = log.Log()
l.setLevel(log.Log.DEBUG)
sm = pickle.load(open(sys.argv[1], 'rb'))
sm.logSkyMapInfo(l)

