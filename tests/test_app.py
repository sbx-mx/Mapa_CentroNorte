import json
import shutil
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

import app as application
from cms_service import synchronize_outputs


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
        dm_by_cc={item['cc']:item['dm'] for item in payload['stores']}
        self.assertEqual(dm_by_cc['38719'],'Veronica García')
        self.assertEqual(dm_by_cc['38894'],'Enrique César')

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
            original=(application.DATA_FILE,application.CMS_FILE,application.LEGACY_CSV_FILE)
            application.DATA_FILE=Path(directory)/'stores.json'
            application.CMS_FILE=Path(directory)/'cms.xlsx'
            application.LEGACY_CSV_FILE=Path(directory)/'data.csv'
            shutil.copy2(original[0],application.DATA_FILE)
            shutil.copy2(original[1],application.CMS_FILE)
            shutil.copy2(original[2],application.LEGACY_CSV_FILE)
            stale=json.loads(application.DATA_FILE.read_text(encoding='utf-8'))
            stale_by_cc={item['cc']:item for item in stale['stores']}
            stale_by_cc['38719']['dm']='Vanessa Carreño'
            stale_by_cc['38894']['dm']='Nancy Rodríguez'
            application.DATA_FILE.write_text(json.dumps(stale,ensure_ascii=False),encoding='utf-8')
            application.LEGACY_CSV_FILE.write_text('base desactualizada',encoding='utf-8')
            try:
                request=urllib.request.Request(f'http://127.0.0.1:{self.port}/administrar/importar',data=body,method='POST',headers={'Content-Type':f'multipart/form-data; boundary={boundary}'})
                with urllib.request.urlopen(request) as response:
                    payload=json.load(response)
                self.assertTrue(payload['ok'])
                self.assertEqual(payload['metadata']['store_count'],72)
                self.assertTrue((Path(directory)/'backups').is_dir())
                self.assertEqual(application.CMS_FILE.read_bytes(),xlsx)
                updated={item['cc']:item['dm'] for item in json.loads(application.DATA_FILE.read_text(encoding='utf-8'))['stores']}
                self.assertEqual(updated['38719'],'Veronica García')
                self.assertEqual(updated['38894'],'Enrique César')
            finally:
                application.DATA_FILE,application.CMS_FILE,application.LEGACY_CSV_FILE=original

    def test_direct_sync_fixes_dm_distribution(self):
        with tempfile.TemporaryDirectory() as directory:
            database=Path(directory)/'stores.json'
            legacy=Path(directory)/'data.csv'
            stale=json.loads(application.DATA_FILE.read_text(encoding='utf-8'))
            by_cc={item['cc']:item for item in stale['stores']}
            by_cc['38719']['dm']='Vanessa Carreño'
            by_cc['38894']['dm']='Nancy Rodríguez'
            database.write_text(json.dumps(stale,ensure_ascii=False),encoding='utf-8')
            legacy.write_text('base desactualizada',encoding='utf-8')
            payload,changed=synchronize_outputs(application.CMS_FILE,database,legacy)
            self.assertEqual(len(changed),2)
            corrected={item['cc']:item['dm'] for item in payload['stores']}
            self.assertEqual(corrected['38719'],'Veronica García')
            self.assertEqual(corrected['38894'],'Enrique César')
            check_payload,pending=synchronize_outputs(application.CMS_FILE,database,legacy,dry_run=True)
            self.assertEqual(pending,[])
            self.assertEqual(check_payload['stores'],payload['stores'])


if __name__=='__main__': unittest.main()
