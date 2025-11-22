from app import app
from scheduler_tasks import start_scheduler

if __name__ == '__main__':
    scheduler = start_scheduler(app)
    try:
        app.run(debug=False, port=5002, use_reloader=False)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
