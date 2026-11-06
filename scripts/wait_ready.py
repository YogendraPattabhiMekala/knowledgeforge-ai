"""Bounded readiness check for documented local/CI startup commands."""
import sys, time, urllib.request
url = sys.argv[1] if len(sys.argv)>1 else 'http://localhost:3000/api/health'
for attempt in range(60):
    try:
        with urllib.request.urlopen(url,timeout=2) as response:
            if response.status==200:
                print('Ready:',url)
                break
    except (OSError,TimeoutError):
        if attempt==59:raise SystemExit('Service not ready after 60 attempts: '+url)
        time.sleep(1)
