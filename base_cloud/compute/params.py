from __future__ import unicode_literals


user_data_start = """Content-Type: multipart/mixed; boundary="===============2197920354430400835=="
MIME-Version: 1.0

--===============2197920354430400835==
Content-Type: text/cloud-config; charset="us-ascii"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Content-Disposition: attachment; filename="cloudconfig.txt"

#cloud-config
"""

change_root_pwd = """
ssh_pwauth: true
disable_root: 0
chpasswd:
  list: |
    root:{root_pwd}
  expire: false
"""

add_xctf_user = """
groups:
  - xctf

users:
  - name: xctf
    primary-group: xctf
    shell: /bin/bash
    lock_passwd: false
    plain_text_passwd: '{xctf_pwd}'
"""

add_xctf_user_with_sudo = """
groups:
  - xctf

users:
  - name: xctf
    primary-group: xctf
    shell: /bin/bash
    sudo: ALL=(ALL) NOPASSWD:ALL
    lock_passwd: false
    plain_text_passwd: '{xctf_pwd}'
"""

add_group_prefix = """
groups:
{groups}
"""

add_group = """
  - {group}
"""

add_user_prefix = """
users:
"""

add_user = """
  - name: {username}
    primary-group: {group}
    shell: /bin/bash
    lock_passwd: false
    plain_text_passwd: '{password}'
"""

add_user_with_sudo = """
  - name: {username}
    primary-group: {group}
    shell: /bin/bash
    lock_passwd: false
    sudo: ALL=(ALL) NOPASSWD:ALL
    plain_text_passwd: '{password}'
"""

script_block_start = """
--===============2197920354430400835==
Content-Type: text/x-shellscript; charset="us-ascii"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Content-Disposition: attachment; filename="boothook.txt"

#!/bin/sh
set -o xtrace
"""

send_message2oj_template_vm = """
echo "send messages to oj platform"
curl -d '' "{report_url}"
"""

send_message2oj_new = """
echo "send messages to oj platform"
curl -d "env_id={env_id}&vm_id='{vm_id}'&vm_status={status}" "{report_url}"
"""

report_started_status = """
echo "send messages to oj platform"
curl -d {}
"""

report_inited_status = """
echo "send messages to oj platform"
curl -d {}
"""

send_message2oj = """
echo "send messages to oj platform"
curl -d "uuid={exam_uuid}&status={status}&inst={inst_type}" "{report_url}"
"""

send_message2ad = """
echo "send messages to ad platform"
curl -d "address={address}&status={status}" "{report_url}"
"""

update_xctf_folder = """
chown xctf:xctf -R /home/xctf
"""

update_hosts = """
if grep -q "mirrors.163.com" /etc/hosts;
then
echo "etc_hosts already updated."
else
echo "{nginx_host}  mirrors.163.com" >> /etc/hosts
echo "{nginx_host}  pecl.php.net" >> /etc/hosts
echo "{nginx_host}  pypi.douban.com" >> /etc/hosts
echo "{nginx_host}  npm.taobao.org" >> /etc/hosts
echo "{nginx_host}  gems.ruby-china.org" >> /etc/hosts
fi
"""

download_zip = """
curl -o /tmp/{zip_file_name} {attach_url} && \
unzip /tmp/{zip_file_name} -d /tmp/{file_folder}
"""

install_evn = """
cd /tmp/{script_folder} && \
chmod +x /tmp/{script_folder}/*.sh && \
/bin/bash /tmp/{file_folder}/{install_script} && \
sync
"""

setup_services = """
cd /tmp/{file_folder} && \
/bin/bash /tmp/{file_folder}/init.sh {flag}
"""

init_services = """
cd /tmp/{script_folder} && \
/bin/bash /tmp/{file_folder}/{init_script}
"""

delete_default_gw = """
route delete default gw 192.168.0.1
"""

set_default_gw = """
route add -net 192.168.0.0/24 gw 192.168.0.1
"""

execute_tcpdump = """
nohup tcpdump -i eth0 -s0 -G 300 -Z root -w /tmp/%Y_%m%d_%H%M_%S.pcap &
"""

clean_env = """
rm -rf /tmp/{file_folder}*
rm -rf /var/log/cloud-*
"""

clean_log = """
rm -rf /var/log/cloud-*
"""

ubuntu_unixtodos = """
fromdos /tmp/{file_folder}/*.sh
"""

centos_unixtodos = """
dos2unix /tmp/{file_folder}/*.sh
"""

user_data_end = """

--===============2197920354430400835==--
"""

powershell_start = """rem cmd
"""

windows_user_create = """net user {username} /add /y
"""

windows_add_user_to_admin = """net localgroup Administrators "{username}" /add /y
"""

windows_add_user_to_rdp = """net localgroup "Remote Desktop Users" "{username}" /add /y
"""

windows_change_user_pwd = """net user {username} "{password}" /y
"""

windows_send_message2oj_template_vm = """
curl -d '' "{report_url}"
"""

windows_send_message2oj = """
curl -d "vm_status={status}&env_id={env_id}&vm_id={vm_id}" "{report_url}"
"""

windows_download_zip = """
curl -o "C:/cloud/{zip_file_name}" {attach_url}
winrar x -y "C:/cloud/{zip_file_name}" "C:/cloud/{file_folder}/"
"""

windows_install_evn = """
cd "C:/cloud/{script_folder}/"
call "C:/cloud/{file_folder}/{install_script}"
"""

windows_init_services = """
cd "C:/cloud/{script_folder}/"
call C:/cloud/{file_folder}/{init_script}
"""

windows_clean_env = """
rd /S /Q "C:/cloud/{file_folder}"
del /S /Q "C:/cloud/{file_folder}.zip"
"""

windows_clean_log = """
del /S /Q "C:/Program Files/Cloudbase Solutions/Cloudbase-Init/log/*"
"""
