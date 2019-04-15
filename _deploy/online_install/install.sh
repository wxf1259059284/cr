#!/bin/bash

debug=1

cr_path=/home/cr
nginx_path=/usr/local/nginx

if [[ "${debug}" == "1" ]]; then
  set -x
fi

function workon_and_cr_home()
{
    cd ${cr_path}
    source /etc/profile
    workon cr
}

function install_nginx()
{
    cp ${cr_path}"/_deploy/online_install/nginx-1.11.3.tar.gz" /tmp
    cp ${cr_path}"/_deploy/online_install/headers-more-nginx-module-0.33.tar.gz" /tmp
    cd /tmp

    tar zxvf nginx-1.11.3.tar.gz
    # nginx 增强头
    tar zxvf headers-more-nginx-module-0.33.tar.gz
    cd nginx-1.11.3
    ./configure --prefix=/usr/local/nginx --with-stream --add-module=/tmp/headers-more-nginx-module-0.33
    make
    make install

    mkdir -p /usr/local/nginx/conf/tcp.d/
    mkdir -p /usr/local/nginx/conf/http/

    touch /usr/local/nginx/conf/metadata_proxy.conf
    touch /usr/local/nginx/conf/http/api.conf
    touch /usr/local/nginx/conf/http/web.conf
    touch /usr/local/nginx/conf/http/cms.conf
}


function install_app()
{
    yum -y install wget

    # yum aliyun source
    if [[ `cat /etc/yum.repos.d/CentOS-Base.repo|grep aliyun | wc -l` -eq 0 ]]; then
        cd /etc/yum.repos.d/
        mv CentOS-Base.repo CentOS-Base.repo_bak
        wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo
        cd /tmp
    fi

    # install epel
    ls /etc/yum.repos.d/ | grep 'epel'
    if [[ $? -ne 0 ]]; then
        yum -y install epel-release
    fi

    yum -y install gcc
    yum -y install pcre
    yum -y install pcre-devel
    yum -y install vim
    yum -y install python-devel
    yum -y install zlib-devel
    yum -y install libjpeg-turbo-devel zziplib-devel
    yum -y install mariadb mariadb-devel mariadb-server
    yum -y install redis
    yum -y install memcached


    # 防火墙
    systemctl stop firewalld.service
    systemctl disable firewalld.service
    yum install -y iptables-services
    systemctl disable iptables
}


function install_pip()
{
    yum install -y python-pip
    pip install  --upgrade pip
    mkdir -p ~/.pip/

    cat > ~/.pip/pip.conf <<EOF
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
    mkdir -p /etc/supervisord.d/

    # 启动supervisor
    supervisord -c /etc/supervisord.conf

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
}


function mysql_init()
{
    /bin/systemctl restart mariadb.service

    mysql -e "
        CREATE USER 'cr'@'%' IDENTIFIED BY 'cr';
        CREATE USER 'cr'@'localhost' IDENTIFIED BY 'cr';
        CREATE DATABASE cr DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
        GRANT ALL PRIVILEGES ON cr.* TO 'cr'@'%';
        GRANT ALL PRIVILEGES ON cr.* TO 'cr'@'localhost';
    "
    mysql -e "
        CREATE DATABASE guacamole_db;
        CREATE USER 'guacamole_user'@'localhost' IDENTIFIED BY 'guacamole_pass';
        CREATE USER 'guacamole_user'@'%' IDENTIFIED BY 'guacamole_pass';
        GRANT SELECT,INSERT,UPDATE,DELETE ON guacamole_db.* TO 'guacamole_user'@'localhost';
        GRANT SELECT,INSERT,UPDATE,DELETE ON guacamole_db.* TO 'guacamole_user'@'%';
        FLUSH PRIVILEGES;
        quit
    "
}


function init_data()
{
    workon_and_cr_home
    pip install -r requirements.txt

    python manage.py makemigrations
    python manage.py migrate

    python manage.py loaddata _deploy/init_data/*.json
}


function nginx_config()
{
    cat ${cr_path}"/_deploy/online_install/nginx/metadata_proxy.conf" > ${nginx_path}"/conf/metadata_proxy.conf"
    cat ${cr_path}"/_deploy/online_install/nginx/cr.conf" > ${nginx_path}"/conf/cr.conf"
    cat ${cr_path}"/_deploy/online_install/nginx/api.conf" > ${nginx_path}"/conf/http/api.conf"
}


function supervisor_config()
{
    cat ${cr_path}"/_deploy/online_install/supervisor_cr.conf" > /etc/supervisord.d/cr.conf
    cat ${cr_path}"/_deploy/online_install/supervisor_service.conf" > /etc/supervisord.d/service.conf
}


function restart_all()
{
    supervisorctl update
    supervisorctl restart all
}


function print_help()
{
    echo -n "
     1) install base env
     2) install nginx
     3) install pip and virtualenv
     4) mysql init
     5) init data
     6) nginx config
     7) supervisor config
     8) restart all
    "
}

print_help

if [[ -n "$1" ]]; then
    step=$1
else
    echo "please choose one number"
    read step
fi

all_step=10


while [[ ${step} -lt ${all_step} ]]
do
    case ${step} in
        1)
            install_app
            ;;
        2)
            install_nginx
            ;;
        3)
            install_pip
            ;;
        4)
            mysql_init
            ;;
        5)
            init_data
            ;;
        6)
            nginx_config
            ;;
        7)
            supervisor_config
            ;;
        8)
            restart_all
            ;;
    esac
        step=`expr ${step} + 1`
done
