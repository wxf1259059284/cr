# -*- coding: utf-8 -*-
import os
import uuid

from django.conf import settings

from .utils import backup, file_upgrade, zip, command, decorator


@decorator.upgrade_status_log
def upgrade_cr(sender, instance=None, created=False, **kwargs):
    if created:
        # 解压升级包
        tmp_path = os.path.join('/tmp', str(uuid.uuid4()))
        zipper = zip.ZipOperation(instance.upgrade_package, tmp_path)
        zipper.unzip()

        # 项目文件，数据库备份，每次备份会删除上次备份
        backup_operation = backup.BackupOperation()
        backup_operation.raise_backup()

        file_path = os.path.join(tmp_path, 'upgrade')
        sh_path = os.path.join(tmp_path, 'sh')

        cmd = command.Command()
        # 升级前脚本
        before_sh = os.path.join(sh_path, 'before_upgrade.sh')
        if os.path.exists(before_sh):
            cmd.run_shell(before_sh)

        # 文件替换
        upgrade = file_upgrade.UpdateFileOperation(file_path, settings.BASE_DIR)
        # upgrade = file_upgrade.UpdateFileOperation(file_path, '/home/cr')
        upgrade.update_files()

        # 根据升级文件执行django操作
        models_files, language_files = file_upgrade.raise_django_operations(
            file_upgrade.FileOperation.list_dir(tmp_path)
        )
        if models_files:
            cmd.django_migrate()
        if language_files:
            cmd.django_compilemessages()

        # 升级后脚本
        after_sh = os.path.join(sh_path, 'after_upgrade.sh')
        if os.path.exists(after_sh):
            cmd.run_shell(after_sh)

        # 清理临时文件
        zipper.clear_tmp()

        # 重启cr项目
        cmd.run_cmd('supervisorctl restart cr')
