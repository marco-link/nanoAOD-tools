import sys

def transform(l):
    n = int(l)
    if n==5: return 0
    elif n==4: return 1
    elif n==0: return 2
    else:
        print 'ERROR: wrong jet flavour'
        sys.exit()

infile = sys.argv[1]
outfile = infile.replace('.csv','_conv.csv')

f = open(infile,'r')
of = open(outfile,'w')
inlines = f.read().splitlines()

for i,line in enumerate(inlines):
    ll = line.split(',')
    if i==0:
        nentries = len(ll)
        ix = ll.index('jetFlavor')
        of.write(line)
    else:
        if len(ll)!=nentries:
            print 'ERROR: wrong format'
            sys.exit()
        of.write('3')
        for j,l in enumerate(ll):
            if j==0: continue
            of.write(',')
            if j!=ix:
                of.write(l)
            else:
                of.write(str(transform(l)))
        of.write('\n')
