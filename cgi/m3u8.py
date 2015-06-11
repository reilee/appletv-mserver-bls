#!/usr/bin/env python
import os
import socket,urllib
try:
	server=os.environ['HTTP_HOST']
except:
	server="192.168.91.4"
try:
	length=float(os.environ["QUERY_STRING"])
except:
	length=0

cl=4
seg=0
print "Content-type: text/plain\r\n\r\n",

print "#EXTM3U\r\n",
print "#EXT-X-TARGETDURATION:4\r\n",
while cl<=length:
	print "#EXTINF:4\r\n",
	print "segment_%d.ts\r\n"%seg,
	seg=seg+1
	cl=cl+4
if int(length)>cl-4:
	print "#EXTINF:%s\r\n"%(int(length)-cl+4),
	print "segment_%d.ts\r\n"%seg,
print "#EXT-X-ENDLIST\n",
