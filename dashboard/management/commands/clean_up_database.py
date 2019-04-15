# coding: utf-8
import time
from datetime import datetime, timedelta
from django.core.management import BaseCommand

from dashboard.models import SystemUseStatus


class Command(BaseCommand):
    """
    每天定期清理30天之前的数据
    """

    def handle(self, *args, **options):
        while True:
            thirty_day = datetime.now() - timedelta(days=30)
            thirty_bofore_datas = SystemUseStatus.objects.filter(alert_time__lte=thirty_day)
            if thirty_bofore_datas.exists():
                thirty_bofore_datas.delete()

            time.sleep(60 * 60 * 24)
