#! /usr/bin/env python
# coding:utf-8

# =============================================================================
# Function: 按时间先后顺序，合并Log文件
# Author  : Liu Gefeng
# Comment : 考虑到log文件可能上G的情况，为了保证脚本的通用性，没有将log文件一次性读到内存中进行处理
# Note    : 1、该脚本文件目前只在mtk平台上进行了调试
#         : 2、脚本只能在python3.3+上测试， python 2.7尚不兼容
# History : 2019-11-02 初步完成开发
# =============================================================================

import sys
import os
import codecs
import re
import datetime
import time

# 根据log文件中的单行内容获取时间戳
def getTimeFromLine(line_text):
    # 10-18 09:19:55.061396  1037  1122 E ViewRootImpl:     at com.android.server.ServiceThread.run(ServiceThread.java:44)
    pat_log = re.compile(r'^\s*(\d+\-\d+\s+\d{2}:\d{2}:\d{2}\.\d+)\s+.*$')
    result = pat_log.search(line_text)
    if result:
        return result.group(1)
    else:
        return ""

# 标记单行所在的文件索引(文件在脚本调用参数的文件列表中的位置)以及该行在文件中的行号
class LineInfo:
    def __init__(self, file_index, line_no):
        self.file_index = file_index
        self.line_no = line_no

# 包含相同时间戳的行
# Note: 对于没有时间戳的行，其时间默认为与后面紧连的时间相同
class TimeInfo:
    def __init__(self, timestr):
        self.timestr = timestr
        self.lst_lines = []

    # 添加时间相同行(可能来自不同文件)
    def add_line_info(self, line_info):
        if not line_info:
            return

        self.lst_lines.append(line_info)

def get_line_info_from_file(lst_files, file_index, lst_timeinfo, map_timeinfo):
    log_file = lst_files[file_index]
    if not os.path.exists(log_file):
        print("file " + log_file + " not exist!")
        return

    print("getting line info for file " + log_file + " ...")

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

if __name__ == '__main__':
    num = len(sys.argv)

    if num < 2:
        print("file not specified.")
        exit(0)

    lst_files = sys.argv[1:]
    log_info = "merge file: "
    for item in lst_files:
        log_info = log_info + item + ", "
    print(log_info + "\n")

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

