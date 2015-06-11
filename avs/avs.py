#!/usr/bin/env python

import os,socket
from SocketServer import ThreadingTCPServer
ThreadingTCPServer.allow_reuse_address=True
ThreadingTCPServer.daemon_threads=True
import threading
import time
import subprocess
import sys,signal
clock=threading.Lock()
segbreak="-------SEGMENT-BREAK-------"

currento=None

SAVESEG=15

def mysig(sig,frame):
	global currento
	if currento is not None:
		clock.acquire()
		currento.stop=1
		clock.release()
	isstop=0
	while 1:
		clock.acquire()
		isstop=currento.isstop
		clock.release()
		if isstop==1:
			break
        sys.exit(1)

orisig=signal.signal(signal.SIGTERM,mysig)

PATH="/DataVolume/.avs/"
class trans:
	def __init__(self,fname,segoff,smap=None,copy=0):
		#self.cmd="""/opt/avs/bin/avconv --segment-length 4 --segment-offset %d -threads 4 -ss %d.0 -i "%s" -map 0:0,0:0 -map 0:1,0:1 -vf "crop=1280:720:0:0, scale=1280:720,copy" -aspect 1280:720 -y -f mpegts -async -1 -vcodec libx264 -vcodec copy -bsf:v h264_mp4toannexb -acodec libmp3lame -ab 256k -ar 48000 -ac 2 -""" % (segoff,segoff*4,fname)
		self.filename=fname
		self.smap=smap
		self.copy=copy
		if smap is not None:
			mvd='0:%d,0:0' % smap[0]
			mad='0:%d,0:1' % smap[1]
		else:
			mvd='0:0,0:0'
			mad='0:1,0:1'
		if segoff==0:
			self.cmd=['/opt/avs/bin/avconv','--segment-length','4','--segment-offset','%d'%segoff, '-threads', '4', '-ss', '0.0', '-i', fname, '-map', mvd,'-map', mad, '-y', '-f', 'mpegts', '-async', '-1', '-vcodec', 'copy', '-bsf:v', 'h264_mp4toannexb']
		elif segoff<6:
			self.cmd=['/opt/avs/bin/avconv','--segment-length','4','--segment-offset','%d'%segoff, '-threads', '4', '-ss', '0.0', '-i', fname, '-ss', '%d.0'%(segoff*4), '-map', mvd,'-map', mad, '-y', '-f', 'mpegts', '-async', '-1', '-vcodec', 'copy', '-bsf:v', 'h264_mp4toannexb']
		else:
			self.cmd=['/opt/avs/bin/avconv','--segment-length','4','--segment-offset','%d'%segoff, '-threads', '4', '-ss', '%d.0'%(segoff*4-24), '-i', fname, '-ss', '24.0', '-map', mvd,'-map', mad, '-y', '-f', 'mpegts', '-async', '-1', '-vcodec', 'copy', '-bsf:v', 'h264_mp4toannexb']
		if copy==0:
			self.cmd=self.cmd+['-acodec', 'libvo_aacenc', '-ab', '320k', '-ac', '2', '-']
		elif copy==2:
			self.cmd=self.cmd+['-acodec', 'ac3', '-ab', '448k', '-ar', '48000', '-ac', '6', '-']
		else:
			self.cmd=self.cmd+['-acodec', 'copy', '-']
		#print self.cmd
		self.segoff=segoff
		self.execseg=-1
		self.readseg=segoff
		self.stop=0
		self.wstop=0
		self.startseg=segoff
		self.isstop=0
	def finishseg(self):
		self.fts.close()
		clock.acquire()
		self.execseg=self.segcount
		clock.release()
		if self.segcount>=2*SAVESEG:
			try:
				os.unlink(PATH+"segment_%d.ts" % (self.segcount-2*SAVESEG))
			except:
				pass
		while 1:
			clock.acquire()
			myseg=self.readseg
			self.wstop=self.stop
			clock.release()
			if self.wstop==1:
				return
			if self.segcount>myseg+SAVESEG:
				time.sleep(1)
			else:
				break
			
		self.segcount+=1
		self.fts=file(PATH+"segment_%d.ts" % self.segcount,"w")
	def start(self):
		f=subprocess.Popen(self.cmd,stdout=subprocess.PIPE)
		self.segcount=self.segoff
		self.fts=file(PATH+"segment_%d.ts" % self.segcount,"w")
		lret=""
		while 1:
			ret=f.stdout.read(1048576)
			if len(ret)==0:
				if len(lret)>0:
					self.fts.write(lret)
				self.fts.close()
				clock.acquire()
				self.execseg=self.segcount
				self.isstop=1
				clock.release()
				break
			if len(lret)>0:
				nret=lret+ret
				fo=0
				while 1:
					pos=nret.find(segbreak)
					if pos>=0:
						fo=1
						self.fts.write(nret[:pos])
						self.finishseg()
						if self.wstop==1:
							os.kill(f.pid,15)
							clock.acquire()
							self.isstop=1
							clock.release()
							return
						nret=nret[pos+len(segbreak):]
					else:
						break
				if fo==1:
					lret=nret
				else:
					self.fts.write(lret)
					self.fts.write(ret[:-1*len(segbreak)])
					lret=ret[-1*len(segbreak):]
			else:
				while 1:
					pos=ret.find(segbreak)
					if pos>=0:
						self.fts.write(ret[:pos])
						self.finishseg()
						if self.wstop==1:
							os.kill(f.pid,15)
							return
						ret=ret[pos+len(segbreak):]
					else:
						break
				self.fts.write(ret[:-1*len(segbreak)])
				lret=ret[-1*len(segbreak):]

