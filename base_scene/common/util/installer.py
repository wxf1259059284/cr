# -*- coding: utf-8 -*-
import logging
import os

from django.conf import settings
from django.templatetags.static import static

from base.utils.enum import Enum
from base.utils.text import rk, contain_zh

from base_scene import app_settings
from base_scene.models import StandardDevice


logger = logging.getLogger(__name__)


windows_spliter = '''\r
'''
linux_spliter = '''
'''


window_template = Enum(
    BASE_DIR='''\r
mkdir {base_dir}\r
mkdir {base_dir}\\custom_install\r
''',
    CUSTOM_NORMAL_INSTALL='''\r
cd {base_dir}\r
{install_script}\r
''',
    CUSTOM_INSTALL='''\r
mkdir {base_dir}\\custom_install\\{installer_folder}\r
winrar x -y "{file_path}" "{base_dir}\\custom_install\\{installer_folder}"\r
call "{base_dir}\\custom_install\\{installer_folder}\\{install_script}"\r
''',
    MADE_SCRIPT_INSTALL='''\r
curl -o "{base_dir}\\custom_install\\install.bat" {file_url}\r
call "{base_dir}\\custom_install\\install.bat"\r
''',
    LOAD_DESKTOP_INSTALLER_LNK='''\r
curl -o "{base_dir}\\{inf_file_name}" {inf_file_url}\r
curl -o "{base_dir}\\{icon_file_name}" {icon_file_url}\r
curl -o "{desktop_dir}工具武器下载.html" {lnk_file_url}\r
{inf_install} "{base_dir}\\{inf_file_name}"\r
'''
)

linux_template = Enum(
    BASE_DIR='''
mkdir {base_dir}
mkdir {base_dir}/custom_install
''',
    CUSTOM_NORMAL_INSTALL='''
cd {base_dir}
{install_script}
''',
    CUSTOM_INSTALL='''
mkdir {base_dir}/custom_install/{installer_folder}
unzip {file_path} -d {base_dir}/custom_install/{installer_folder}
cd {base_dir}/custom_install/{installer_folder}
chmod +x {base_dir}/custom_install/{installer_folder}/*.sh
/bin/bash {base_dir}/custom_install/{installer_folder}/{install_script}
sync
''',
)


def get_spliter(system_sub_type):
    system_type = StandardDevice.SystemSubTypeMap[system_sub_type]
    if system_type == StandardDevice.SystemType.WINDOWS:
        return windows_spliter
    else:
        return linux_spliter


def fix_win_zh_script(script, spliter):
    return spliter + 'chcp 65001' + spliter + script + spliter + 'chcp 936' + spliter


def generate_base_dir_script(system_sub_type):
    system_type = StandardDevice.SystemSubTypeMap[system_sub_type]
    if system_type == StandardDevice.SystemType.WINDOWS:
        script = window_template.BASE_DIR.format(
            base_dir=app_settings.WINDOWS_INSTALLER_DIR,
        )
    else:
        script = linux_template.BASE_DIR.format(
            base_dir=app_settings.LINUX_INSTALLER_DIR,
        )
    return script


def generate_file_download_script(file_url, system_sub_type, file_name=None):
    if not file_name:
        file_name = file_url.split('/')[-1]
    system_type = StandardDevice.SystemSubTypeMap[system_sub_type]
    if system_type == StandardDevice.SystemType.WINDOWS:
        file_path = r'{base_dir}\{file_name}'.format(
            base_dir=app_settings.WINDOWS_INSTALLER_DIR,
            file_name=file_name,
        )
    else:
        file_path = r'{base_dir}/{file_name}'.format(
            base_dir=app_settings.LINUX_INSTALLER_DIR,
            file_name=file_name,
        )
    script = r'curl -o "{file_path}" {file_url}'.format(
        file_path=file_path,
        file_url=file_url,
    )
    return file_path, script


def generate_default_install_script(file_path, system_sub_type):
    script = ''
    if system_sub_type in (
        StandardDevice.SystemSubType.WINDOWS_10,
        StandardDevice.SystemSubType.WINDOWS_7,
        StandardDevice.SystemSubType.WINDOWS_SERVER_2012,
        StandardDevice.SystemSubType.WINDOWS_SERVER_2008,
    ):
        script = r'echo %s>>%s\file.txt' % (file_path, app_settings.WINDOWS_INSTALLER_DIR)
    elif system_sub_type in (
        StandardDevice.SystemSubType.WINDOWS_XP,
        StandardDevice.SystemSubType.WINDOWS_SERVER_2003,
    ):
        script = script + r'start /b {file_path}'.format(file_path=file_path)
    elif system_sub_type == StandardDevice.SystemSubType.CENTOS_7:
        if file_path.endswith('.rpm'):
            script = 'rpm -ivh {file}'.format(file=file_path)
    elif system_sub_type in (StandardDevice.SystemSubType.UBUNTU_14,
                             StandardDevice.SystemSubType.UBUNTU_16,
                             StandardDevice.SystemSubType.KALI_2):
        if file_path.endswith('.deb'):
            script = 'apt-get install {file}'.format(file=file_path)
    return script


