"""Celery entry point for draining the ledger posting queues — schedule via Celery Beat."""

from celery import shared_task

from .services.queue_consumer import process_pending_postings


@shared_task
def process_pending_ledger_postings():
    return process_pending_postings()
