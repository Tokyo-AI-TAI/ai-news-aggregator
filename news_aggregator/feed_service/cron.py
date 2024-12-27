from django_cron import CronJobBase, Schedule
from django.core.management import call_command
from django.conf import settings
from zoneinfo import ZoneInfo


class UpdateFeedsCronJob(CronJobBase):
    schedule = Schedule(run_at_times=["00:20", "07:00"])
    code = "feed_service.update_feeds_cron"  # a unique code
    timezone = ZoneInfo("Asia/Tokyo")  # Set to JST

    def do(self):
        call_command("update_feeds")
