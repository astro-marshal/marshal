import datetime
import os
from pathlib import Path
import shutil
import pandas as pd
import base64

from baselayer.app.env import load_env
from baselayer.app.model_util import status, create_tables, drop_tables
from social_tornado.models import TornadoStorage
from skyportal.models import (init_db, Base, DBSession, Comment,
                              Instrument, Group, GroupUser, Photometry,
                              Source, Spectrum, Telescope, Thumbnail, User)
from skyportal.model_util import setup_permissions


if __name__ == "__main__":
    """Insert test data"""
    env, cfg = load_env()
    basedir = Path(os.path.dirname(__file__))/'..'

    with status(f"Connecting to database {cfg['database']['database']}"):
        init_db(**cfg['database'])

    with status("Dropping all tables"):
        drop_tables()

    with status("Creating tables"):
        create_tables()

    for model in Base.metadata.tables:
        print('    -', model)

    with status(f"Creating permissions"):
        setup_permissions()

    with status(f"Creating dummy users"):
        g = Group(name='Stream A')
        super_admin_user = User(username='testuser@cesium-ml.org',
                                role_ids=['Super admin'])
        group_admin_user = User(username='groupadmin@cesium-ml.org',
                                role_ids=['Super admin'])
        DBSession().add_all(
            [GroupUser(group=g, user=super_admin_user, admin=True),
             GroupUser(group=g, user=group_admin_user, admin=True)]
        )
        full_user = User(username='fulluser@cesium-ml.org',
                         role_ids=['Full user'], groups=[g])
        view_only_user = User(username='viewonlyuser@cesium-ml.org',
                              role_ids=['View only'], groups=[g])
        DBSession().add_all([super_admin_user, group_admin_user,
                             full_user, view_only_user])

        for u in [super_admin_user, group_admin_user, full_user, view_only_user]:
            DBSession().add(TornadoStorage.user.create_social_auth(u, u.username,
                                                                   'google-oauth2'))

    with status("Creating dummy instruments"):
        t1 = Telescope(name='Palomar 1.5m', nickname='P60',
                       lat=33.3633675, lon=-116.8361345, elevation=1870,
                       diameter=1.5, groups=[g])
        i1 = Instrument(telescope=t1, name='P60 Camera', type='phot',
                        band='optical')

        t2 = Telescope(name='Nordic Optical Telescope', nickname='NOT',
                       lat=28.75, lon=17.88, elevation=2327,
                       diameter=2.56, groups=[g])
        i2 = Instrument(telescope=t2, name='ALFOSC', type='both',
                        band='optical')
        DBSession().add_all([i1, i2])

    with status("Creating dummy sources"):
        SOURCES = [{'id': '14gqr', 'ra': 353.36647, 'dec': 33.646149, 'redshift': 0.063,
                    'comments': ["No source at transient location to R>26 in LRIS imaging",
                                 "Strong calcium lines have emerged."]},
                   {'id': '16fil', 'ra': 322.718872, 'dec': 27.574113, 'redshift': 0.0,
                    'comments': ["Frogs in the pond", "The eagle has landed"]}]

        (basedir/'static/thumbnails').mkdir(parents=True, exist_ok=True)
        for source_info in SOURCES:
            comments = source_info.pop('comments')

            s = Source(**source_info, groups=[g])
            s.comments = [Comment(text=comment, author=group_admin_user.username)
                          for comment in comments]

            phot_file = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                     'skyportal', 'tests', 'data',
                                     'phot.csv')
            phot_data = pd.read_csv(phot_file)
            s.photometry = [Photometry(instrument=i1, **row)
                            for j, row in phot_data.iterrows()]

            spec_file = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                     'skyportal', 'tests', 'data',
                                     'spec.csv')
            spec_data = pd.read_csv(spec_file)
            s.spectra = [Spectrum(instrument_id=int(i),
                                  observed_at=datetime.datetime(2014, 10, 24),
                                  wavelengths=df.wavelength,
                                  fluxes=df.flux, errors=None)
                         for i, df in spec_data.groupby('instrument_id')]
            DBSession().add(s)
            DBSession().commit()

            for ttype in ['new', 'ref', 'sub']:
                fname = f'{s.id}_{ttype}.png'
                file_path = os.path.abspath(basedir/f'skyportal/tests/data/{fname}')
                im = base64.b64encode(open(file_path, 'rb').read())
                t = Thumbnail(type=ttype, photometry_id=s.photometry[0].id,
                              image=im,
                              public_url=f'/static/thumbnails/{fname}')
                DBSession().add(t)

            s.add_linked_thumbnails()
