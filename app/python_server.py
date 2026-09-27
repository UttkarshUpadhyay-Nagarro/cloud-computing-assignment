import json
import os
import subprocess
import uuid
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
BUCKET = os.environ["UPLOAD_BUCKET"]
REGION = os.environ.get("AWS_REGION", "ap-south-1")


class Handler(BaseHTTPRequestHandler):
    CONTENT_TYPES = {
        ".html": "text/html",
        ".css": "text/css",
        ".js": "application/javascript",
    }

    def do_GET(self):
        path = "/index.html" if self.path == "/" else self.path
        public_root = (ROOT / "public").resolve()
        file_path = (public_root / path.lstrip("/")).resolve()
        if public_root not in file_path.parents or not file_path.is_file():
            self.send_error(404)
            return
        content_type = self.CONTENT_TYPES.get(file_path.suffix, "application/octet-stream")
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/upload":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        message = BytesParser(policy=policy.default).parsebytes(
            b"Content-Type: " + self.headers["Content-Type"].encode() + b"\r\n\r\n" + raw
        )
        parts = message.iter_parts() if message.is_multipart() else []
        document = next((part for part in parts if part.get_param("name", header="content-disposition") == "document"), None)
        if document is None or not document.get_filename():
            self.respond({"error": "Choose a file first"}, 400)
            return
        key = f"uploads/{uuid.uuid4()}-{Path(document.get_filename()).name}"
        body = document.get_payload(decode=True)
        command = ["aws", "s3", "cp", "-", f"s3://{BUCKET}/{key}", "--region", REGION, "--content-type", document.get_content_type()]
        result = subprocess.run(command, input=body, capture_output=True)
        if result.returncode != 0:
            self.respond({"error": "Upload failed"}, 500)
            return
        self.respond({"fileName": document.get_filename(), "key": key, "message": "Upload complete"}, 200)

    def respond(self, value, status):
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "3000"))), Handler).serve_forever()