def generate_default_custom_install_script(file_path, system_sub_type, install_script):
    system_type = StandardDevice.SystemSubTypeMap[system_sub_type]
    # 0不执行 1直接执行 2解压执行
    mode = 0
    file_path_lower = file_path.lower()
    if system_type == StandardDevice.SystemType.WINDOWS:
        template = window_template
        base_dir = app_settings.WINDOWS_INSTALLER_DIR
        if install_script.find('{this}') >= 0:
            file_name = file_path.split('\\')[-1]
            install_script = install_script.replace('{this}', file_name)
            mode = 1
        else:
            if file_path_lower.endswith('.zip') or file_path_lower.endswith('.rar'):
                mode = 2
    else:
        template = linux_template
        base_dir = app_settings.LINUX_INSTALLER_DIR
        if install_script.find('{this}') >= 0:
            file_name = file_path.split('/')[-1]
            install_script = install_script.replace('{this}', file_name)
            mode = 1
        else:
            if file_path.lower().endswith('.zip'):
                mode = 2

    if mode == 1:
        script = template.CUSTOM_NORMAL_INSTALL.format(
            base_dir=base_dir,
            install_script=install_script,
        )
    elif mode == 2:
        script = template.CUSTOM_INSTALL.format(
            file_path=file_path,
            base_dir=base_dir,
            installer_folder=rk(),
            install_script=install_script,
        )
    else:
        script = ''
    return script


def generate_installer_lnk_script(spliter, system_sub_type):
    script = spliter

    inf_file_name = 'convert_html_icon.INF'
    inf_file_url = settings.SERVER + settings.MEDIA_URL + 'download_installer_lnk/' + inf_file_name
    icon_file_name = 'bitbug.ico'
    icon_file_url = settings.SERVER + settings.MEDIA_URL + 'download_installer_lnk/' + icon_file_name
    lnk_file_url = settings.SERVER + settings.MEDIA_URL + 'download_installer_lnk/%s.html' % system_sub_type
    if system_sub_type in (
            StandardDevice.SystemSubType.WINDOWS_10,
            StandardDevice.SystemSubType.WINDOWS_7,
            StandardDevice.SystemSubType.WINDOWS_SERVER_2012,
            StandardDevice.SystemSubType.WINDOWS_SERVER_2008,
    ):
        script = script + 'chcp 65001' + spliter
        script = script + window_template.LOAD_DESKTOP_INSTALLER_LNK.format(
            base_dir=app_settings.WINDOWS_INSTALLER_DIR,
            inf_file_name=inf_file_name,
            inf_file_url=inf_file_url,
            icon_file_name=icon_file_name,
            icon_file_url=icon_file_url,
            desktop_dir='C:\\Users\\Public\\Desktop\\',
            lnk_file_url=lnk_file_url,
            inf_install=r'%SystemRoot%\System32\InfDefaultInstall.exe'
        ) + spliter
        script = script + 'chcp 936' + spliter
    elif system_sub_type in (
            StandardDevice.SystemSubType.WINDOWS_XP,
            StandardDevice.SystemSubType.WINDOWS_SERVER_2003,
    ):
        script = script + 'chcp 65001' + spliter
        script = script + window_template.LOAD_DESKTOP_INSTALLER_LNK.format(
            base_dir=app_settings.WINDOWS_INSTALLER_DIR,
            inf_file_name=inf_file_name,
            inf_file_url=inf_file_url,
            icon_file_name=icon_file_name,
            icon_file_url=icon_file_url,
            desktop_dir='C:\\Documents and Settings\\All Users\\桌面\\',
            lnk_file_url=lnk_file_url,
            inf_install=r'%SystemRoot%\System32\rundll32.exe setupapi.dll,InstallHinfSection DefaultInstall 132'
        ) + spliter
        script = script + 'chcp 936' + spliter
    elif system_sub_type == StandardDevice.SystemSubType.CENTOS_7:
        pass
    elif system_sub_type in (
            StandardDevice.SystemSubType.UBUNTU_14,
            StandardDevice.SystemSubType.UBUNTU_16,
            StandardDevice.SystemSubType.KALI_2
    ):
        pass
    return script


