#!/usr/bin/env python
#
# Author: Sergei Franco (sergei at sergei.nz)
# License: GPL3 
# Warranty: NONE! Use at your own risk!
# Disclaimer: I am no programmer!
# Description: this script will crudely extract embedded GPS data from Novatek generated MP4 files.
#

import struct


def fix_time(hour, minute, second, year, month, day):
    return "%d-%02d-%02dT%02d:%02d:%02dZ" % ((year + 2000), int(month), int(day), int(hour), int(minute), int(second))


def fix_coordinates(hemisphere, coordinate):
    # Novatek stores coordinates in odd DDDmm.mmmm format
    minutes = coordinate % 100.0
    degrees = coordinate - minutes
    coordinate = degrees / 100.0 + (minutes / 60.0)
    if hemisphere == 'S' or hemisphere == 'W':
        return -1 * float(coordinate)
    else:
        return float(coordinate)


def fix_speed(speed):
    # 1 knot = 0.514444 m/s
    return speed * float(0.514444)


def get_atom_info(eight_bytes):
    try:
        atom_size, atom_type = struct.unpack('>I4s', eight_bytes)
    except struct.error:
        return 0, ''
    return int(atom_size), atom_type


def get_gps_atom_info(eight_bytes):
    atom_pos, atom_size = struct.unpack('>II', eight_bytes)
    return int(atom_pos), int(atom_size)


def get_gps_atom(gps_atom_info, f):
    atom_pos, atom_size = gps_atom_info
    if atom_size > 100000:
        print("Error! Atom too big!")
        return
    f.seek(atom_pos)
    data = f.read(atom_size)
    expected_type = 'free'
    expected_magic = 'GPS '
    try:
        atom_size1, atom_type, magic = struct.unpack_from('>I4s4s', data)

        # sanity:
        if atom_size != atom_size1 or atom_type != expected_type or magic != expected_magic:
            print(
            "Error! skipping atom at %x (expected size:%d, actual size:%d, expected type:%s, actual type:%s, expected magic:%s, actual maigc:%s)!" % (
            int(atom_pos), atom_size, atom_size1, expected_type, atom_type, expected_magic, magic))
            return

        hour, minute, second, year, month, day, active, latitude_b, longitude_b, unknown2, latitude, longitude, speed = struct.unpack_from(
            '<IIIIIIssssfff', data, 48)

        time = fix_time(hour, minute, second, year, month, day)
        latitude = fix_coordinates(latitude_b, latitude)
        longitude = fix_coordinates(longitude_b, longitude)
        speed = fix_speed(speed)

        # it seems that A indicate reception
        if active != 'A':
            # print("Skipping: lost GPS satelite reception. Time: %s." % time)
            return
    except struct.error:
        return

    return (latitude, longitude, time, speed)


def get_gpx(gps_data, in_file, out_file=''):
    gpx = '<?xml version="1.0" encoding="UTF-8"?>\n'
    gpx += '<gpx version="1.0"\n'
    gpx += '\tcreator="Sergei\'s Novatek MP4 GPS parser"\n'
    gpx += '\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
    gpx += '\txmlns="http://www.topografix.com/GPX/1/0"\n'
    gpx += '\txsi:schemaLocation="http://www.topografix.com/GPX/1/0 http://www.topografix.com/GPX/1/0/gpx.xsd">\n'
    gpx += "\t<name>%s</name>\n" % in_file
    gpx += '\t<url>sergei.nz</url>\n'
    gpx += "\t<trk><name>%s</name><trkseg>\n" % out_file
    for l in gps_data:
        if l:
            gpx += "\t\t<trkpt lat=\"%f\" lon=\"%f\"><time>%s</time><speed>%f</speed></trkpt>\n" % l
    gpx += '\t</trkseg></trk>\n'
    gpx += '</gpx>\n'
    return gpx


def extract_gpx(in_file, header=False):
    gps_data = []
    with open(in_file, "rb") as f:
        offset = 0

        while True:
            atom_pos = f.tell()
            atom_size, atom_type = get_atom_info(f.read(8))
            if atom_size == 0:
                break

            if atom_type == 'moov':
                # print("Found moov atom...")
                sub_offset = offset + 8

                while sub_offset < (offset + atom_size):
                    sub_atom_pos = f.tell()
                    sub_atom_size, sub_atom_type = get_atom_info(f.read(8))

                    if sub_atom_type == 'gps ':
                        # print("Found gps chunk descriptor atom...")
                        gps_offset = 16 + sub_offset  # +16 = skip headers
                        f.seek(gps_offset, 0)
                        while gps_offset < (sub_offset + sub_atom_size):
                            gps_data.append(get_gps_atom(get_gps_atom_info(f.read(8)), f))
                            gps_offset += 8
                            f.seek(gps_offset, 0)

                    sub_offset += sub_atom_size
                    f.seek(sub_offset, 0)

            offset += atom_size
            f.seek(offset, 0)
    if header:
        get_gpx(gps_data, in_file)
    return gps_data

#
# gpx=get_gpx(gps_data,in_file,out_file)
