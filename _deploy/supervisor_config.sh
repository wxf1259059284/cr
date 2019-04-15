# 配置nginx, memcached
touch /etc/supervisord.d/service.conf
cat <<"EOF" > /etc/supervisord.d/service.conf
[program:nginx]
command=/usr/local/nginx/sbin/nginx -c /usr/local/nginx/conf/cr.conf
autostart=true
autorestart=true
user=root

[program:memcached]
command=memcached -uroot -l127.0.0.1
autostart=true
autorestart=true
user=root

[program:redis]
command=redis-server
autostart=true
autorestart=true
user=root
EOF


# 配置rc supervisor
touch /etc/supervisord.d/cr.conf
cat <<"EOF" > /etc/supervisord.d/cr.conf
[program:cr]
command=/root/.virtualenvs/cr/bin/gunicorn cr.wsgi -c gunicorn_config.py
directory=/home/cr/
environment=LIBGUESTFS_PATH=/usr/lib64/guestfs,LIBGUESTFS_BACKEND=direct
autostart=true
autorestart=true
user=root

[program:daphne]
command=/root/.virtualenvs/cr/bin/daphne cr.asgi:channel_layer -b 127.0.0.1 -p 8088
directory=/home/cr/
autostart=true
autorestart=true
user=root

[program:ws_worker]
command=/root/.virtualenvs/cr/bin/python manage.py runworker --only-channels=websocket.*
directory=/home/cr/
numprocs=4
process_name=%(program_name)s_%(process_num)02d
autostart=true
autorestart=true
user=root
EOF
