
import os
import glob

RED   = "\033[1;31m"
BLUE  = "\033[1;34m"
GREEN = "\033[0;32m"
RESET = "\033[0;0m"
BOLD    = "\033[;1m"
REVERSE = "\033[;7m"
print(REVERSE + 'Running SMART resubmit script for CRAB3...' + RESET)
print('Good luck!\n')


Ncomplete = 0
Nrunning = 0
Nresubmitted = 0
Nfailed = 0



os.makedirs('completed', exist_ok=True)

def parseStatus(path):
    status = {
        'Status on the CRAB server': None,
        'Status on the scheduler': None,
        'Jobs status': None,
        'Output dataset': None,
        'Publication status': None,
        }

    with open(path) as statusfile:
        for line in statusfile.readlines():
            for key in status.keys():
                if key in line:
                    status[key] = line.strip().split('\t')[-1]

    return status



for path in glob.glob('crab_*/*'):
    message = path

    # get status
    os.system('crab status {path} &> {path}/status.txt'.format(path=path))
    status = parseStatus(path + '/status.txt')


    # job complete
    if status['Status on the scheduler'] == 'COMPLETED':
        Ncomplete +=1
        message = GREEN + 'COMPLETE\t' + message + RESET
        os.makedirs('completed/' + os.path.split(path)[0], exist_ok=True)
        os.system('mv {path} completed/{path}'.format(path=path))

    # running jobs
    elif status['Status on the scheduler'] == 'SUBMITTED':
        Nrunning +=1
        message = BOLD + 'RUNNING  \t' + message + RESET

    # failed jobs to resubmit
    elif status['Status on the scheduler'] == 'FAILED':
        Nresubmitted +=1
        message = BLUE + 'RESUBMITTED\t' + message + RESET
        os.system('crab resubmit --maxmemory=3500 {path} &> {path}/resubmit.txt'.format(path=path))

    # something went wrong
    else:
        Nfailed +=1
        message = RED + 'ERROR\t' + message + RESET
        print(status)

    print(message)


print(BOLD)
print('+++ DONE +++')
print('{} total jobs'.format(Ncomplete + Nrunning + Nresubmitted + Nfailed))
print('{} complete jobs'.format(Ncomplete))
print('{} running jobs'.format(Nrunning))
print('{} resubmitted jobs'.format(Nresubmitted))
print('{} failed jobs'.format(Nfailed))
print(RESET)
