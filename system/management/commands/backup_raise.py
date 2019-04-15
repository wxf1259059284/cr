# -*- coding: utf-8 -*-
import logging
from django.core.management import BaseCommand

from system.utils.backup import BackupOperation

logger = logging.getLogger()


class Command(BaseCommand):
    def handle(self, *args, **options):
        operation = BackupOperation()
        try:
            operation.raise_backup()
        except Exception as e:
            logger.error(e.message)
