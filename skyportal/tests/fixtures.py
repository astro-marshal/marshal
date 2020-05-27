import datetime
from itertools import cycle, islice
import uuid
from tempfile import mkdtemp
import numpy as np
import factory
from skyportal.models import (DBSession, User, Group, Photometry,
                              Spectrum, Instrument, Telescope, Obj,
                              Comment, Thumbnail, Filter)

TMP_DIR = mkdtemp()


class BaseMeta:
    sqlalchemy_session = DBSession()
    sqlalchemy_session_persistence = 'commit'


class TelescopeFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta(BaseMeta):
        model = Telescope

    name = 'Test telescope'
    nickname = 'test_scope'
    lat = 0.0
    lon = 0.0
    elevation = 0.0
    diameter = 1.0


class CommentFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta(BaseMeta):
        model = Comment

    text = f'Test comment {str(uuid.uuid4())}'
    ctype = 'text'
    author = 'test factory'


class InstrumentFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta(BaseMeta):
        model = Instrument

    name = 'Test instrument'
    type = 'Type 1'
    band = 'Band 1'
    telescope = factory.SubFactory(TelescopeFactory)


class PhotometryFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta(BaseMeta):
        model = Photometry

    instrument = factory.SubFactory(InstrumentFactory)
    mjd = factory.LazyFunction(lambda: 58000. + np.random.random())
    flux = factory.LazyFunction(lambda: 20 + 10 * np.random.random())
    fluxerr = factory.LazyFunction(lambda: 2 * np.random.random())

    zp = factory.LazyFunction(lambda: 25. + 1 * np.random.random())
    zpsys = 'ab'


class ThumbnailFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta(BaseMeta):
        model = Thumbnail

    type = 'new'


class SpectrumFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta(BaseMeta):
        model = Spectrum

    instrument = factory.SubFactory(InstrumentFactory)
    wavelengths = np.sort(1000 * np.random.random(10))
    fluxes = 1e-9 * np.random.random(len(wavelengths))
    observed_at = datetime.datetime.now()


class GroupFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta(BaseMeta):
        model = Group
    name = factory.LazyFunction(lambda: str(uuid.uuid4()))
    users = []


class FilterFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta(BaseMeta):
        model = Filter
    query_string = str(uuid.uuid4())


class ObjFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta(BaseMeta):
        model = Obj
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    ra = 0.0
    dec = 0.0
    redshift = 0.0
    altdata = {"simbad": {"class": "RRLyr"}}

    @factory.post_generation
    def add_phot_spec(obj, create, value, *args, **kwargs):
        instruments = [InstrumentFactory(), InstrumentFactory()]
        filters = ['ztfg', 'ztfr', 'ztfi']
        for instrument, filter in islice(zip(cycle(instruments), cycle(filters)), 10):
            phot1 = PhotometryFactory(obj_id=obj.id,
                                      instrument=instrument,
                                      filter=filter)
            DBSession().add(phot1)
            DBSession().add(PhotometryFactory(obj_id=obj.id, flux=99.,
                                              fluxerr=99., zp=25., zpsys='ab',
                                              instrument=instrument,
                                              filter=filter))

            DBSession().add(ThumbnailFactory(photometry=phot1))
            DBSession().add(CommentFactory(obj_id=obj.id))
        DBSession().add(SpectrumFactory(obj_id=obj.id,
                                        instrument=instruments[0]))
        DBSession().commit()


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta(BaseMeta):
        model = User

    username = factory.LazyFunction(lambda: f'{uuid.uuid4()}@cesium-ml.org')

    @factory.post_generation
    def roles(obj, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for role in extracted:
                obj.roles.append(role)
                DBSession().add(obj)
                DBSession().commit()

    @factory.post_generation
    def groups(obj, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for group in extracted:
                obj.groups.append(group)
                DBSession().add(obj)
                DBSession().commit()
