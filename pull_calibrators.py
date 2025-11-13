import sys,glob,os
import argparse

'''
    Convenience script to allow access to the public calibrator surfdrive
'''


def download_file_from_surf(filename):
    # Download a file from the SURFdrive archive
    url = f'https://surfdrive.surf.nl/index.php/s/F34o4kCVMvpcb06/download?path=%2F&files={filename}'
    url = f'https://surfdrive.surf.nl/remote.php/dav/files/groeneveldc%40leidenuniv.nl/LoDeSS_calibrators/{filename}'
    url = f'https://surfdrive.surf.nl/public.php/dav/files/fenDYKZ2RPekCT3/{filename}'
    os.system(f'wget -O {filename} "{url}"')

def main():
    parser = argparse.ArgumentParser(description="Pull calibrated calibrator data from archive.")
    parser.add_argument('pointing_name', type=str, help='Name of the pointing to process. Name should be like PXXX+XX')
    args = parser.parse_args()
    if not os.path.exists('obsidlist.txt'):
        download_file_from_surf('obsidlist.txt')

    # Read the obsidlist.txt file
    with open('obsidlist.txt', 'r') as f:
        obsidlist = f.readlines()
    obsid_dict = {}
    for line in obsidlist:
        line = line.strip()
        if not line:
            continue
        obsid, targets = line.split(maxsplit=1)
        obsid_dict[obsid] = targets.split(',') # Format: OBSID: target1,target2,...
        # OBSID is observationID, calibrators are in the archive under their observationID
        # target1,target2,... are the names of the fields

    # Find the obsids that contain the specified pointing
    obsids = []
    for obsid, targets in obsid_dict.items():
        if args.pointing_name in targets:
            obsids.append(obsid)

    # Download the calibrated data for each obsid
    for obsid in obsids:
        filename = f'{obsid}.tar.gz'
        print(f'Downloading {filename}...')
        download_file_from_surf(filename)
        print(f'Extracting {filename}...')
        os.system(f'tar -xzf {filename}')
        os.remove(filename)




if __name__ == "__main__":
    main()