def generate_install_script(standard_device, installers):
    system_sub_type = standard_device.system_sub_type
    system_type = StandardDevice.SystemSubTypeMap[system_sub_type]
    spliter = get_spliter(system_sub_type)
    # 生成安装目录
    script = spliter + generate_base_dir_script(system_sub_type) + spliter

    # sub_script = spliter + generate_installer_lnk_script(spliter, system_sub_type) + spliter
    sub_script = spliter
    resources = []
    has_default_installer = False
    for installer in installers:
        resource = installer.resources.filter(platforms__icontains=system_sub_type).first()
        resources.append(resource)
        if resource.file and not resource.install_script:
            has_default_installer = True

    if has_default_installer and standard_device.system_sub_type in (
            StandardDevice.SystemSubType.WINDOWS_10,
            StandardDevice.SystemSubType.WINDOWS_7,
            StandardDevice.SystemSubType.WINDOWS_SERVER_2012,
            StandardDevice.SystemSubType.WINDOWS_SERVER_2008,
    ):
        installer_tool_urls = [
            settings.SERVER + static('base_scene/common/tools/windows_installer/1.dll'),
            settings.SERVER + static('base_scene/common/tools/windows_installer/start.exe'),
        ]
        for installer_tool_url in installer_tool_urls:
            file_path, download_script = generate_file_download_script(installer_tool_url, system_sub_type)
            sub_script = sub_script + download_script + spliter

    for resource in resources:
        if resource.file:
            file_name = os.path.basename(resource.file.name)
            file_url = settings.SERVER + settings.MEDIA_URL + resource.file.name

            is_win_file_contains_zh = system_type == StandardDevice.SystemType.WINDOWS and contain_zh(file_name)
            if is_win_file_contains_zh:
                download_file_name = (rk() + os.path.splitext(file_name)[-1])
            else:
                download_file_name = file_name
            file_path, download_script = generate_file_download_script(file_url, system_sub_type,
                                                                       download_file_name)
            sub_script = sub_script + download_script + spliter

            resource_script = ''
            if is_win_file_contains_zh:
                resource_script = resource_script + 'ren {} {}'.format(file_path, file_name) + spliter
                file_path = file_path.replace(download_file_name, file_name)

            if resource.install_script:
                resource_install_script = generate_default_custom_install_script(file_path, system_sub_type,
                                                                                 resource.install_script)
                is_win_script_contains_zh = system_type == StandardDevice.SystemType.WINDOWS and contain_zh(
                    resource_install_script)
                if not is_win_file_contains_zh and is_win_script_contains_zh:
                    resource_install_script = fix_win_zh_script(resource_install_script, spliter)
                resource_script = resource_script + resource_install_script + spliter
            else:
                resource_script = resource_script + generate_default_install_script(file_path,
                                                                                    system_sub_type) + spliter

            if is_win_file_contains_zh:
                resource_script = fix_win_zh_script(resource_script, spliter)

            sub_script = sub_script + resource_script + spliter
        else:
            if resource.install_script:
                resource_install_script = resource.install_script
                is_win_script_contains_zh = system_type == StandardDevice.SystemType.WINDOWS and contain_zh(
                    resource_install_script)
                if is_win_script_contains_zh:
                    resource_install_script = fix_win_zh_script(resource_install_script, spliter)
                sub_script = sub_script + resource_install_script + spliter

    if has_default_installer and standard_device.system_sub_type in (
            StandardDevice.SystemSubType.WINDOWS_10,
            StandardDevice.SystemSubType.WINDOWS_7,
            StandardDevice.SystemSubType.WINDOWS_SERVER_2012,
            StandardDevice.SystemSubType.WINDOWS_SERVER_2008,
    ):
        sub_script = sub_script + r'start /b {base_dir}\start.exe'.format(
            base_dir=app_settings.WINDOWS_INSTALLER_DIR) + spliter

    # windows作成脚本文件安装
    if system_type == StandardDevice.SystemType.WINDOWS:
        made_script_filename = '%s.bat' % rk()
        made_script_path = os.path.join(settings.MEDIA_ROOT, 'tmp_script', made_script_filename)
        with open(made_script_path, 'w') as made_script_file:
            made_script_file.write(sub_script)

        script = script + window_template.MADE_SCRIPT_INSTALL.format(
            base_dir=app_settings.WINDOWS_INSTALLER_DIR,
            file_url=settings.SERVER + settings.MEDIA_URL + 'tmp_script/' + made_script_filename,
        ) + spliter
    else:
        script = script + sub_script + spliter

    return script
