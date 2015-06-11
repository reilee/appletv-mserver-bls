#!/bin/bash
/etc/init.d/lighttpd.sh stop
/opt/etc/init.d/K92avs.sh stop
echo "enable_httpd=False" > /etc/melco/httpd
cp -af /etc/lighttpd/bak/lighttpd.conf /etc/melco/
cp -af /etc/lighttpd/bak/mod_cgi.conf /etc/lighttpd/
rm -f /etc/lighttpd/avs.conf
rm -rf /DataVolume/www
rm -rf /DataVolume/.avs
rm  /DataVolume
rm -f /opt/etc/init.d/S92avs.sh
rm -f /opt/etc/init.d/K92avs.sh
rm -rf /opt/avs
rm /var/run/avs-daemon.pid
echo "Uninstall done!"
