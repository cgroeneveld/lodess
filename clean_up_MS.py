'''
    hopefully this code will be useless soon
'''

import os
import sys,glob,shutil
import argparse
import pyrap.tables as pt

def main():
    parser = argparse.ArgumentParser(description='clean up MS files')
    parser.add_argument('--remove_model', help='if set, remove model files', default=True,type=bool)
    parser.add_argument('--remove_corrected', help='if set, remove corrected files', default=True,type=bool)
    parser.add_argument('file', help='input measurement set file',nargs='+')
    args = parser.parse_args()

    for fl in args.file:
        with pt.table(fl,readonly=False) as tb:
            colnamelist = tb.colnames()
            print(colnamelist)
            if 'CORRECTED_DATA' in tb.colnames() and args.remove_corrected:
                print('removing CORRECTED_DATA column from %s'%fl)
                tb.removecols('CORRECTED_DATA')
            if 'DATA_SUB' in tb.colnames() and args.remove_corrected:
                print('removing DATA_SUB column from %s'%fl)
                tb.removecols('DATA_SUB')
            for col in colnamelist:
                if 'MODEL_DATA' in col and args.remove_model:
                    print('removing %s column from %s'%(col,fl))
                    tb.removecols(col)
                elif 'PREDICT' in col and args.remove_model:
                    print('removing %s column from %s'%(col,fl))
                    tb.removecols(col)

if __name__=='__main__':
    main()