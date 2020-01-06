import base64
import cgi
import os
from http.server import BaseHTTPRequestHandler


class PostHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        # Parse the form data posted
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers,
            environ={
                'REQUEST_METHOD': 'POST',
                'CONTENT_TYPE': self.headers['Content-Type'],
                }
            )

        # Begin the response
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write('{"success": true}'.encode('utf-8'))

        print('Client: {}\n'.format(self.client_address))
        print('User-agent: {}\n'.format(self.headers['user-agent']))
        print('Path: {}\n'.format(self.path))
        print('Form data:\n')

        # Echo back information about what was posted in the form
        for field in form.keys():
            if field == 'content_file':
                print('Writing file : %s' % form['name_file'].value)
                with open(os.path.basename(form['name_file'].value),
                        'wb') as fp:
                    fp.write(base64.b64decode(form['content_file'].value))
                continue

            field_item = form[field]
            if field_item.filename:
                # The field contains an uploaded file
                file_data = field_item.file.read()
                file_len = len(file_data)
                del file_data
                print(
                    '\tUploaded {} as {!r} ({} bytes)\n'.format(
                        field, field_item.filename, file_len)
                    )
            else:
                # Regular form value
                print('\t{}={}\n'.format(field, form[field].value))


if __name__ == '__main__':
    from http.server import HTTPServer
    server = HTTPServer(('localhost', 7766), PostHandler)
    print('Starting server, use <Ctrl-C> to stop')
    server.serve_forever()
