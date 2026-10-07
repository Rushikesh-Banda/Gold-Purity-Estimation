from backend.server import handle, config
from wsgiref.simple_server import make_server
import os
if __name__ == "__main__":
    config.ensure_directories()
    port=int(os.environ.get("PORT","8000"))
    print(f"Open http://127.0.0.1:{port}")
    make_server("127.0.0.1",port,handle).serve_forever()
