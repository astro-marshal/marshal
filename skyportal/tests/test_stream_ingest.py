import time
import os
import shutil
import subprocess
import inspect
import requests

import baselayer
from baselayer.app.config import load_config
from baselayer.app.model_util import clear_tables
from skyportal.models import init_db, Token, Source, Telescope, Instrument, Photometry, DBSession
from skyportal.model_util import create_token, load_demo_data


def test_stream_ingest():
    #skyportal_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    skyportal_root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(inspect.getsourcefile(lambda:0)))))
    print(skyportal_root)
    os.chdir(skyportal_root)
    print("\n\ncwd:", os.getcwd(), "\n\n")
    cfg = load_config([os.path.join(skyportal_root, 'test_config.yaml')])
    load_demo_data(cfg)
    # Retrieve or generate token for SkyPortal API auth
    token = Token.query.filter(Token.name == 'alert_stream_token').first()
    if not token:
        token = create_token(1, ['Upload data'], name='alert_stream_token')
    else:
        token = token.id

    r = requests.get('http://localhost:5000/api/sources',
                     headers={'Authorization': f'token {token}'})
    print(r.json())
    assert len(r.json()['data']['sources']) == 2
    proc = subprocess.Popen("make alert_stream_demo",
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True)

    for i in range(120):
        out = str(proc.stdout.readline())
        r = requests.get('http://localhost:5000/api/sources',
                         headers={'Authorization': f'token {token}'})
        n_sources = len(r.json()['data']['sources'])
        if n_sources > 2:
            print("\n\n\n\nYES!!!!!!!!!!\n\n\n\n")
            proc.terminate()
            #clear_tables()
            break
        else:
            print("\n\n\nNot yet...", out, "\n\n\n")
            time.sleep(2)
    else:
        print('Stream ingestion test failed - no ouput indicating success.')
        print(out)
        proc.terminate()
        clear_tables()
        raise Exception('test failed...')


if __name__ == '__main__':
    test_stream_ingest()
