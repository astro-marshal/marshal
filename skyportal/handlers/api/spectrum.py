from marshmallow.exceptions import ValidationError
from baselayer.app.access import permissions, auth_or_token
from ..base import BaseHandler
from ...models import DBSession, Spectrum, Instrument, Source, Candidate


class SpectrumHandler(BaseHandler):
    @permissions(['Upload data'])
    def post(self):
        """
        ---
        description: Upload spectrum
        requestBody:
          content:
            application/json:
              schema: SpectrumNoID
        responses:
          200:
            content:
              application/json:
                schema:
                  allOf:
                    - Success
                    - type: object
                      properties:
                        id:
                          type: integer
                          description: New spectrum ID
          400:
            content:
              application/json:
                schema: Error
        """
        data = self.get_json()
        source_id = data.pop('source_id', None)
        candidate_id = data.pop('candidate_id', None)
        source = (Source.get_if_owned_by(source_id, self.current_user)
                  if source_id is not None else None)
        candidate = (Candidate.get_if_owned_by(candidate_id, self.current_user)
                     if candidate_id is not None else None)
        instrument_id = data.pop('instrument_id')
        instrument = Instrument.query.get(instrument_id)

        schema = Spectrum.__schema__()
        try:
            spec = schema.load(data)
        except ValidationError as e:
            return self.error('Invalid/missing parameters: '
                              f'{e.normalized_messages()}')
        if source is not None:
            spec.source = source
        if candidate is not None:
            spec.candidate = candidate
        spec.instrument = instrument
        DBSession().add(spec)
        DBSession().commit()

        return self.success(data={"id": spec.id})

    @auth_or_token
    def get(self, spectrum_id):
        """
        ---
        description: Retrieve a spectrum
        parameters:
          - in: path
            name: spectrum_id
            required: true
            schema:
              type: integer
        responses:
          200:
            content:
              application/json:
                schema: SingleSpectrum
          400:
            content:
              application/json:
                schema: Error
        """
        spectrum = Spectrum.query.get(spectrum_id)

        if spectrum is None:
            return self.error(f"Could not load spectrum {spectrum_id}",
                              data={"spectrum_id": spectrum_id})
        # Ensure user/token has access to parent source/candidate
        try:
            _ = Source.get_if_owned_by(spectrum.source_id, self.current_user)
        except (ValueError, AttributeError, TypeError):
            _ = Candidate.get_if_owned_by(spectrum.candidate_id, self.current_user)

        return self.success(data={'spectrum': spectrum})


    @permissions(['Manage sources'])
    def put(self, spectrum_id):
        """
        ---
        description: Update spectrum
        parameters:
          - in: path
            name: spectrum_id
            required: true
            schema:
              type: integer
        requestBody:
          content:
            application/json:
              schema: SpectrumNoID
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
        spectrum = Spectrum.query.get(spectrum_id)
        # Ensure user/token has access to parent source/candidate
        try:
            _ = Source.get_if_owned_by(spectrum.source_id, self.current_user)
        except (ValueError, AttributeError, TypeError):
            _ = Candidate.get_if_owned_by(spectrum.candidate_id, self.current_user)
        data = self.get_json()
        data['id'] = spectrum_id

        schema = Spectrum.__schema__()
        try:
            schema.load(data)
        except ValidationError as e:
            return self.error('Invalid/missing parameters: '
                              f'{e.normalized_messages()}')
        DBSession().commit()

        return self.success()

    @permissions(['Manage sources'])
    def delete(self, spectrum_id):
        """
        ---
        description: Delete a spectrum
        parameters:
          - in: path
            name: spectrum_id
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
        spectrum = Spectrum.query.get(spectrum_id)
        # Ensure user/token has access to parent source/candidate
        try:
            _ = Source.get_if_owned_by(spectrum.source_id, self.current_user)
        except (ValueError, AttributeError, TypeError):
            _ = Candidate.get_if_owned_by(spectrum.candidate_id, self.current_user)
        DBSession().delete(spectrum)
        DBSession().commit()

        return self.success()
