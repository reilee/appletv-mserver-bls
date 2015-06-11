#!/bin/bash
DATA_DIR=""
HOME_DIR=""
CONFIG_HTTPD="/etc/melco/httpd"
LIGHTTPD_CONF="/etc/melco/lighttpd.conf"
LIGHTTPD_CTRL="/etc/init.d/lighttpd.sh"

if [ ! -x /mnt/disk1 ] ; then
    HOME_DIR="/mnt/array1"
else
    HOME_DIR="/mnt/disk1" 
fi
ln -f -s $HOME_DIR /DataVolume
if [ -z $DATA_DIR ] ; then
    DATA_DIR=$HOME_DIR"/share"
fi

if [ ! -x /etc/lighttpd/bak ] ; then
	mkdir /etc/lighttpd/bak
	cp -p -f /etc/melco/lighttpd.conf /etc/lighttpd/bak/
	cp -p -f /etc/lighttpd/mod_cgi.conf /etc/lighttpd/bak/
fi
                
cp -f bls/avs.conf /etc/lighttpd/
cp -f bls/mime-types.conf /etc/lighttpd/
cp -f bls/mod_cgi.conf /etc/lighttpd/
cp -f bls/lighttpd.conf /etc/melco/
rm -f /etc/lighttpd/lighttpd.conf
ln -s -f $LIGHTTPD_CONF /etc/lighttpd/lighttpd.conf

echo "enable_httpd=True" > $CONFIG_HTTPD

mkdir /DataVolume/www
mkdir /DataVolume/www/cgi-bin
mkdir /DataVolume/www/htdocs
ln -f -s $DATA_DIR /DataVolume/www/htdocs/share
cp -pf cgi/* /DataVolume/www/cgi-bin/
chown apache:apache /DataVolume/www -R

sed -i 's/index.php/.index/' $LIGHTTPD_CTRL

mkdir -p /DataVolume/.avs/pl/
chmod -R 755 /DataVolume/.avs/
cp -af avs /opt/avs
cp -af avs/lib/* /usr/lib
chmod 755 /opt/avs -R
ln -f -s /opt/avs/avs.sh /opt/etc/init.d/S92avs.sh
ln -f -s /opt/avs/avs.sh /opt/etc/init.d/K92avs.sh

/etc/init.d/lighttpd.sh start
/opt/avs/avs.sh start

echo "AppleTV mserver for LS-(Q\W)VL install completed! Enjoy it!"
