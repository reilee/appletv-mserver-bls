Options +Indexes
RewriteEngine on
RewriteBase /
RewriteRule ^(.*)\.m3u8$ /cgi-bin/m3u8.cgi?$1 [L]
RewriteRule ^segment_(.*)\.ts$ /cgi-bin/ts.cgi?$1 [L]


