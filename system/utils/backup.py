# -*- coding: utf-8 -*-
import os
import shutil
import subprocess

from django.conf import settings


class BackupOperation(object):
    def __init__(self, parent_dir='/home', backup_name='cr_backup', cr_backup_dir='cr', db_backup_name='cr_backup.sql'):
        self.process = subprocess.Popen
        self.backup_dir = os.path.join(parent_dir, backup_name)
        self.cr_backup_dir = os.path.join(self.backup_dir, cr_backup_dir)
        self.db_back_name = os.path.join(self.backup_dir, db_backup_name)

    def __excute(self, cmd):
        '''执行cmd命令'''
        process = self.process(cmd,
                               env=os.environ.copy(),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               shell=True)
        _, error = process.communicate()
        if error:
            raise Exception(error)

    def complete_cr_backup_dir(self):
        '''生成备份所需文件夹'''
        if not os.path.exists(self.cr_backup_dir):
            os.makedirs(self.cr_backup_dir)

    def clear_backup(self):
        '''清除备份'''
        try:
            shutil.rmtree(self.backup_dir)
        except OSError:
            pass

    def backup_cr(self):
        '''备份cr项目除media文件夹下所有文件'''
        ignore = shutil.ignore_patterns('media')
        shutil.copytree(settings.BASE_DIR, self.cr_backup_dir, ignore=ignore)

    def raise_db_backup_cmd(self):
        '''生成备份数据库命令'''
        db_info = settings.DATABASES.get('default')
        user = db_info.get('USER')
        passwd = db_info.get('PASSWORD')
        db = db_info.get('NAME')

        if not all((user, passwd, db)):
            raise ValueError('Incorrect Database Information')

        db_backup_cmd = "mysqldump -u{user} -p{pwd} {db} > {file}".format(
            user=user,
            pwd=passwd,
            db=db,
            file=self.db_back_name
        )
        return db_backup_cmd

    def raise_backup(self):
        '''文件备份'''
        self.clear_backup()
        self.backup_cr()

        db_backup_cmd = self.raise_db_backup_cmd()
        try:
            self.__excute(db_backup_cmd)
        except Exception as e:
            if 'Warning' not in e.message:
                raise e

    def backup_recovery(self):
        '''todo: 数据库备份恢复未完成'''
        if not all(map(os.path.exists, [self.backup_dir, self.cr_backup_dir, self.db_back_name])):
            raise Exception('Backup Files Not Completed')
        shutil.copytree(
            os.path.join(settings.BASE_DIR, 'media'),
            os.path.join(self.cr_backup_dir, 'media')
        )

        # shutil.rmtree(settings.BASE_DIR)
        # shutil.copytree(self.cr_backup_dir, settings.BASE_DIR)
