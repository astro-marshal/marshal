"""Test fixture configuration."""

import pytest
import os
import uuid
import pathlib
from psycopg2 import OperationalError
from baselayer.app import models
from baselayer.app.config import load_config
from baselayer.app.test_util import (
    driver,
    MyCustomWebDriver,
    set_server_url,
    reset_state,
)
from skyportal.tests.fixtures import (
    TMP_DIR,
    ObjFactory,
    GroupFactory,
    UserFactory,
    FilterFactory,
    InstrumentFactory,
    ObservingRunFactory,
    TelescopeFactory
)
from skyportal.model_util import create_token
from skyportal.models import DBSession, Source, Candidate, Role
import astroplan


print("Loading test configuration from _test_config.yaml")
basedir = pathlib.Path(os.path.dirname(__file__))
cfg = load_config([(basedir / "../../test_config.yaml").absolute()])
set_server_url(f'http://localhost:{cfg["ports.app"]}')
print("Setting test database to:", cfg["database"])
models.init_db(**cfg["database"])


@pytest.fixture()
def public_group():
    return GroupFactory()


@pytest.fixture()
def public_filter(public_group):
    return FilterFactory(group=public_group)


@pytest.fixture()
def public_source(public_group):
    obj = ObjFactory()
    DBSession.add(Source(obj_id=obj.id, group_id=public_group.id))
    DBSession.commit()
    return obj


@pytest.fixture()
def public_candidate(public_filter):
    obj = ObjFactory()
    DBSession.add(Candidate(obj=obj, filter=public_filter))
    DBSession.commit()
    return obj

@pytest.fixture()
def ztf_camera():
    return InstrumentFactory()


@pytest.fixture()
def red_transients_group(group_admin_user, view_only_user):
    return GroupFactory(name=f'red transients-{uuid.uuid4().hex}',
                        users=[group_admin_user,
                               view_only_user])

@pytest.fixture()
def ztf_camera():
    return InstrumentFactory()


@pytest.fixture()
def keck1_telescope():
    observer = astroplan.Observer.at_site('Keck')
    return TelescopeFactory(name='Keck I Telescope',
                            nickname='Keck1',
                            lat=observer.location.lat.to('deg').value,
                            lon=observer.location.lon.to('deg').value,
                            elevation=observer.location.height.to('m').value,
                            diameter=10.)

@pytest.fixture()
def p60_telescope():
    observer = astroplan.Observer.at_site('Palomar')
    return TelescopeFactory(name='Palomar 60-inch telescope',
                            nickname='p60',
                            lat=observer.location.lat.to('deg').value,
                            lon=observer.location.lon.to('deg').value,
                            elevation=observer.location.height.to('m').value,
                            diameter=1.6)


@pytest.fixture()
def lris(keck1_telescope):
    return InstrumentFactory(name='LRIS', type='imaging spectrograph',
                             robotic=False, telescope=keck1_telescope,
                             band='Optical', filters=['sdssu', 'sdssg',
                                                      'sdssr', 'sdssi',
                                                      'sdssz', 'bessellux',
                                                      'bessellv', 'bessellb',
                                                      'bessellr', 'besselli'])

@pytest.fixture()
def sedm(p60_telescope):
    return InstrumentFactory(name='SEDM', type='imaging spectrograph',
                             robotic=True, telescope=p60_telescope,
                             band='Optical', filters=['sdssu', 'sdssg', 'sdssr',
                                                      'sdssi'])

@pytest.fixture()
def red_transients_run():
    return ObservingRunFactory()


@pytest.fixture()
def private_source():
    return ObjFactory()


@pytest.fixture()
def user(public_group):
    return UserFactory(
        groups=[public_group], roles=[models.Role.query.get("Full user")]
    )


@pytest.fixture()
def view_only_user(public_group):
    return UserFactory(
        groups=[public_group], roles=[models.Role.query.get("View only")]
    )


@pytest.fixture()
def group_admin_user(public_group):
    return UserFactory(
        groups=[public_group], roles=[models.Role.query.get("Group admin")]
    )


@pytest.fixture()
def super_admin_user(public_group):
    return UserFactory(
        groups=[public_group], roles=[models.Role.query.get("Super admin")]
    )


@pytest.fixture()
def view_only_token(user):
    token_id = create_token(
        permissions=[], created_by_id=user.id, name=str(uuid.uuid4())
    )
    return token_id


@pytest.fixture()
def manage_sources_token(group_admin_user):
    token_id = create_token(
        permissions=["Manage sources"],
        created_by_id=group_admin_user.id,
        name=str(uuid.uuid4()),
    )
    return token_id


@pytest.fixture()
def upload_data_token(user):
    token_id = create_token(
        permissions=["Upload data"], created_by_id=user.id, name=str(uuid.uuid4())
    )
    return token_id


@pytest.fixture()
def manage_groups_token(super_admin_user):
    token_id = create_token(
        permissions=["Manage groups"],
        created_by_id=super_admin_user.id,
        name=str(uuid.uuid4()),
    )
    return token_id


@pytest.fixture()
def manage_users_token(super_admin_user):
    token_id = create_token(
        permissions=["Manage users"],
        created_by_id=super_admin_user.id,
        name=str(uuid.uuid4()),
    )
    return token_id


@pytest.fixture()
def super_admin_token(super_admin_user):
    role = Role.query.get('Super admin')
    token_id = create_token(
        permissions=[a.id for a in role.acls],
        created_by_id=super_admin_user.id,
        name=str(uuid.uuid4()),
    )
    return token_id


@pytest.fixture()
def comment_token(user):
    token_id = create_token(
        permissions=["Comment"], created_by_id=user.id, name=str(uuid.uuid4())
    )
    return token_id
