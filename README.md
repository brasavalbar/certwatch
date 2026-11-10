# certwatch

Zero-dependency Python script that watches TLS certificates and host availability, and alerts a Slack/Discord/generic webhook before things expire.

    python3 certwatch.py hosts.txt --days 14 --webhook https://hooks.example/xyz --loop 3600

- hosts.txt: one host[:port] per line
- Exit code 1 if any host is down or expiring soon (cron/CI friendly)
- --loop N runs 24/7 checking every N seconds

MIT licensed.
