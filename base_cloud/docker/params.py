from __future__ import unicode_literals


download_zip = "curl -o /tmp/{zip_file_name} {attach_url}"

unzip_file = "unzip /tmp/{zip_file_name} -d /tmp/{file_folder}"

change_dir = "cd /tmp/{script_folder}"

install_evn = "/bin/bash /tmp/{file_folder}/{install_script}"

init_services = "/bin/bash /tmp/{file_folder}/{init_script}"

report_status = "curl -d \"address={address}&status={status}\" \"{report_url}\""

report_started_status = "curl -d {}"

report_inited_status = "curl -d {}"

clean_zip = "rm -rf /tmp/{file_folder}*"

change_root_pwd = "echo {root_passwd} | passwd --stdin  root"
