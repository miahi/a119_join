import argparse
import subprocess
import tempfile
import sys
from os import listdir
from os.path import isfile, join, isdir

from datetime import datetime

import nvtk_mp42gpx

# Path to ffmpeg executable, used for joining video files and timelapses. Not needed for GPX extraction
# Change to the full path if not in $PATH
ffmpeg = "ffmpeg"


class VideoFile:

    def __init__(self, mp4, folder):
        self.mp4fileonly = mp4
        self.mp4file = join(folder, mp4)
        # first 16 chars in filename are the date and time 2016_1224_094105_116.MP4
        self.date = datetime.strptime(mp4[:16], '%Y_%m%d_%H%M%S')
        self.number = mp4[16:2]
        self.gpx = []

    def str_date(self):
        return str(self.date)

    def __str__(self):
        return self.mp4file + self.str_date() + (' gps ' + str(len(self.gpx)) if len(self.gpx) > 0 else '')

    def read_gps(self):
        if not self.gpx:
            self.gpx = nvtk_mp42gpx.extract_gpx(self.mp4file)
        return self.gpx


def print_group(i, gr):
    print 'Group %s [%d files]: %s \tTO %s \t(%d min)\t' % (i, len(gr), gr[0].str_date(), gr[-1].str_date(), (gr[-1].date - gr[0].date).total_seconds() / 60, )


# read gps data, filtering the unusable data
def read_group_gps(gr):
    full_gpx = []
    for fi in gr:
        full_gpx = full_gpx + fi.read_gps()
    return filter(None, full_gpx)


def extract_day_group(groups, target_date):
    res = []
    for g in groups:
        check_date = g[0].date
        if check_date.year == target_date.year and check_date.month == target_date.month and check_date.day == target_date.day:
            res += g
    return res


def init_parser():
    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-list", action="store_true", help="List the found groups in the input dir")
    group.add_argument("-gps", action="store_true", help="Extract GPS data to GPX files")
    group.add_argument("-join", action="store_true", help="Join the video files")
    group.add_argument("-tl", "--timelapse", action="store_true", help="Join the video files in 8x timelapse")

    parser.add_argument('input', help='Input dir', action="store")
    parser.add_argument('out', help='Output dir', action="store")

    parser.add_argument('-g', type=int, help='Select only this group to process')
    parser.add_argument('-d', action="store_true", help='Process all video from this day (select a group)')

    parser.print_help()
    return parser


def main():
    parser = init_parser()

    args = parser.parse_args()

    mypath = args.input
    mypath_ro = join(mypath, 'RO')
    groups = [[]]
    group = groups[0]

    dirfiles = [VideoFile(f, mypath) for f in listdir(mypath) if isfile(join(mypath, f)) and f.endswith('MP4')]
    rofiles = []
    if isdir(mypath_ro):
        rofiles = [VideoFile(f, mypath_ro) for f in listdir(mypath_ro) if isfile(join(mypath_ro, f)) and f.endswith('MP4')]

    allfiles = dirfiles + rofiles
    allfiles.sort(key=lambda x: x.date, reverse=False)

    # grouping
    last = allfiles[0]
    for f in allfiles:
        if last:
            if (f.date - last.date).total_seconds() > 610:
                # print ('--- cut here ---')
                group = []
                groups.append(group)

        group.append(f)
        last = f

    # List groups
    if args.list:
        for i, g in enumerate(groups):
            print_group(i, g)

    # Extract GPS data
    if args.gps:
        selected_index = []
        if args.g:
            selected_index = [args.g]
        else:
            selected_index = range(0, len(groups))

        if args.d:
            # todo: implement
            print "Day selection is not supported yet."
            return

        for i in selected_index:
            selected_group = groups[i]

            group_gpx = read_group_gps(selected_group)

            print str(len(group_gpx)) + " GPS points found"
            if len(group_gpx) > 0 :
                gpx_file_content = nvtk_mp42gpx.get_gpx(group_gpx, selected_group[0])

                out_file = join(args.out, selected_group[0].mp4fileonly + '.gpx')

                if isfile(out_file):
                    print "File %s already exists" % (out_file,)
                else:
                    with open(out_file, "w") as gpx_file:
                        print("Writing '%s'" % out_file)
                        gpx_file.write(gpx_file_content)

    # Join files
    if args.join:
        if args.g:
            group = groups[args.g]
            if args.d:
                group = extract_day_group(groups, group[0].date)
                out_file = join(args.out, 'DAY_' + group[0].mp4fileonly + '_join.mp4')
            else:
                out_file = join(args.out, group[0].mp4fileonly + '_join.mp4')

            if isfile(out_file):
                print "File %s already exists" % (out_file,)
            else:
                with tempfile.NamedTemporaryFile(delete=False) as ffmpeg_filelist:
                    print ffmpeg_filelist.name
                    for g in group:
                        ffmpeg_filelist.write('file \'%s\'\r\n' % (g.mp4file,))
                    ffmpeg_filelist.flush()

                # ffmpeg -safe 0 -f concat -i 3.txt  -c copy 3.mp4
                command = '%s -y -safe 0 -f concat -i %s -c copy  %s' % (
                    ffmpeg, ffmpeg_filelist.name, out_file,)

                print command
                subprocess.call(command, shell=True)

    # Join files in 8x timelapse
    if args.timelapse:
        if args.g:
            group = groups[args.g]
            if args.d:
                group = extract_day_group(groups, group[0].date)
                out_file = join(args.out, 'DAY_' + group[0].mp4fileonly + '_10x.mp4')
            else:
                out_file = join(args.out, group[0].mp4fileonly + '_10x.mp4')

            if isfile(out_file):
                print "File %s already exists" % (out_file,)
            else:
                with tempfile.NamedTemporaryFile(delete=False) as ffmpeg_filelist:
                    for g in group:
                        ffmpeg_filelist.write('file \'%s\'\r\n' % (g.mp4file,))
                    ffmpeg_filelist.flush()

                # timelapse 8x with sound
                command = '%s -y -safe 0 -f concat -i %s -filter:v \"setpts=PTS/8\" -filter:a "atempo=2.0,atempo=2.0,atempo=2.0" -c:a libmp3lame -q:a 4 -threads 10 %s' % (ffmpeg, ffmpeg_filelist.name, out_file,)

                # timelapse 8x without sound
                # command = '%s -y -safe 0 -f concat -i %s -filter:v \"setpts=PTS/8\" -an -threads 8 %s' % (ffmpeg, ffmpeg_filelist.name, out_file,)

                print 'Running ' + command

                child = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE)
                processing = -1
                line = ''
                start_time = datetime.now()
                print start_time

                # Monitors ffmpeg and tries to calculate the speed
                while True:
                    out = child.stderr.read(1)
                    if out == '' and not child.poll() is None:
                        print 'Finished ' + str(datetime.now())
                        break
                    if out != '':
                        line += out
                        if '\n' == out:
                            if 'Auto-inserting' in line:
                                processing += 1
                                current_time = datetime.now()
                                second = (current_time - start_time).total_seconds()
                                if processing > 0:
                                    estimate = (len(group) - processing) * second / processing
                                else:
                                    # estimation based on quad i7
                                    estimate = 40*len(group)
                                minutes = estimate/60

                                print 'Processing %s (%d%% done, %d minutes left)' %(group[processing], processing*100/len(group), minutes)
                            else:
                                # debug
                                # sys.stdout.write(line)
                                sys.stdout.flush()
                            line = ''


if __name__ == "__main__":
    main()
