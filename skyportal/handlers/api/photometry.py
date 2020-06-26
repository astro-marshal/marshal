import uuid
import numpy as np
import arrow
import time as t
from astropy.table import Table
import pandas as pd
from marshmallow.exceptions import ValidationError
import sncosmo
from sncosmo.photdata import PhotometricData
from baselayer.app.access import permissions, auth_or_token
from ..base import BaseHandler
from ...models import (
    DBSession, Group, Photometry, Instrument, Source, Obj,
    PHOT_ZP, PHOT_SYS, GroupPhotometry
)

from baselayer.app.models import EXECUTEMANY_PAGESIZE

from ...schema import (PhotometryMag, PhotometryFlux, PhotFluxFlexible, PhotMagFlexible)
from ...phot_enum import ALLOWED_MAGSYSTEMS


def nan_to_none(value):
    """Coerce a value to None if it is nan, else return value."""
    try:
        return None if np.isnan(value) else value
    except TypeError:
        return value


def allscalar(d):
    return all(np.isscalar(v) or v is None for v in d.values())


def serialize(phot, outsys, format):

    retval = {
        'obj_id': phot.obj_id,
        'ra': phot.ra,
        'dec': phot.dec,
        'filter': phot.filter,
        'mjd': phot.mjd,
        'instrument_id': phot.instrument_id,
        'ra_unc': phot.ra_unc,
        'dec_unc': phot.dec_unc
    }

    filter = phot.filter

    magsys_db = sncosmo.get_magsystem('ab')
    outsys = sncosmo.get_magsystem(outsys)

    relzp_out = 2.5 * np.log10(outsys.zpbandflux(filter))

    # note: these are not the actual zeropoints for magnitudes in the db or
    # packet, just ones that can be used to derive corrections when
    # compared to relzp_out

    relzp_db = 2.5 * np.log10(magsys_db.zpbandflux(filter))
    db_correction = relzp_out - relzp_db

    # this is the zeropoint for fluxes in the database that is tied
    # to the new magnitude system
    corrected_db_zp = PHOT_ZP + db_correction

    if format == 'mag':
        if phot.original_user_data is not None and 'limiting_mag' in phot.original_user_data:
            magsys_packet = sncosmo.get_magsystem(phot.original_user_data['magsys'])
            relzp_packet = 2.5 * np.log10(magsys_packet.zpbandflux(filter))
            packet_correction = relzp_out - relzp_packet
            maglimit = phot.original_user_data['limiting_mag']
            maglimit_out = maglimit + packet_correction
        else:
            # calculate the limiting mag
            fluxerr = phot.fluxerr
            fivesigma = 5 * fluxerr
            maglimit_out = -2.5 * np.log10(fivesigma) + corrected_db_zp

        retval.update({
            'mag': phot.mag + db_correction if phot.mag is not None else None,
            'magerr': phot.e_mag if phot.e_mag is not None else None,
            'magsys': outsys.name,
            'limiting_mag': maglimit_out
        })
    elif format == 'flux':
        retval.update({
            'flux': phot.flux,
            'magsys': outsys.name,
            'zp': corrected_db_zp,
            'fluxerr': phot.fluxerr
        })
    else:
        raise ValueError('Invalid output format specified. Must be one of '
                         f"['flux', 'mag'], got '{format}'.")
    return retval


