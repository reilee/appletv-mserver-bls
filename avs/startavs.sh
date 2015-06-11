#!/bin/bash
export LC_ALL=zh_CN.UTF-8
#
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/bin:/opt/sbin:.
export LANG=zh_CN.UTF-8
cd /opt/avs
/bin/rm -f /DataVolume/.avs/*.ts
LD_LIBRARY_PATH=/opt/avs/lib python avs.py
