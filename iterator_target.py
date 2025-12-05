import os,sys,glob
import argparse


def run_single_target(target_name):
    os.system('LoDeSSdb.py test-connection')
    os.system(f'LoDeSSdb.py inprog {target_name}')
    print(f'Starting field {target_name}')
    os.system(f'LoDeSS_target.py {target_name}')
    os.chdir('../')
    os.system(f'LoDeSSdb.py finished {target_name}')
    os.system(f'LoDeSSdb.py upload {target_name}')
    os.chdir('../../')


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-s','--single',action='store_true')
    parser.add_argument('-c','--continuous',action='store_true')
    parser.add_argument('-f','--field',type=str)
    args = parser.parse_args()
    if args.single:
        run_single_target(args.field)
    elif args.continuous:
        field = os.popen('LoDeSSdb.py pullrandom').read().split(': ')[-1]
        print(field)

if __name__ == '__main__':
    main()
