import os
import sys
import glob
import time
import argparse
import random
import numpy as np


def main():

    parser = argparse.ArgumentParser(
        description="Iterate through all the pointings for the cal/target for LoDeSS")
    parser.add_argument(
        "mode", type=str, help="Mode of operation: 'cal' or 'target'", choices=['cal', 'target'])
    parser.add_argument("--lodess_path", type=str, default=os.path.join(
        os.path.dirname(__file__), '..', 'lodess'), help="Path to the LoDeSS directory")
    parser.add_argument("--username", type=str,
                        default='c.groeneveld', help="Username for SSH connection")
    res = parser.parse_args()

    if res.mode == 'target':
        print("Target not yet implemented")
        sys.exit(1)
    elif res.mode == 'cal':
        while True:
            print("Running calibration mode")
            location_on_iranet = '/iranet/groups/ulu/c.groeneveld/LoDeSS_cal/PROGRESS/TODO/'
            cmd = f'ssh {res.username}@gaia.ira.inaf.it ls {location_on_iranet}'
            todos = os.popen(cmd).read().strip().split('\n')

            # pull a random obsid from the list
            random_obsid = np.random.choice(todos)
            print(random_obsid)

            # Copy LoDeSS_cal before importing core
            sys.path.append(res.lodess_path)
            from LoDeSS_cal import core
            res = {}
            res["obsid"] = random_obsid
            res["testing"] = False  # Set to True for testing mode
            core(res)  # main run

            # check if STOP file exists
            if os.path.exists('STOP'):
                print("STOP file found, exiting.")
                sys.exit(0)


if __name__ == "__main__":
    main()
