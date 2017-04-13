# a119_join
Viofo A119 dashcam tool to join video files, create timelapses and extract GPS data as GPX

The camera creates a file every few minutes (depending on its settings). This tool groups the files by the time passed between recordings (if less than 10 minutes passed between two files, they are put in the same group). The groups can be listed using the -list parameter.

The video and GPX commands use the group id for group selection (-g). Day selection (-d) uses the group ID to select the day (all the groups in the same day as the given one). 

The GPS data extraction uses Sergei's GPX extractor tool (http://sergei.nz/extracting-gps-data-from-viofo-a119-and-other-novatek-powered-cameras/), with a few changes. 

## Setup

The scripts uses ffmpeg for video manipulation. If it's not in PATH then the full path should be provided in the script (the ffmpeg= variable). This is not needed for GPS extraction.

## Command line

The full path to the Movie folder on the SD card must be provided as IN_PATH. OUT_PATH is the output path (always requred).
If the group is not given, the operation is applied to all the groups. Group selection can also use Python's list indexing, so group -1 means the last group.

If the -d parameter is given, all the files in the same day as the given group are selected.

If the output file exists (video or GPX file), it will not be overwritten.

### List all the recorded files as groups

    python a119_join.py -list IN_PATH OUT_PATH

sample

    python a119_join.py -list  f:\DCIM\Movie

### Extract GPS data

    python a119_join.py -gps IN_PATH OUT_PATH
  
For all the groups (safe, as it only writes the file if it doesn't exist)
  
    python a119_join.py -gps f:\DCIM\Movie d:\
    
For a specific group
    
    python a119_join.py -gps -g 2 f:\DCIM\Movie d:\
        
This command does not support the day parameter yet      
  
### Join video files

    python a119_join.py -join -g GROUP_ID IN_PATH OUT_PATH
  
sample
  
    python a119_join.py -join -g 3 f:\DCIM\Movie d:\
    
For a specific day
    
    python a119_join.py -join -g 3 -d f:\DCIM\Movie d:\

### Join video files as timelapse (8x)

    python a119_join.py -tl -g GROUP_ID IN_PATH OUT_PATH
  
sample
  
    python a119_join.py -tl -g 3 f:\DCIM\Movie d:\
    
For a specific day
    
    python a119_join.py -tl -g 3 -d f:\DCIM\Movie d:\
    
There are two timelapse options, with or without sound, in the code, but they have to be manually switched    