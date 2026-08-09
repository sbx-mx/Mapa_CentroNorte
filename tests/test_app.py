import json
import shutil
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

import app as application


class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=application.create_server(port=0)
        cls.port=cls.server.server_address[1]
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(timeout=2)

    def get(self,path):
        return urllib.request.urlopen(f'http://127.0.0.1:{self.port}{path}')

    def test_pages_and_api(self):
        for path in ['/mapa','/directorio','/administrar']:
            with self.get(path) as response:
                self.assertEqual(response.status,200)
                self.assertIn('Centro Norte',response.read().decode())
        with self.get('/api/stores') as response:
            payload=json.load(response)
        self.assertEqual(payload['metadata']['store_count'],len(payload['stores']))
        self.assertEqual(len(payload['stores']),72)

    def test_downloads(self):
        with self.get('/descargar/cms') as response:
            self.assertGreater(len(response.read()),10000)
        with self.get('/descargar/json') as response:
            self.assertIn(b'"stores"',response.read())

    def test_excel_upload_updates_json(self):
        boundary='----CentroNorteTestBoundary'
        xlsx=application.CMS_FILE.read_bytes()
        body=(
            f'--{boundary}\r\nContent-Disposition: form-data; name="token"\r\n\r\n\r\n'
            f'--{boundary}\r\nContent-Disposition: form-data; name="archivo"; filename="cms.xlsx"\r\n'
            'Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n'
        ).encode()+xlsx+f'\r\n--{boundary}--\r\n'.encode()
        with tempfile.TemporaryDirectory() as directory:
            original=application.DATA_FILE
            application.DATA_FILE=Path(directory)/'stores.json'
            shutil.copy2(original,application.DATA_FILE)
            try:
                request=urllib.request.Request(f'http://127.0.0.1:{self.port}/administrar/importar',data=body,method='POST',headers={'Content-Type':f'multipart/form-data; boundary={boundary}'})
                with urllib.request.urlopen(request) as response:
                    payload=json.load(response)
                self.assertTrue(payload['ok'])
                self.assertEqual(payload['metadata']['store_count'],72)
                self.assertTrue((Path(directory)/'backups').is_dir())
            finally:
                application.DATA_FILE=original


if __name__=='__main__': unittest.main()