class PhotometryHandler(BaseHandler):
    @permissions(['Upload data'])
    def post(self):
        """
        ---
        description: Upload photometry
        requestBody:
          content:
            application/json:
              schema:
                oneOf:
                  - $ref: "#/components/schemas/PhotMagFlexible"
                  - $ref: "#/components/schemas/PhotFluxFlexible"
        responses:
          200:
            content:
              application/json:
                schema:
                  allOf:
                    - $ref: '#/components/schemas/Success'
                    - type: object
                      properties:
                        data:
                          type: object
                          properties:
                            ids:
                              type: array
                              items:
                                type: integer
                              description: List of new photometry IDs
                            upload_id:
                              type: string
                              description: |
                                Upload ID associated with all photometry points
                                added in request. Can be used to later delete all
                                points in a single request.
        """

        data = self.get_json()

        if not isinstance(data, dict):
            return self.error('Top level JSON must be an instance of `dict`, got '
                              f'{type(data)}.')
        if "altdata" in data and not data["altdata"]:
            del data["altdata"]

        # quick validation - just to make sure things have the right fields
        try:
            data = PhotMagFlexible.load(data)
        except ValidationError as e1:
            try:
                data = PhotFluxFlexible.load(data)
            except ValidationError as e2:
                return self.error('Invalid input format: Tried to parse data '
                                  f'in mag space, got: '
                                  f'"{e1.normalized_messages()}." Tried '
                                  f'to parse data in flux space, got:'
                                  f' "{e2.normalized_messages()}."')
            else:
                kind = 'flux'
        else:
            kind = 'mag'

        try:
            group_ids = data.pop("group_ids")
        except KeyError:
            return self.error("Missing required field: group_ids")
        groups = Group.query.filter(Group.id.in_(group_ids)).all()
        if not groups:
            return self.error("Invalid group_ids field. "
                              "Specify at least one valid group ID.")
        if "Super admin" not in [r.id for r in self.associated_user_object.roles]:
            if not all([group in self.current_user.groups for group in groups]):
                return self.error("Cannot upload photometry to groups that you "
                                  "are not a member of.")

        if allscalar(data):
            data = [data]

        upload_id = str(uuid.uuid4())

        start = t.time()

        try:
            df = pd.DataFrame(data)
        except ValueError as e:
            if "altdata" in data and "Mixing dicts with non-Series" in str(e):
                try:
                    data["altdata"] = [
                        {key: value[i] for key, value in data["altdata"].items()}
                        for i in range(len(data["altdata"][list(data["altdata"].keys())[-1]]))
                    ]
                    df = pd.DataFrame(data)
                except ValueError:
                    return self.error('Unable to coerce passed JSON to a series of packets. '
                                      f'Error was: "{e}"')
            else:
                return self.error('Unable to coerce passed JSON to a series of packets. '
                                  f'Error was: "{e}"')

        if kind == 'mag':
            # ensure that neither or both mag and magerr are null
            magnull = df['mag'].isna()
            magerrnull = df['magerr'].isna()
            magdet = ~magnull

            # https://en.wikipedia.org/wiki/Bitwise_operation#XOR
            bad = magerrnull ^ magnull  # bitwise exclusive or -- returns true
                                        #  if A and not B or B and not A

            if any(bad):
                # find the first offending packet
                first_offender = np.argwhere(bad)[0, 0]
                packet = df.iloc[first_offender].to_dict()

                # coerce nans to nones
                for key in packet:
                    packet[key] = nan_to_none(packet[key])

                return self.error(f'Error parsing packet "{packet}": mag '
                                  f'and magerr must both be null, or both be '
                                  f'not null.')

            # ensure nothing is null for the required fields
            for field in PhotMagFlexible.required_keys:
                missing = df[field].isna()
                if any(missing):
                    first_offender = np.argwhere(missing)[0, 0]
                    packet = df.iloc[first_offender].to_dict()

                    # coerce nans to nones
                    for key in packet:
                        packet[key] = nan_to_none(packet[key])

                    return self.error(f'Error parsing packet "{packet}": '
                                      f'missing required field {field}.')

            # convert the mags to fluxes
            # detections
            detflux = 10**(-0.4 * (df[magdet]['mag'] - PHOT_ZP))
            detfluxerr = df[magdet]['magerr'] / (2.5 / np.log(10)) * detflux

            # non-detections
            limmag_flux = 10**(-0.4 * (df[magnull]['limiting_mag'] - PHOT_ZP))
            ndetfluxerr = limmag_flux / df[magnull]['limiting_mag_nsigma']

            # initialize flux to be none
            phot_table = Table.from_pandas(df[['mjd', 'magsys', 'filter']])

            phot_table['zp'] = PHOT_ZP
            phot_table['flux'] = np.nan
            phot_table['fluxerr'] = np.nan
            phot_table['flux'][magdet] = detflux
            phot_table['fluxerr'][magdet] = detfluxerr
            phot_table['fluxerr'][magnull] = ndetfluxerr

        else:
            for field in PhotFluxFlexible.required_keys:
                missing = df[field].isna()
                if any(missing):
                    first_offender = np.argwhere(missing)[0, 0]
                    packet = df.iloc[first_offender].to_dict()

                    for key in packet:
                        packet[key] = nan_to_none(packet[key])

                    return self.error(f'Error parsing packet "{packet}": '
                                      f'missing required field {field}.')

            phot_table = Table.from_pandas(df[['mjd', 'magsys', 'filter', 'zp']])
            phot_table['flux'] = df['flux'].fillna(np.nan)
            phot_table['fluxerr'] = df['fluxerr'].fillna(np.nan)

        stop = t.time()

        print(f'Preprocessing took {stop - start:.3e} sec')

        start = t.time()

        # convert to microjanskies, AB for DB storage as a vectorized operation
        pdata = PhotometricData(phot_table)
        standardized = pdata.normalized(zp=PHOT_ZP, zpsys='ab')

        df['standardized_flux'] = standardized.flux
        df['standardized_fluxerr'] = standardized.fluxerr

        stop = t.time()

        print(f'Magsys switch took {stop - start:.3e} sec')

        start = t.time()

        phots = []
        for i, row in df.iterrows():
            packet = row.to_dict()

            # coerce nans to nones
            for key in packet:
                packet[key] = nan_to_none(packet[key])

            # check that the instrument and object exist
            instrument = Instrument.query.get(packet['instrument_id'])
            if not instrument:
                raise ValidationError(
                    f'Invalid instrument ID: {packet["instrument_id"]}')

            # get the object
            obj = Obj.query.get(
                packet['obj_id'])  # TODO : implement permissions checking
            if not obj:
                raise ValidationError(f'Invalid object ID: {packet["obj_id"]}')

            if packet["filter"] not in instrument.filters:
                raise ValidationError(
                    f"Instrument {instrument.name} has no filter "
                    f"{packet['filter']}.")

            flux = packet.pop('standardized_flux')
            fluxerr = packet.pop('standardized_fluxerr')

            phot = Photometry(original_user_data=packet,
                              groups=groups,
                              upload_id=upload_id,
                              flux=flux,
                              fluxerr=fluxerr,
                              obj_id=packet['obj_id'],
                              altdata=packet['altdata'],
                              instrument_id=packet['instrument_id'],
                              ra_unc=packet['ra_unc'],
                              dec_unc=packet['dec_unc'],
                              mjd=packet['mjd'],
                              filter=packet['filter'],
                              ra=packet['ra'],
                              dec=packet['dec'])

            phots.append(phot)
            #DBSession().add(phot)

        stop = t.time()

        print(f'postprocess took {stop - start:.3e} seconds', flush=True)

        #DBSession().bulk_save_objects(phots)
        #print(phots)

        start = t.time()

        query = Photometry.__table__.insert().returning(Photometry.id)
        params = [p.to_dict() for p in phots]

        # get the groups
        groups = []
        for p in params:
            groups.append(p.pop('groups'))

        #print('query= ', query)
        #print('params= ', params)

        i = 0
        ids = []
        while EXECUTEMANY_PAGESIZE * i < len(params):
            chunk_lo = EXECUTEMANY_PAGESIZE * i
            chunk_hi = EXECUTEMANY_PAGESIZE * (i + 1)
            subparams = params[chunk_lo:chunk_hi]
            result = DBSession().execute(query, subparams)
            ids.extend([i[0] for i in result])
            i += 1

        #print('result= ', result)
        #ids = result.inserted_primary_key

        """
        try:
            ids = 
        except:
            badq = query.compile(compile_kwargs={'literal_bind':True})
            print(f'Error was {badq}')
            raise
        """

        #ids = result
        #print('ids= ', ids)

        groupquery = GroupPhotometry.__table__.insert()
        params = []
        for id, groups in zip(ids, groups):
            for group in groups:
                params.append({'photometr_id': id, 'group_id': group.id})

        #print('groupquery= ', groupquery)
        DBSession().execute(groupquery, params)
        DBSession().commit()

        stop = t.time()

        print(f'insert took {stop - start:.3e} seconds', flush=True)

        return self.success(data={"ids": ids, "upload_id": upload_id})

    @auth_or_token
    def get(self, photometry_id):
        # The full docstring/API spec is below as an f-string

        phot = Photometry.get_if_owned_by(photometry_id, self.current_user)
        if phot is None:
            return self.error('Invalid photometry ID')

        # get the desired output format
        format = self.get_query_argument('format', 'mag')
        outsys = self.get_query_argument('magsys', 'ab')
        output = serialize(phot, outsys, format)
        return self.success(data=output)

    @permissions(['Manage sources'])
    def put(self, photometry_id):
        """
        ---
        description: Update photometry
        parameters:
          - in: path
            name: photometry_id
            required: true
            schema:
              type: integer
        requestBody:
          content:
            application/json:
              schema:
                oneOf:
                  - $ref: "#/components/schemas/PhotometryMag"
                  - $ref: "#/components/schemas/PhotometryFlux"
        responses:
          200:
            content:
              application/json:
                schema: Success
          400:
            content:
              application/json:
                schema: Error
        """
        _ = Photometry.get_if_owned_by(photometry_id, self.current_user)
        packet = self.get_json()
        group_ids = packet.pop("group_ids", None)

        try:
            phot = PhotometryFlux.load(packet)
        except ValidationError as e1:
            try:
                phot = PhotometryMag.load(packet)
            except ValidationError as e2:
                return self.error('Invalid input format: Tried to parse '
                                  f'{packet} as PhotometryFlux, got: '
                                  f'"{e1.normalized_messages()}." Tried '
                                  f'to parse {packet} as PhotometryMag, got:'
                                  f' "{e2.normalized_messages()}."')

        phot.original_user_data = packet
        phot.id = photometry_id
        DBSession().merge(phot)
        DBSession.flush()
        # Update groups, if relevant
        if group_ids is not None:
            photometry = Photometry.query.get(photometry_id)
            groups = Group.query.filter(Group.id.in_(group_ids)).all()
            if not groups:
                return self.error("Invalid group_ids field. "
                                  "Specify at least one valid group ID.")
            if "Super admin" not in [r.id for r in self.associated_user_object.roles]:
                if not all([group in self.current_user.groups for group in groups]):
                    return self.error("Cannot upload photometry to groups you "
                                      "are not a member of.")
            photometry.groups = groups
        DBSession().commit()
        return self.success()

    @permissions(['Manage sources'])
    def delete(self, photometry_id):
        """
        ---
        description: Delete photometry
        parameters:
          - in: path
            name: photometry_id
            required: true
            schema:
              type: integer
        responses:
          200:
            content:
              application/json:
                schema: Success
          400:
            content:
              application/json:
                schema: Error
        """
        _ = Photometry.get_if_owned_by(photometry_id, self.current_user)
        DBSession.query(Photometry).filter(Photometry.id == int(photometry_id)).delete()
        DBSession().commit()

        return self.success()


