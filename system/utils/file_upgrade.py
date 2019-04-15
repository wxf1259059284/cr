# -*- coding:utf-8 -*-
import os
import shutil

from django.conf import settings

from .decorator import raise_error


def raise_django_operations(files):
    models_file = filter(lambda x: x.endswith('models.py'), files)
    language_files = filter(lambda x: x.endswith('.po') or x.endswith('.mo'), files)
    return models_file, language_files


class FileOperation(object):
    def complete_dir(self, abs_path):
        dir_path, _ = os.path.split(abs_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    @classmethod
    def list_dir(cls, dir):
        files = list()
        for path in os.listdir(dir):
            abs_path = os.path.join(dir, path)
            if os.path.isdir(abs_path):
                files.extend(cls.list_dir(abs_path))
            else:
                files.append(abs_path)
        return files


class UpdateFileOperation(FileOperation):
    def __init__(self, source_dir, destination_dir=settings.BASE_DIR):
        super(UpdateFileOperation, self).__init__()
        self.source = source_dir
        self.destionation = destination_dir

    def replace_file(self, source_abs_path):
        destonation_abs_path = source_abs_path.replace(self.source, self.destionation)
        self.complete_dir(destonation_abs_path)
        shutil.copy(source_abs_path, destonation_abs_path)

    @raise_error()
    def update_files(self):
        files = self.list_dir(self.source)
        map(self.replace_file, files)
