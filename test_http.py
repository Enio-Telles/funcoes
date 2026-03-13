import urllib.request
import urllib.error

def check_url(url):
    print(f"--- Checking {url} ---")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            print("Status:", response.status)
            print("Headers:")
            for k, v in response.headers.items():
                print(f"  {k}: {v}")
            body = response.read().decode('utf-8', errors='ignore')
            print("Body (first 500 chars):")
            print(body[:500])
            if 'sefin.ro.gov.br' in body:
                print("FOUND sefin.ro.gov.br in body!")
    except urllib.error.URLError as e:
        print("Error:", e)

check_url("http://localhost:3004/")
check_url("http://localhost:3004/src/main.tsx")