def info(fn):
	cmd="""/opt/avs/bin/avprobe "%s" 2>&1"""  % fn
	f=os.popen(cmd)
	data=f.read()
	f.close()
	lines=data.split("\n")
	length=''
	video=''
	audio=[]
	for line in lines:
		fields=line.split()
		if len(fields)<3:continue
		if fields[0]=='Duration:':
			length=fields[1]
		elif fields[0]=='Stream':
			if fields[2]=='Video:':
				video=fields[1]
			elif fields[2]=='Audio:':
				audio.append(line)
	return length,video,audio

class Handler:
	def __init__(self,request,client_address,server):
		rfile = request.makefile('rb',-1)
		wfile = request.makefile('wb', 0)
		data=''
		while 1:
			word=rfile.read(1)
			if word=='\n':
				break
			data=data+word
		ret=self.parse(data.strip())
		wfile.write(ret);
		if not wfile.closed:
			wfile.flush()
		wfile.close()
		rfile.close()
		request.shutdown(socket.SHUT_RDWR)
	def parse(self,data):
		global currento
		#print data
		if data[0]=='I':
			fn=data[1:]
			ret=str(info(fn))
		elif data[0]=='T':
			fn=data[1:]
			ret=list(info(fn))
			srt=fn[:-3]+'shooter.srt'
			try:
				st=os.stat(srt)
			except:
				st=None
			if st is None:
				cmd="""/opt/avs/shooter.py "%s" 2>&1"""  % fn
				os.system(cmd)
			try:
				st=os.stat(srt)
			except:
				st=None
			if st:
				ret.append('shooter.srt')
			ret=str(ret)
		elif data[0]=='S':
			fn=data[1:]
			arg=''
			if fn[-4:-2]=='.q':
				arg=fn[-2:]
				fn=fn[:-4]
			vinfo=info(fn)
			ret=str(vinfo)
			try:
				video=ret[1].split('.')[1]
				pos=video.find('(')
				if pos>=0:
					video=video[:pos].strip()
				video=int(video)
			except:
				video=0
			if arg=='':
				smap=None
				copy=0
			else:
				if arg[0]=='c':
					copy=1
					try:
						for audline in vinfo[2]:
							ainfo=audline.split("Audio:")
							sid=ainfo[0].split()[1].split('.')[1]
							pos=sid.find("(")
							if pos>=0:
								sid=sid[:pos]
							else:
								if sid[-1]==":":sid=sid[:-1]
							sinfo=ainfo[1].strip()
							if arg[1]==sid:
								break
						if sinfo.find("DTS")>=0 or sinfo.find("dca")>=0:
							copy=2
					except:
						pass
				else:
					copy=0
				audio=int(arg[1])
				smap=[video,audio]
			same=0
			if currento is not None:
				clock.acquire()
				wstop=currento.stop
				clock.release()
				if currento.filename!=fn or wstop==1 or currento.smap!=smap or currento.copy!=copy:
					clock.acquire()
					currento.stop=1
					clock.release()
				else:
					same=1
			if same==0:
				currento=trans(fn,0,smap,copy)
				t=threading.Thread(target = currento.start,args=())
				t.setDaemon(0)
				t.start()
		elif data[0]=='G':
			seg=int(data[1:])
			if currento is None:
				return "ERROR"
			clock.acquire()
			ex=currento.execseg
			clock.release()
			if seg>ex-2*SAVESEG and seg<=ex and seg>=currento.startseg:
				ret=PATH+"segmeng_%d.ts"%seg
				clock.acquire()
				currento.readseg=seg
				clock.release()
			elif seg>ex and seg<ex+SAVESEG:
				while 1:
					time.sleep(1)
					clock.acquire()
					ex=currento.execseg
					currento.readseg=seg
					clock.release()
					if ex>=seg:
						ret=PATH+"segmeng_%d.ts"%seg
						break
			else:
				fn=currento.filename
				smap=currento.smap
				copy=currento.copy
				clock.acquire()
				currento.stop=1
				clock.release()
				currento=trans(fn,seg,smap,copy)
				t=threading.Thread(target = currento.start,args=())
				t.setDaemon(0)
				t.start()
				while 1:
					time.sleep(1)
					clock.acquire()
					ex=currento.execseg
					clock.release()
					if ex>=seg:
						ret=PATH+"segmeng_%d.ts"%seg
						break
		else:
			ret='ERROR'
		return ret




server=ThreadingTCPServer(('0.0.0.0',7890),Handler)
		


server.serve_forever()

