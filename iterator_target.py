#! /usr/bin/env python

import os,sys,glob
import argparse


def run_single_target(target_name):
    os.system('LoDeSSdb.py test-connection')
    os.system(f'LoDeSSdb.py inprog {target_name}')
    print(f'Starting field {target_name}')
    outcode = os.system(f'LoDeSS_target.py {target_name}')
    outcode = outcode >> 8
    if outcode != 0:
        print(f"LoDeSS failed with exit code {outcode}")
        os.system(f'LoDeSSdb.py error {target_name}')
        sys.exit(outcode)
    os.chdir(f'{target_name}/mss')
    os.system(f'LoDeSSdb.py finished {target_name}')
    os.system(f'LoDeSSdb.py upload {target_name}')
    os.chdir('../../')


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-s','--single',action='store_true')
    parser.add_argument('-c','--continuous',action='store_true')
    parser.add_argument('-f','--field',type=str)
    parser.add_argument('-d','--delete_after',action='store_true')
    args = parser.parse_args()
    if args.single:
        run_single_target(args.field)
        if args.delete_after:
            print(f'Deleting {args.field}')
            os.system(f'rm -rf {args.field}')
    elif args.continuous:
        while True:
            field = os.popen('LoDeSSdb.py pullrandom').read().split(': ')[-1]
            run_single_target(field)
            # check if STOP file exists
            if args.delete_after:
                print(f'Deleting {field}')
                os.system(f'rm -rf {field}')

            if os.path.exists('STOP'):
                print("STOP file found, exiting.")
                sys.exit(0)

if __name__ == '__main__':
    main()
