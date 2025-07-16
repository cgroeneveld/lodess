
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
    parser.add_argument("--target_list", type=str, default="obsidlist.txt",help="File with obsid and target names. Should be generated with build_target_obsidlist.py")
    parser.add_argument("--testing", help=argparse.SUPPRESS,
                        action="store_true", default=False)
    res = parser.parse_args()

    res = vars(res)

    # Read in the obsid list
    targlist = res["target_list"]
    with open(targlist, 'r') as f:
        obsidlist = f.readlines()
    obsid_dict = {}
    for line in obsidlist:
        line = line.strip()
        if not line:
            continue
        obsid, targets = line.split(maxsplit=1)
        obsid_dict[obsid] = targets.split(',')


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
    os.chdir('..')

    # Begin with stager
    for obsid in obsids:
        cmd = f'LOFAR_stager.py -t {res["target"]} -n --nobug -p LT16_014 -o {obsid}'
        call(cmd, res["testing"])


if __name__ == "__main__":
    main()
