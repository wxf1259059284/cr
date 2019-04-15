#!/bin/bash

source /etc/profile
workon cr

mkdocs build
sed -i 's/wy-nav-content{padding:1.618em 3.236em;height:100%;max-width:800px;margin:auto}/wy-nav-content{padding:1.618em 3.236em;height:100%;margin:auto}/g' ./site/css/theme.css                                                     
sed -i 's/href="\//href="\/help\//g' ./site/404.html                                                               
sed -i 's/src="\//src="\/help\//g' ./site/404.html                                                                 
sed -i 's/action="\//action="\/help\//g' ./site/404.html                                                           
sed -i "s/base_url = ''/base_url = '\/help'/g" ./site/404.html                                                     
sed -i 's/<\/pre>/<\/code><\/pre>/g' ` find ./site/ -iname "*.html"`                                               
sed -i 's/<pre>/<pre><code>/g' ` find ./site/ -iname "*.html"`


