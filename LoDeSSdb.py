#! /usr/bin/env python

import os,sys,glob,pickle
import numpy as np
import argparse
import ftplib
import warnings
warnings.filterwarnings(action='ignore', module='paramiko')
warnings.filterwarnings(action='ignore', module='cryptography')

from sshtunnel import SSHTunnelForwarder
import pymysql

home = os.environ['HOME']

'''
 === How to run ===
This pipeline builds on LiLF. However, since we are using a different setup, we made a few
different choices. Firstly, you need to Leiden Observatory account, for that contact me
(c.groeneveld@ira.inaf.it) and I will tell you more. Then, you need to add your ssh public
key to the ~/.ssh/authorized_keys/ file on the home disk of the Leiden Observatory.

After that, you need an account for the mysql server, for that you need to send me an email.
I will then provide a .my.cnf file that you need to put in the home folder (see the 
DEFAULT_FILE_PYMYSQL variable).

Finally, make sure you have your StageIt API token stored in your ~/.staginrc . Note that we
now use a different stager, so your old username/password combo does not work anymore!!

'''

# 
# === EDIT THESE LINES ===
#

USERNAME = 'groeneveld' # username for leiden observatory intranet
DEFAULT_FILE_PYMYSQL = home+'/.my.cnf'
MACHINE = 'LOFAR15'
HOSTNAME = 'IRA'

#
# ==========
#

def download_file_from_surf(filename):
    # Download a file from the SURFdrive archive
    url = f'https://surfdrive.surf.nl/public.php/dav/files/fenDYKZ2RPekCT3/{filename}'
    os.system(f'wget -O {filename} "{url}"')

sshtunnel_dict = {
    'remote_bind_address': ('127.0.0.1', 3306),
    'local_bind_address': ('127.0.0.1', 3306),
    'ssh_username': USERNAME,
    'ssh_pkey': '~/.ssh/id_rsa',
}

def runcmd(cmd):
    conn = pymysql.connect(
        read_default_file=DEFAULT_FILE_PYMYSQL,
        database='lodess'
    )
    with conn.cursor() as cur:
        cur.execute(cmd)
        conn.commit()
        output = cur.fetchall()
    conn.close()
    return output