class ObjPhotometryHandler(BaseHandler):
    @auth_or_token
    def get(self, obj_id):
        obj = Obj.query.get(obj_id)
        if obj is None:
            return self.error('Invalid object id.')
        photometry = Obj.get_photometry_owned_by_user(obj_id, self.current_user)
        format = self.get_query_argument('format', 'mag')
        outsys = self.get_query_argument('magsys', 'ab')
        return self.success(
            data=[serialize(phot, outsys, format) for phot in photometry]
        )


class BulkDeletePhotometryHandler(BaseHandler):
    @auth_or_token
    def delete(self, upload_id):
        """
        ---
        description: Delete bulk-uploaded photometry set
        parameters:
          - in: path
            name: upload_id
            required: true
            schema:
              type: string
        responses:
          200:
            content:
              application/json:
                schema: Success
          400:
            content:
              application/json:
                schema: Error
        """
        # Permissions check:
        phot_id = Photometry.query.filter(
            Photometry.upload_id == upload_id).first().id
        _ = Photometry.get_if_owned_by(phot_id, self.current_user)

        n_deleted = DBSession.query(Photometry).filter(
            Photometry.upload_id == upload_id).delete()
        DBSession().commit()

        return self.success(f"Deleted {n_deleted} photometry points.")


PhotometryHandler.get.__doc__ = f"""
        ---
        description: Retrieve photometry
        parameters:
          - in: path
            name: photometry_id
            required: true
            schema:
              type: integer
          - in: query
            name: format
            required: false
            description: >-
              Return the photometry in flux or magnitude space?
              If a value for this query parameter is not provided, the
              result will be returned in magnitude space.
            schema:
              type: string
              enum:
                - mag
                - flux
          - in: query
            name: magsys
            required: false
            description: >-
              The magnitude or zeropoint system of the output. (Default AB)
            schema:
              type: string
              enum: {list(ALLOWED_MAGSYSTEMS)}

        responses:
          200:
            content:
              application/json:
                schema:
                  oneOf:
                    - $ref: "#/components/schemas/SinglePhotometryFlux"
                    - $ref: "#/components/schemas/SinglePhotometryMag"
          400:
            content:
              application/json:
                schema: Error
        """

ObjPhotometryHandler.get.__doc__ = f"""
        ---
        description: Retrieve all photometry associated with an Object
        parameters:
          - in: path
            name: obj_id
            required: true
            schema:
              type: string
            description: ID of the object to retrieve photometry for
          - in: query
            name: format
            required: false
            description: >-
              Return the photometry in flux or magnitude space?
              If a value for this query parameter is not provided, the
              result will be returned in magnitude space.
            schema:
              type: string
              enum:
                - mag
                - flux
          - in: query
            name: magsys
            required: false
            description: >-
              The magnitude or zeropoint system of the output. (Default AB)
            schema:
              type: string
              enum: {list(ALLOWED_MAGSYSTEMS)}

        responses:
          200:
            content:
              application/json:
                schema:
                  oneOf:
                    - $ref: "#/components/schemas/ArrayOfPhotometryFluxs"
                    - $ref: "#/components/schemas/ArrayOfPhotometryMags"
          400:
            content:
              application/json:
                schema: Error
        """
