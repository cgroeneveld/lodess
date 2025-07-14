import os
import sys
import glob
import shutil
import time
import numpy as np
import argparse


def call(cmd, testing):
    if testing:
        print(f"Testing mode: {cmd}")
    else:
        print(f"Executing: {cmd}")
        os.system(cmd)


def main():
    parser = argparse.ArgumentParser(description="LoDeSS Calibration")
    # For now, only obsid is supported. Maybe different in future
    parser.add_argument("obsid", type=str,
                        help="Observation ID")
    parser.add_argument("--testing", help=argparse.SUPPRESS,
                        action="store_true", default=False)
    res = parser.parse_args()

    res = vars(res)

    os.mkdir(res["obsid"])
    os.chdir(res["obsid"])
    cmd_staging = f'LOFAR_stager.py -o {res["obsid"]} -c --nobug'
    call(cmd_staging, res["testing"])

    # move file from TODO to INPROG
    sshcmd = 'mv /iranet/groups/ulu/c.groeneveld/LoDeSS_cal/PROGRESS/TODO/' + res["obsid"] + ' /iranet/groups/ulu/c.groeneveld/LoDeSS_cal/PROGRESS/INPROG/'
    cmd = f'ssh c.groeneveld@gaia.ira.inaf.it "{sshcmd}"'
    call(cmd, res["testing"])
    # Check if the staging is not affected by the bug
    if not res["testing"]:
        nfiles = glob.glob('*')
        if len(nfiles) < 2:
            print("Staging failed - probably due to the correlator bug.")
            sys.exit(1)

    # Make a LiLF.conf for the demix
    conf_file = "LiLF.conf"
    with open(conf_file, "w") as f:
        f.write("[LOFAR_preprocess]\n")
        f.write("demix_sources = [CasA,CygA]\n")

    # Run preprocesser

    cmd = 'LOFAR_preprocess.py'
    call(cmd, res["testing"])

    # run LOFAR_cal in directory
    if res["testing"]:
        os.mkdir('mss')
    os.chdir('mss')
    ids = glob.glob(f'id{res["obsid"]}*')
    os.chdir(ids[0])
    os.mkdir('data-bkp')
    cmd = 'mv * data-bkp'
    call(cmd, res["testing"])

    # Enable imaging in the LOFAR_cal pipeline
    conf_file = 'LiLF.conf'
    with open(conf_file, "a") as f:
        f.write("\n[LOFAR_cal]\n")
        f.write("imaging = True\n")

    cmd = 'LOFAR_cal.py'
    call(cmd, res["testing"])

    # done
    os.system('rm -rf data-bkp')
    os.chdir('../../../')
    os.system(f'tar cf {res["obsid"]}.tar {res["obsid"]}')
    # Check if the node is the IRA node by checking if path exists
    if os.path.exists('/iranet/groups/ulu/c.groeneveld/'):
        cmd = f'mv {res["obsid"]}.tar /iranet/groups/ulu/c.groeneveld/'
        call(cmd, res["testing"])
    else:
        cmd = f'scp {res["obsid"]}.tar c.groeneveld@gaia.ira.inaf.it:/iranet/groups/ulu/c.groeneveld/LoDeSS_cal/archive'
        call(cmd, res["testing"])
    os.system(f'rm -rf {res["obsid"]}')
    
    # remove inprog file
    sshcmd = 'rm /iranet/groups/ulu/c.groeneveld/LoDeSS_cal/PROGRESS/INPROG/' + res["obsid"]
    cmd = f'ssh c.groeneveld@gaia.ira.inaf.it "{sshcmd}"'
    call(cmd, res["testing"])


if __name__ == "__main__":
    main()
