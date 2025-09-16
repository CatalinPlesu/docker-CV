#!/usr/bin/env python3
import os
import json
import tempfile
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LaTeXHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/compile':
            self.handle_compile()
        else:
            self.send_error(404)

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'healthy'}).encode())
        else:
            self.send_error(404)

    def handle_compile(self):
        try:
            # Get content length
            content_length = int(self.headers['Content-Length'])

            # Read the request body
            post_data = self.rfile.read(content_length)

            # Parse JSON
            try:
                data = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError as e:
                self.send_json_error(400, "Invalid JSON: " + str(e))
                return

            # Validate request
            if 'latex' not in data:
                self.send_json_error(400, "Missing 'latex' field in request")
                return

            latex_content = data['latex']
            if not latex_content or not isinstance(latex_content, str):
                self.send_json_error(
                    400, "LaTeX content must be a non-empty string")
                return

            logger.info("Received LaTeX compilation request (" +
                        str(len(latex_content)) + " characters)")

            # Compile LaTeX to PDF
            pdf_data = self.compile_latex(latex_content)

            # Send PDF response
            self.send_response(200)
            self.send_header('Content-Type', 'application/pdf')
            self.send_header('Content-Length', str(len(pdf_data)))
            self.end_headers()
            self.wfile.write(pdf_data)

            logger.info("PDF compilation completed successfully")

        except Exception as e:
            logger.error("Compilation error: " + str(e))
            self.send_json_error(500, "Compilation failed: " + str(e))

    def compile_latex(self, latex_content):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write LaTeX content to file
            tex_file = os.path.join(temp_dir, 'document.tex')
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)

            # Run pdflatex
            cmd = [
                'pdflatex',
                '-interaction=nonstopmode',
                '-output-directory', temp_dir,
                tex_file
            ]

            logger.info("Running: " + ' '.join(cmd))

            try:
                result = subprocess.run(
                    cmd,
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=30  # 30 second timeout
                )
            except subprocess.TimeoutExpired:
                raise Exception("LaTeX compilation timed out after 30 seconds")

            if result.returncode != 0:
                logger.error("pdflatex failed with return code " +
                             str(result.returncode))
                logger.error("stdout: " + result.stdout)
                logger.error("stderr: " + result.stderr)
                raise Exception("pdflatex failed: " + result.stderr)

            # Read the generated PDF
            pdf_file = os.path.join(temp_dir, 'document.pdf')
            if not os.path.exists(pdf_file):
                raise Exception("PDF file was not generated")

            with open(pdf_file, 'rb') as f:
                pdf_data = f.read()

            logger.info("Generated PDF (" + str(len(pdf_data)) + " bytes)")
            return pdf_data

    def send_json_error(self, code, message):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        error_response = json.dumps({'error': message})
        self.wfile.write(error_response.encode())

    def log_message(self, format, *args):
        # Override to use our logger instead of stderr
        logger.info(self.address_string() + " - " + (format % args))


def main():
    port = int(os.environ.get('PORT', 3001))
    server = HTTPServer(('0.0.0.0', port), LaTeXHandler)
    logger.info("LaTeX compilation server starting on port " + str(port))

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        server.shutdown()


if __name__ == '__main__':
    main()
