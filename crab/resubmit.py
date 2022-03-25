
import os
import glob


for path in glob.glob('crab_*/*'):
    print('\n\n' + path)
    os.system('crab resubmit ' + path)

