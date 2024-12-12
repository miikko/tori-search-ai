import multiprocessing

bind = "0.0.0.0:8000"
workers = (multiprocessing.cpu_count() * 2) + 1
worker_class = "sync"
max_requests = 1000
max_requests_jitter = 50 # Prevents all workers from restarting at the same time
timeout = 60
graceful_timeout = 30
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stdout
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
chdir = "src"