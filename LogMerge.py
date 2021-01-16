#! /usr/bin/env python
# coding:utf-8

# =============================================================================
# Function: LogMerge
# Author  : Liu Gefeng
# Comment : merge sys and main log from MTK
# Note    : 1 merge MTK main/sys/radio log
#         : 2 support python version 3.x
# History : 2019-11-02 finished develop
# =============================================================================

import sys
import os
import codecs
import re
import datetime
import time

# =============================================================================
# Function : regexp 
# Author   : Liu Gefeng
# Date     : 2020-12-18 17:36
# Comment  : regular expression
# Parameter: str: 
# Note     :
# =============================================================================
def regexp(str, regstr, ignore_case = False):
    flags = 0
    if not ignore_case:
        flags |= re.I

    match = re.search(regstr, str, flags)
    if match:
        return match

    return None

# =============================================================================
# Function : getTimeFromLine
# Author   : Liu Gefeng
# Date     : 2021-01-15 22:22
# Comment  : get time info from specified line
# Parameter: 
# Note     :
# =============================================================================
def getTimeFromLine(line_text):
    # 10-18 09:19:55.061396  1037  1122 E ViewRootImpl:     at com.android.server.ServiceThread.run(ServiceThread.java:44)
    result = regexp(line_text, r'^\s*(\d+\-\d+\s+\d{2}:\d{2}:\d{2}\.\d+)\s+.*$')
    if result:
        return result.group(1)
    else:
        return ""

# =============================================================================
# Class    : LineInfo
# Author   : Liu Gefeng
# Date     : 2021-01-15 22:22
# Comment  : line info class
# Parameter: file_index: specified file index in list to be merged
#          : line_no: line no
# Note     :
# =============================================================================
class LineInfo:
    def __init__(self, file_index, line_no):
        self.file_index = file_index
        self.line_no = line_no

# =============================================================================
# Class    : TimeInfo
# Author   : Liu Gefeng
# Date     : 2021-01-15 22:22
# Comment  : time info
# Parameter: timestr time string from line text
#          : lst_lines to store lines at current time
# Note     :
# =============================================================================
class TimeInfo:
    def __init__(self, timestr):
        self.timestr = timestr
        self.lst_lines = []

    def add_line_info(self, line_info):
        if not line_info:
            return

        self.lst_lines.append(line_info)

# =============================================================================
# Function : get_line_info_from_file
# Author   : Liu Gefeng
# Date     : 2021-01-15 22:22
# Comment  : get line info from specified log file 
# Parameter: lst_files: log file list
#          : file_index: file index from log file list
#          : lst_timeinfo: time info list
#          : map_timeinfo: time info map
# Note     :
# =============================================================================
def get_line_info_from_file(lst_files, file_index, lst_timeinfo, map_timeinfo):
    log_file = lst_files[file_index]
    if not os.path.exists(log_file):
        print("file " + log_file + " not exist!")
        return

    print("scanning file %s ..." % log_file)

    lst_no_time = []
    timeinfo = None
    line_no = 1
    line_text = ""
    fd = open(log_file, encoding='utf-8', errors='ignore')
    line_text = fd.readline()

    while line_text:
        timestr = getTimeFromLine(line_text)

        # time not included in current line
        if not timestr:
            line_info = LineInfo(file_index, line_no)
            lst_no_time.append(line_info)
        else:
            # current time not exists in map
            if not timestr in map_timeinfo.keys():
                timeinfo = TimeInfo(timestr)
                lst_timeinfo.append(timestr)
                map_timeinfo[timestr] = timeinfo
            else:
                timeinfo = map_timeinfo[timestr]

            for item in lst_no_time:
                timeinfo.add_line_info(item)

            lst_no_time = []
            line_info = LineInfo(file_index, line_no)
            timeinfo.add_line_info(line_info)

        # get next line text
        line_text = fd.readline()
        line_no = line_no + 1

    fd.close()

# =============================================================================
# Function : get_files_by_dir
# Author   : Liu Gefeng
# Date     : 2021-01-15 22:22
# Comment  : get files under specified directory (not recursive)
# Parameter: dir: from which the function get files
#          : lst_files: log file list
# Note     :
# =============================================================================
def get_files_by_dir(dir, lst_files):
    # if path exists
    if not os.path.exists(dir):
        print("path " + dir + " not exist!")
        return

    # add files
    if os.path.isfile(dir):
        if dir.startswith("."):
            return

        lst_files.append(dir)
        return

    # add files and recursive find files for subdir
    lst_items = os.listdir(dir)
    for item in lst_items:
        if item.startswith("."):
            continue

        if not dir.endswith("/"):
            dir += "/"
        item = dir + item

        if os.path.isfile(item):
            lst_files.append(item)

if __name__ == '__main__':
    num = len(sys.argv)

    if num < 2:
        print("not log file specified.")
        sys.exit()

    # remove result file already exists
    result_file = "main_log_merge"
    if os.path.exists(result_file):
        print("rm " + result_file)
        os.system("rm " + result_file)

    # get files to be merged from Parameters
    lst_files = []
    for item in sys.argv[1:]:
        item = item.strip()

        # current item is file
        if os.path.isfile(item):
            if not item in lst_files:
                lst_files.append(item)
            else:
                print("file %s already exists!" % item)

            continue

        # current item is match string
        elif item.endswith("*"):
            result = regexp(item, r'(.+/)?([^/]+)\*$')
            if result:
                file_path = result.group(1)
                if not file_path:
                    file_path = "./"

                file_match = result.group(2)
                lst_match_files = []
                get_files_by_dir(file_path, lst_match_files)
                for sub_item in lst_match_files:
                    sub_result = regexp(sub_item, r'.*/' + file_match + r'[^/]*$')
                    if sub_result:
                        if not sub_item in lst_files:
                            lst_files.append(sub_item)
            else:
                print("error format for item1 %s." % item)
            continue
        else:
            print("error format item2: %s." % item)

    if len(lst_files) < 2:
        print("log file to be merge is < 2, merge canceled.")
        sys.exit()
    else:
        print("merge file: %s." % ", ".join(lst_files))

    map_timeinfo = {}
    lst_timeinfo = []

    for file_index in range(len(lst_files)):
        get_line_info_from_file(lst_files, file_index, lst_timeinfo, map_timeinfo)

    # sort scan result
    print("\nsorting lines by time ...")
    lst_timeinfo.sort()

    lst_fd = []
    for item in lst_files:
        fd = open(item, encoding='utf-8', errors='ignore')
        lst_fd.append(fd)

    print("sorting lines end.\n")

    # generate merge file
    print("generating merge file ...")
    wfd = open("main_log_merge", 'w', errors='ignore')
    for item in lst_timeinfo:
        if not item in map_timeinfo.keys():
            print("time " + item + " not found!")
            continue

        timeinfo = map_timeinfo[item]
        if not timeinfo:
            continue

        lst_lines = timeinfo.lst_lines
        for line_info in lst_lines:
            line_text = lst_fd[line_info.file_index].readline()
            wfd.write(line_text)

    print("merge file generated.")
    wfd.close()

    for item in lst_fd:
        item.close()

