#!/usr/bin/env python3
import os
import sys
import json
import tempfile
import subprocess
import signal
from http.server import HTTPServer, BaseHTTPRequestHandler


class LaTeXHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/compile':
            self.handle_compile()
        else:
            self.send_error(404)

    def handle_compile(self):
        try:
            # Get content length
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            # Parse JSON data
            data = json.loads(post_data.decode('utf-8'))
            latex_content = data.get('latex_content')

            if not latex_content:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_response = json.dumps(
                    {'error': 'No LaTeX content provided'})
                self.wfile.write(error_response.encode('utf-8'))
                return

            # Compile LaTeX with timeout
            pdf_data = self.compile_latex_with_timeout(
                latex_content, timeout=60)

            # Send success response
            self.send_response(200)
            self.send_header('Content-Type', 'application/pdf')
            self.send_header('Content-Length', str(len(pdf_data)))
            self.end_headers()
            self.wfile.write(pdf_data)

        except subprocess.TimeoutExpired:
            self.send_response(408)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({'error': 'Compilation timeout'})
            self.wfile.write(error_response.encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({'error': 'Compilation failed'})
            self.wfile.write(error_response.encode('utf-8'))

    def compile_latex_with_timeout(self, latex_content, timeout=60):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write LaTeX file as cv.tex
            tex_file = os.path.join(temp_dir, 'cv.tex')
            with open(tex_file, 'w') as f:
                f.write(latex_content)

            # Prepare pdflatex command
            cmd = [
                'pdflatex',
                '-interaction=nonstopmode',
                '-output-directory', temp_dir,
                tex_file
            ]

            # Run with timeout
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )

                if result.returncode != 0:
                    raise Exception('pdflatex failed')

                # Read PDF
                pdf_file = os.path.join(temp_dir, 'cv.pdf')
                if not os.path.exists(pdf_file):
                    raise Exception('PDF not generated')

                with open(pdf_file, 'rb') as f:
                    return f.read()

            except subprocess.TimeoutExpired:
                raise subprocess.TimeoutExpired(cmd, timeout)

    def log_message(self, format, *args):
        # Disable default logging
        pass


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3001))
    server = HTTPServer(('0.0.0.0', port), LaTeXHandler)
    print(f"LaTeX service running on port {port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
