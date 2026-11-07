import http.server, socketserver, threading, functools, os, sys
from playwright.sync_api import sync_playwright

ROOT = "/root/idelatech-local-ai"
PORT = 8123

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()

URL = f"http://127.0.0.1:{PORT}/index.html"
VIEWPORTS = [
    ("phone-390x844", 390, 844),
    ("phone-320x568", 320, 568),
    ("tablet-768x1024", 768, 1024),
    ("tabletL-1024x768", 1024, 768),
    ("laptop-1440x900", 1440, 900),
    ("wide-1920x1080", 1920, 1080),
]

with sync_playwright() as p:
    b = p.chromium.launch()
    for name, w, h in VIEWPORTS:
        pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
        pg.goto(URL, wait_until="networkidle")
        res = pg.evaluate("""() => {
          const de = document.documentElement;
          const docOverflow = de.scrollWidth - window.innerWidth;
          const canScroll = el => { const b = el.scrollLeft; el.scrollLeft = 9999; const m = el.scrollLeft; el.scrollLeft = b; return m; };
          // any element wider than viewport
          let worst = 0, worstEl = '';
          document.querySelectorAll('body *').forEach(el => {
            const r = el.getBoundingClientRect();
            const ov = r.right - window.innerWidth;
            if (ov > worst) { worst = ov; worstEl = el.tagName + '.' + (el.className||''); }
          });
          return {docOverflow, worst: Math.round(worst), worstEl,
                  bodyScrollable: canScroll(document.body)};
        }""")
        flag = "OK " if res["docOverflow"] <= 1 else "BAD"
        print(f"{flag} {name:18s} docOverflow={res['docOverflow']:4d} worst=+{res['worst']:4d}px {res['worstEl'][:40]}")
        pg.screenshot(path=f"/root/idelatech-local-ai/shot_{name}.png", full_page=(name.startswith("laptop") or name.startswith("wide")))
        pg.close()
    b.close()
httpd.shutdown()
print("done")
