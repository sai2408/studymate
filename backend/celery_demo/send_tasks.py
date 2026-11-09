"""Sends tasks to the queue. The worker terminal shows them being processed."""
from tasks import count_words, send_reminder

job = count_words.delay("Normalization removes redundancy from tables")
print("Task queued with id:", job.id, "| status:", job.status)
print("Waiting for result...")
print("Result:", job.get(timeout=15))

reminder = send_reminder.delay("student@example.com")
print(reminder.get(timeout=15))