# -*- coding: utf-8 -*-
import os
import sys
import subprocess

from .decorator import raise_error


class Command(object):
    def __run_command(self, args, str_cmd=False):
        process_func = subprocess.Popen(
            args,
            env=os.environ.copy(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=str_cmd
        )
        return process_func

    @raise_error()
    def run_cmd(self, args):
        if not isinstance(args, list):
            args = args.split()
        process = self.__run_command(args)
        output, error = process.communicate()
        return process.returncode, output, error

    @raise_error()
    def run_shell(self, args):
        if not isinstance(args, list):
            args = [args]
        map(lambda x: os.chmod(x, 0777), args)
        process = self.__run_command(args, str_cmd=True)
        output, error = process.communicate()
        return process.returncode, output, error

    def django_manage(self, cmd, arg='', str_cmd=False):
        if not str_cmd:
            args = [sys.executable, 'manage.py', cmd, arg] if arg else [sys.executable, 'manage.py', cmd]
        else:
            args = ' '.join([sys.executable, 'manage.py', cmd, arg])

        process = self.__run_command(args, str_cmd=str_cmd)
        output, error = process.communicate()

        return process.returncode, output, error

    def django_dumpdata(self, args):
        return self.django_manage('dumpdata', arg=args, str_cmd=True)

    def django_loaddata(self, path):
        return self.django_manage('loaddata', arg=path)

    def django_flush(self):
        return self.django_manage('flush', arg='--no-input')

    @raise_error()
    def django_migrate(self):
        return self.django_manage('migrate')

    @raise_error()
    def django_collectstatic(self):
        return self.django_manage('collectstatic')

    @raise_error()
    def django_compilemessages(self):
        return self.django_manage('compilemessages', arg='--no-input')
