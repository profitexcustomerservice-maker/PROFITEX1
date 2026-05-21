import urllib.request
import urllib.error

for port in (8000, 8001):
    url = f'http://127.0.0.1:{port}/'
    print('REQUEST', url)
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        print('STATUS', resp.status)
        print(resp.read(2000).decode('utf-8', 'replace'))
    except urllib.error.HTTPError as e:
        print('HTTPError', e.code)
        print(e.read(2000).decode('utf-8', 'replace'))
    except Exception as ex:
        print('ERROR', type(ex).__name__, ex)
    print('---')
