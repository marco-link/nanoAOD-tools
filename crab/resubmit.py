
import os
import glob


for folder in ['crab_2016', 'crab_2017', 'crab_2018']:
    for path in glob.glob(folder + '/*'):
        print('\n\n' + path)
        os.system('crab resubmit ' + path)

