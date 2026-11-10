#!/usr/bin/env python3
'''certwatch - zero-dependency TLS certificate expiry + uptime watcher with webhook alerts.
Usage: certwatch.py hosts.txt [--days 14] [--webhook URL] [--loop SECONDS]
hosts.txt: one host[:port] per line. Webhook gets JSON with text/content keys (Slack/Discord compatible).
Exit code 1 if any host is failing or expiring soon (CI/cron friendly).'''
import ssl, socket, sys, json, time, argparse, urllib.request
from datetime import datetime, timezone

def check(hostport, timeout=8):
    host, _, port = hostport.partition(':')
    port = int(port or 443)
    t0 = time.time()
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=timeout) as s:
            with ctx.wrap_socket(s, server_hostname=host) as ss:
                cert = ss.getpeercert()
        exp = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z').replace(tzinfo=timezone.utc)
        days = (exp - datetime.now(timezone.utc)).days
        return {'host': hostport, 'ok': True, 'days_left': days, 'ms': int((time.time()-t0)*1000), 'expires': exp.date().isoformat()}
    except Exception as e:
        return {'host': hostport, 'ok': False, 'error': str(e)[:120]}

def notify(url, text):
    body = json.dumps({'text': text, 'content': text}).encode()
    req = urllib.request.Request(url, body, {'Content-Type': 'application/json'})
    urllib.request.urlopen(req, timeout=10).read()

def run(hosts, days, webhook):
    bad = []
    for h in hosts:
        r = check(h)
        if not r['ok']:
            line = f"DOWN/ERROR {h}: {r['error']}"; bad.append(line)
        elif r['days_left'] < days:
            line = f"EXPIRING {h}: {r['days_left']}d left ({r['expires']})"; bad.append(line)
        else:
            line = f"ok {h}: {r['days_left']}d left, {r['ms']}ms"
        print(line)
    if bad and webhook:
        try: notify(webhook, 'certwatch alert:\n' + '\n'.join(bad))
        except Exception as e: print('webhook failed:', e, file=sys.stderr)
    return bad

if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('file'); a.add_argument('--days', type=int, default=14)
    a.add_argument('--webhook'); a.add_argument('--loop', type=int, default=0)
    o = a.parse_args()
    hosts = [l.strip() for l in open(o.file) if l.strip() and not l.startswith('#')]
    while True:
        bad = run(hosts, o.days, o.webhook)
        if not o.loop: sys.exit(1 if bad else 0)
        time.sleep(o.loop)