def main(args):
    with SSHTunnelForwarder(
        ('hoendiep.strw.leidenuniv.nl', 22),
        **sshtunnel_dict
    ) as tunnel:
        if args.command == 'test-connection':
            allsuccess = True
            out = runcmd("SELECT now()")[0][0] # This should otherwise crash 
            print(f"Connection to database successful, server time: {out}")
            test2 = os.system(f"rclone --config={DEFAULT_FILE_PYMYSQL} ls gdrivelodess:/")
            if test2 == 0:
                print('Successful connection with rclone')
            else:
                print("Rclone failed")
                allsuccess = False
            download_file_from_surf('obsidlist.txt')
            if os.path.exists('obsidlist.txt'):
                print("Calibrator host is avail")
                os.system('rm -rf obsidlist.txt')
            else:
                allsuccess = False
                print("ERROR: calibrator host down")
            if allsuccess:
                print("ALL TESTS OK")
        if args.command == 'inprog':
            # set field status to INPROG
            cmd = f"UPDATE fields SET status='INPROG' WHERE id='{args.field}';"
            runcmd(cmd)
            runcmd(f"UPDATE fields SET start_date=NOW() WHERE id='{args.field}';")
            runcmd(f"UPDATE fields SET username='{USERNAME}' WHERE id='{args.field}';")
            runcmd(f"UPDATE fields SET clustername='{HOSTNAME}' WHERE id='{args.field}';")
            runcmd(f"UPDATE fields SET nodename='{MACHINE}' WHERE id='{args.field}';")
            print(f"Field {args.field} set to INPROG")
        if args.command == 'todo':
            # set field status to TODO
            cmd = f"UPDATE fields SET status='TODO' WHERE id='{args.field}';"
            runcmd(cmd)
            print(f"Field {args.field} set to TODO")
        if args.command == 'finished':
            # set field status to FINISHED
            cmd = f"UPDATE fields SET status='FINISHED' WHERE id='{args.field}';"
            runcmd(cmd)
            print(f"Field {args.field} set to FINISHED")
            # here be some code for quality control. maybe separate? maybe not.
            with open('DD/quality/quality.pickle','rb') as handle:
                quality = pickle.load(handle)

            runcmd(f"UPDATE fields SET noise={quality['ddserial_c0_rms']} WHERE id='{args.field}';")
            runcmd(f"UPDATE fields SET nvss_ratio={quality['nvss_ratio']} WHERE id='{args.field}';")
            runcmd(f"UPDATE fields SET nvss_match={quality['nvss_match']} WHERE id='{args.field}';")
            runcmd(f"UPDATE fields SET flag_frac={quality['flag_frac']} WHERE id='{args.field}';")
            runcmd(f"UPDATE fields SET end_date=NOW() WHERE id='{args.field}';")

        if args.command == 'error':
            # set field status to ERROR
            cmd = f"UPDATE fields SET status='ERROR' WHERE id='{args.field}';"
            runcmd(cmd)
            print(f"Field {args.field} set to ERROR")
        if args.command == 'pullrandom':
            # pull random field with status TODO
            # First pull fields with priority 0, then 1, etc. and lastly NULL
            for priority in [0,1,2,3,4,5,'NULL']:
                if priority == 'NULL':
                    cmd = f"SELECT id FROM fields WHERE status='TODO' AND priority IS NULL ORDER BY RAND() LIMIT 1;"
                else:
                    cmd = f"SELECT id FROM fields WHERE status='TODO' AND priority={priority} ORDER BY RAND() LIMIT 1;"
                result = runcmd(cmd)
                if result:
                    field_id = result[0][0]
                    print(f"Random TODO field with priority {priority}: {field_id}")
                    break
        if args.command == 'upload':
            # ok different
            # Things to copy: ddparallel images, ddparallel logs, ddparallel solutions
            # ddserial imges, ddserial logs, ddserial solutions
            # msfiles
            # run this in mss folder (not in DD folder!)
            abspath = os.path.abspath(args.path)
            os.mkdir(args.field)
            os.chdir(args.field)
            os.system(f'cp -r {abspath}/mss-avg .')
            os.mkdir('ddserial')
            os.chdir('ddserial')
            os.system(f'cp -r {abspath}/ddserial/c00/images .')
            os.system(f'cp -r {abspath}/ddserial/c00/solutions/interp.h5 ddserial.h5')
            os.system(f'cp -r {abspath}/ddserial/c00/solutions/facetsS-c0.reg .')
            os.system(f'cp -r {abspath}/ddserial/c00/skymodel/ddcals-c0.reg .')
            os.chdir('..')
            os.mkdir('ddparallel')
            os.chdir('ddparallel')
            os.system(f'cp -r {abspath}/ddparallel/images .')
            os.system(f'cp -r {abspath}/ddparallel/solutions/ .')

            os.chdir('..')
            os.system(f'cp -r {abspath}/quality .')
            os.system(f'cp -r {abspath}/pipeline-ddparallel.logger .')
            os.system(f'cp -r {abspath}/pipeline-ddserial.logger .')
            os.system(f'cp -r {abspath}/pipeline-quality.logger .')
            os.chdir('..')
            os.system(f'cp -r {abspath}/ddserial/c00/images/wideDDS-c0-MFS-image-pb.fits {args.field}.fits')
            os.system(f'tar -cf {args.field}.tar {args.field}')
            print("Compressing...")
            os.system(f'pigz {args.field}.tar')

            # Connect to FTP and upload
            os.system(f'rclone --config={DEFAULT_FILE_PYMYSQL} copy {args.field}.tar.gz gdrivelodess:{args.field}.tar.gz -P')
            os.system(f'rclone --config={DEFAULT_FILE_PYMYSQL} copy {args.field}.fits gdrivelodess:{args.field}.fits -P')
            print(f"Uploaded data for field {args.field} to the google drive.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Interact with LoDeSS database")
    subparsers = parser.add_subparsers(dest='command')
    # Subcommands: test-connection , todo, inprog, finished, error, upload, pullrandom
    testconap = subparsers.add_parser('test-connection', help='Test database connection')
    todoap = subparsers.add_parser('todo', help='List todo entries')
    inprogap = subparsers.add_parser('inprog', help='List in-progress entries')
    finishedap = subparsers.add_parser('finished', help='List finished entries')
    errorap = subparsers.add_parser('error', help='List error entries')
    uploadap = subparsers.add_parser('upload', help='Upload entries')
    pullrandomap = subparsers.add_parser('pullrandom', help='Pull random entries')

    todoap.add_argument('field', type=str, help='Field to mark as TODO')
    inprogap.add_argument('field', type=str, help='Field to mark as IN-PROGRESS')
    finishedap.add_argument('field', type=str, help='Field to mark as FINISHED')
    errorap.add_argument('field', type=str, help='Field to mark as ERROR')
    uploadap.add_argument('field', type=str, help='Field to upload')
    uploadap.add_argument('--path','-p', type=str, default='./DD', help='Path to folder with DD data')

    args = parser.parse_args()
    main(args)
