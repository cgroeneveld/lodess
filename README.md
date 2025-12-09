# LoDeSS
LOFAR Decameter Sky Survey

## Checklist
1. Build a container for your machine. For this, you need to pick either the AMD or Intel container, and use the right settings for march/mtune
2. Configure LoDeSSdb.py with your Leiden username and the location of your .my.conf file (ask me if you need one)
3. Open the apptainer image
4. run `ulimit -n 8000`
5. add the LiLF/ directory to your $PYTHONPATH
6. add the LiLF/scripts and LiLF/pipelines to your $PATH
7. add the lodess/ directory to your $PATH
8. Make sure that you have enough space on your disk (around 1.5 TB should be fine, data is compressed afterwards and uploaded)
9. Run `python LoDeSSdb.py test-connection` to verify if rclone/mysql connection is up
10. Run `python iterator_target.py -c`
