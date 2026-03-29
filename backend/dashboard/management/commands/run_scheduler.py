"""Management command to start the APScheduler for periodic data fetching."""

import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django_apscheduler.jobstores import DjangoJobStore

from dashboard.jobs import (
    fetch_calendar,
    fetch_google_calendar,
    fetch_google_photos,
    fetch_news,
    fetch_stocks,
    fetch_weather,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Runs APScheduler for periodic data fetching."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        scheduler.add_job(
            fetch_weather,
            trigger=IntervalTrigger(minutes=15),
            id="fetch_weather",
            max_instances=1,
            replace_existing=True,
        )

        scheduler.add_job(
            fetch_stocks,
            trigger=IntervalTrigger(minutes=5),
            id="fetch_stocks",
            max_instances=1,
            replace_existing=True,
        )

        scheduler.add_job(
            fetch_calendar,
            trigger=IntervalTrigger(minutes=30),
            id="fetch_calendar",
            max_instances=1,
            replace_existing=True,
        )

        scheduler.add_job(
            fetch_news,
            trigger=IntervalTrigger(minutes=60),
            id="fetch_news",
            max_instances=1,
            replace_existing=True,
        )

        scheduler.add_job(
            fetch_google_calendar,
            trigger=IntervalTrigger(minutes=30),
            id="fetch_google_calendar",
            max_instances=1,
            replace_existing=True,
        )

        scheduler.add_job(
            fetch_google_photos,
            trigger=IntervalTrigger(minutes=60),
            id="fetch_google_photos",
            max_instances=1,
            replace_existing=True,
        )

        self.stdout.write(self.style.SUCCESS("Starting scheduler..."))
        logger.info("Starting scheduler...")
        try:
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            self.stdout.write(self.style.SUCCESS("Scheduler shut down successfully."))
