"""CLI entrypoint for Project 2 Auto-Publishing Background Worker.

Usage:
    python -m worker.main --once              # Process pending queue once and exit
    python -m worker.main --poll              # Start continuous polling loop
    python -m worker.main --seed              # Seed sample test jobs into publishing_jobs
    python -m worker.main --sync-analytics     # Pull and sync engagement metrics
    python -m worker.main --health            # Check publisher provider connectivity
"""
import argparse
import logging
import signal
import sys
import time

from worker.config import worker_settings
from worker.poller import PublishingWorker
from worker.publishers import get_publisher
from worker.seed_test_jobs import seed_test_publishing_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ja_assure.worker")

_running = True


def _signal_handler(sig, frame):
    global _running
    logger.info("Termination signal received. Shutting down worker...")
    _running = False


def run_continuous_polling(worker: PublishingWorker, interval_seconds: int):
    """Runs continuous background polling using APScheduler if available, or a resilient loop."""
    logger.info(
        "Starting background worker: provider=%s, poll_interval=%ds, batch_size=%d",
        worker_settings.PUBLISHER_MODE,
        interval_seconds,
        worker.batch_size,
    )

    try:
        from apscheduler.schedulers.blocking import BlockingScheduler

        scheduler = BlockingScheduler()
        scheduler.add_job(
            worker.poll_once,
            "interval",
            seconds=interval_seconds,
            id="publishing_poll",
            # No next_run_time here: in APScheduler 3.x next_run_time=None adds
            # the job PAUSED, so it never fired after the startup sweep below
            # and jobs created later sat in the queue until a restart.
        )
        scheduler.add_job(
            worker.sync_analytics,
            "interval",
            seconds=max(interval_seconds * 3, 30),
            id="analytics_sync",
        )

        # Run first sweep immediately
        worker.poll_once()

        logger.info("APScheduler running. Press Ctrl+C to exit.")
        scheduler.start()
    except (ImportError, Exception) as exc:
        logger.info("Running standard resilient poll loop (APScheduler: %s)", exc)
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

        iteration = 0
        while _running:
            try:
                stats = worker.poll_once()
                if stats.get("claimed", 0) > 0:
                    logger.info("Poll result: %s", stats)

                iteration += 1
                if iteration % 3 == 0:
                    worker.sync_analytics()

            except Exception as e:
                logger.error("Error in polling iteration: %s", e)

            for _ in range(interval_seconds):
                if not _running:
                    break
                time.sleep(1)

    logger.info("Worker stopped.")


def main():
    parser = argparse.ArgumentParser(description="JA Assure Auto-Publishing Worker")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process current pending/scheduled queue once and exit",
    )
    parser.add_argument(
        "--poll",
        action="store_true",
        help="Run continuous polling background daemon",
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Insert test jobs into database for verification",
    )
    parser.add_argument(
        "--sync-analytics",
        action="store_true",
        help="Sync engagement metrics for published jobs into analytics table",
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Check publisher connectivity and credentials",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=worker_settings.POLL_INTERVAL_SECONDS,
        help="Polling interval in seconds (default: 10)",
    )

    args = parser.parse_args()
    publisher = get_publisher()
    worker = PublishingWorker(publisher=publisher)

    if args.seed:
        logger.info("Seeding test publishing jobs...")
        seed_test_publishing_data()
        return

    if args.health:
        info = publisher.health_check()
        logger.info("Publisher Health Status: %s", info)
        return

    if args.sync_analytics:
        logger.info("Running analytics synchronization...")
        count = worker.sync_analytics()
        logger.info("Synced analytics for %d post(s).", count)
        return

    if args.once:
        logger.info("Running single poll pass...")
        stats = worker.poll_once()
        logger.info("Poll sweep completed: %s", stats)
        return

    # Default to continuous polling if --poll or no flag is provided
    run_continuous_polling(worker, args.interval)


if __name__ == "__main__":
    main()
