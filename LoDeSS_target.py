import os
import sys
import glob
import shutil
import time
import numpy as np
import argparse
from awlofar.main.aweimports import CorrelatedDataProduct, \
    FileObject, \
    Observation


def download_file_from_surf(filename):
    # Download a file from the SURFdrive archive
    url = f'https://surfdrive.surf.nl/public.php/dav/files/fenDYKZ2RPekCT3/{filename}'
    os.system(f'wget -O {filename} "{url}"')

def call(cmd, testing):
    if testing:
        print(f"Testing mode: {cmd}")
    else:
        print(f"Executing: {cmd}")
        os.system(cmd)


def main():
    parser = argparse.ArgumentParser(description="LoDeSS Calibration")
    parser.add_argument("target", type=str,
                        help="target")
    parser.add_argument("--testing", help=argparse.SUPPRESS,
                        action="store_true", default=False)
    res = parser.parse_args()

    res = vars(res)

    # Read in the obsid list
    if not os.path.exists('obsidlist.txt'):
        download_file_from_surf('obsidlist.txt')
    targlist = 'obsidlist.txt'
    with open(targlist, 'r') as f:
        obsidlist = f.readlines()
    obsid_dict = {}
    for line in obsidlist:
        line = line.strip()
        if not line:
            continue
        obsid, targets = line.split(maxsplit=1)
        obsid_dict[obsid] = targets.split(',')


    devel = False
    if not devel:
        # Create a target directory
        os.mkdir(res["target"])
        os.chdir(res["target"])

        # Find obsids for target
        obsids = []
        for obsid, targets in obsid_dict.items():
            if res["target"] in targets:
                obsids.append(obsid)
        print('Calibrators required: ',obsids)
        # Test if iranet is locally available, see LoDeSS_cal.py
        os.mkdir('calibrators')
        os.chdir('calibrators')
        if False:
            if not os.path.exists('/iranet/groups/ulu/c.groeneveld/LoDeSS_cal/PROGRESS/TODO/'):
                # Download via ssh
                for obsid in obsids:
                    # tar file first
                    cmd = f'ssh c.groeneveld@gaia.ira.inaf.it tar -C /iranet/groups/ulu/c.groeneveld/LoDeSS_cal/archive/{obsid} -cf /iranet/groups/ulu/c.groeneveld/{obsid}.tar .'
                    call(cmd, res["testing"])
                    # Copy tar file
                    cmd = f'scp -r c.groeneveld@gaia.ira.inaf.it:/iranet/groups/ulu/c.groeneveld/{obsid}.tar .'
                    call(cmd, res["testing"])
                    # delete tar file on gaia
                    cmd = f'ssh c.groeneveld@gaia.ira.inaf.it rm /iranet/groups/ulu/c.groeneveld/{obsid}.tar'
                    call(cmd, res["testing"])
                    # untar file
                    os.mkdir(obsid)
                    cmd = f'tar -xf {obsid}.tar -C {obsid}'
                    call(cmd, res["testing"])
            else:
                # Copy from local iranet
                for obsid in obsids:
                    cmd = f'cp -r /iranet/groups/ulu/c.groeneveld/LoDeSS_cal/archive/{obsid} .'
                    call(cmd, res["testing"])
        if True:
            for obsid in obsids:
                download_file_from_surf(f'{obsid}.tar.gz')
                os.system(f'tar -xf {obsid}.tar.gz')

        os.chdir('..')

        # Begin with stager
        for obsid in obsids:
            cmd = f'LOFAR_stager.py -t {res["target"]} -n --nobug -p LT16_014 -o {obsid}'
            call(cmd, res["testing"])

        # Make LiLF.conf for the demix
        conf_file = "LiLF.conf"
        with open(conf_file, "w") as f:
            f.write("[LOFAR_preprocess]\n")
            f.write("demix_sources = [CasA,CygA]\n")
        
        # Run preprocesser
        cmd = 'LOFAR_preprocess.py'
        call(cmd, res["testing"])

        
    else: # devel mode, fix missing variables and chdirs
        print('skipping dl, preprocessor')
        os.chdir(f'{res["target"]}')
        # Find obsids for target
        obsids = []
        for obsid, targets in obsid_dict.items():
            if res["target"] in targets:
                obsids.append(obsid)
        print('Calibrators required: ',obsids)
    
    # Do timesplit for every observation
    # Move to the target directory
    if not devel:
        os.chdir('mss')
        for obsid in obsids:
            os.chdir(f'id{obsid}_-_{res["target"]}')
            os.mkdir('data-bkp')
            call('mv * data-bkp', res["testing"])

            # Set up the conf file for timesplit
            conf_file = 'LiLF.conf'
            get_cal_dir = f'../calibrators/{obsid}/'
            with open(conf_file, "a") as f:
                f.write("\n[LOFAR_timesplit]\n")
                f.write(f"cal_dir={get_cal_dir}/\n")
                f.write(f"apply_fr=False\n")  # For now...
            cmd = 'LOFAR_timesplit.py'
            call(cmd, res["testing"])
            os.chdir('..')  # Go back to mss directory
            
    else:
        os.chdir('mss')

    # Run DDparallel

    if not devel:
        os.mkdir('DD')
        os.chdir('DD')
        os.mkdir('mss')
        itera = 0
        for obsid in obsids:
            TCL = glob.glob(f'../id{obsid}_-_{res["target"]}/mss/*')
            TCL = sorted(TCL)
            for i in TCL:
                os.system(f'cp -r {i} mss/TC0{itera}.MS')
                itera += 1


        cmd = 'LOFAR_ddparallel.py'
        call(cmd, res["testing"])
    else:
        os.chdir('DD')

    cmd = 'LOFAR_ddserial.py'
    call(cmd, res["testing"])

    with open('../target.txt','w') as handle:
        handle.write(res['target'])

    cmd = 'LOFAR_quality.py'
    call(cmd,res["testing"])

if __name__ == "__main__":
    main()
