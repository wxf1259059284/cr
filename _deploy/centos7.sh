# 检查controller是否配置
if [ `grep -c "controller" /etc/hosts` -eq 0 ]; then
    echo "[ERROR] Controller not configured ."
    echo "Please config controller in /etc/hosts! eg: 10.10.52.31 controller."
    exit 0
else
    echo "Found controller in /etc/hosts ."
fi

PRODUCT_DIR=/home/cr
DEPLOY_DIR=${PRODUCT_DIR}/_deploy

#安装基础库
yum -y install gcc
yum -y install pcre
yum -y install pcre-devel
yum -y install wget
yum -y install vim
yum -y install python-devel
yum -y install zlib-devel
yum -y install libjpeg-turbo-devel zziplib-devel
yum -y install ffmpeg

# 安装mariadb
yum -y install mariadb mariadb-devel mariadb-server
# 安装redis memcached
yum -y install redis
yum -y install memcached

# nginx
cd /tmp
wget http://nginx.org/download/nginx-1.11.3.tar.gz
tar zxvf nginx-1.11.3.tar.gz
cd nginx-1.11.3
./configure --prefix=/usr/local/nginx --with-stream
make
make install
# 添加代理配置目录
mkdir /usr/local/nginx/conf/tcp.d/

# 安装pip, 配置pip源
cd /tmp
curl -O https://bootstrap.pypa.io/get-pip.py
python get-pip.py
pip install  --upgrade pip
mkdir ~/.pip/
cat <<EOF >> ~/.pip/pip.conf
[global]
index-url = https://mirrors.aliyun.com/pypi/simple/

[install]
trusted-host=mirrors.aliyun.com
EOF

pip install supervisor
# 配置supervisor
cd /tmp
echo_supervisord_conf > supervisord.conf
cat <<EOF >> supervisord.conf
[include]
files = /etc/supervisord.d/*.conf
EOF
mv supervisord.conf /etc/
mkdir /etc/supervisord.d/
# 启动supervisor
supervisord -c /etc/supervisord.conf

# 配置项目nginx
. ${DEPLOY_DIR}/supervisor_nginx_config.sh
# 配置项目supervisor
. ${DEPLOY_DIR}/supervisor_config.sh
supervisorctl update

# 虚拟环境
pip install virtualenv
pip install virtualenvwrapper
# 配置虚拟环境
cat <<"EOF" >> /etc/profile
export WORKON_HOME=$HOME/.virtualenvs
source /usr/bin/virtualenvwrapper.sh
EOF
source /etc/profile
mkvirtualenv cr
workon cr

# 配置　base_remote.setting
# -- _GUACAMOLE_ADDRESS: 安装guacamole的机器地址　本地安装则127.0.0.1
# 配置　base_proxy.setting
# -- PROXY_IP: 代理IP

cd ${PRODUCT_DIR}
pip install -r requirements.txt

# 建库, 建表
mysql -e "
CREATE USER 'cr'@'%' IDENTIFIED BY 'cr';
CREATE USER 'cr'@'localhost' IDENTIFIED BY 'cr';
CREATE DATABASE cr DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
GRANT ALL PRIVILEGES ON cr.* TO 'cr'@'%';
GRANT ALL PRIVILEGES ON cr.* TO 'cr'@'localhost';
"

