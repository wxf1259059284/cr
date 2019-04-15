# -*- coding: utf-8 -*-
import os
import zipfile
import shutil


class ZipOperation(object):
    def __init__(self, zip_path, unzip_path):
        self.zip_path = zip_path
        self.unzip_path = unzip_path

    def unzip(self):
        if not os.path.exists(self.unzip_path):
            os.makedirs(self.unzip_path)

        if not os.path.isdir(self.unzip_path):
            raise ValueError('Invalid Unzip Path')

        f = zipfile.ZipFile(self.zip_path, 'r')
        for file in f.namelist():
            f.extract(file, self.unzip_path)

    def clear_tmp(self):
        shutil.rmtree(self.unzip_path)
