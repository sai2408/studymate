"""
Task queue demo with Celery + Redis (shown live, not part of StudyMate).
Why: FastAPI BackgroundTasks run inside the API process. A task queue runs work
in SEPARATE worker processes, survives restarts, and can retry and scale.

1. Start Redis (the queue):     docker run -d -p 6379:6379 --name redis redis
2. Start a worker:              celery -A tasks worker --loglevel=info
                                (Windows: celery -A tasks worker --loglevel=info --pool=solo)
3. In another terminal:         python send_tasks.py
"""
import time

from celery import Celery

app = Celery("studymate", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0")


@app.task
def count_words(text: str) -> int:
    time.sleep(3)  # pretend this is slow
    return len(text.split())


@app.task(bind=True, max_retries=3)
def send_reminder(self, email: str):
    print(f"Sending study reminder to {email}")
    return f"reminder sent to {email}"