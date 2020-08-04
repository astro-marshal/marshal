from marshmallow.exceptions import ValidationError
from baselayer.app.access import permissions, auth_or_token
from ..base import BaseHandler
from ...models import DBSession, Telescope, Group


class TelescopeHandler(BaseHandler):
    @permissions(['Upload data'])
    def post(self):
        """
        ---
        description: Create telescopes
        requestBody:
          content:
            application/json:
              schema:
                allOf:
                  - $ref: '#/components/schemas/TelescopeNoID'
                  - type: object
                    properties:
                      group_ids:
                        type: array
                        items:
                          type: integer
                        description: List of group IDs to associate the telescope with
                    required:
                      - group_ids
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
                            id:
                              type: integer
                              description: New telescope ID
          400:
            content:
              application/json:
                schema: Error
        """
        data = self.get_json()
        group_ids = data.pop('group_ids')
        groups = [g for g in Group.query.filter(Group.id.in_(group_ids)).all()
                  if g in self.current_user.accessible_groups]
        if not groups:
            return self.error('You must specify at least one group of which you '
                              'are a member.')
        schema = Telescope.__schema__()

        try:
            telescope = schema.load(data)
        except ValidationError as e:
            return self.error('Invalid/missing parameters: '
                              f'{e.normalized_messages()}')
        telescope.groups = groups
        DBSession().add(telescope)
        DBSession().commit()

        return self.success(data={"id": telescope.id})

    @auth_or_token
    def get(self, telescope_id):
        """
        ---
        description: Retrieve a telescope
        parameters:
          - in: path
            name: telescope_id
            required: true
            schema:
              type: integer
        responses:
          200:
            content:
              application/json:
                schema: SingleTelescope
          400:
            content:
              application/json:
                schema: Error
        """
        t = Telescope.get_if_owned_by(int(telescope_id), self.current_user)

        if t is not None:
            return self.success(data=t)
        else:
            return self.error(f"Could not load telescope with ID {telescope_id}")

    @permissions(['Manage sources'])
    def put(self, telescope_id):
        """
        ---
        description: Update telescope
        parameters:
          - in: path
            name: telescope_id
            required: true
            schema:
              type: integer
        requestBody:
          content:
            application/json:
              schema: TelescopeNoID
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
        t = Telescope.get_if_owned_by(int(telescope_id), self.current_user)
        data = self.get_json()
        data['id'] = int(telescope_id)

        schema = Telescope.__schema__()
        try:
            schema.load(data)
        except ValidationError as e:
            return self.error('Invalid/missing parameters: '
                              f'{e.normalized_messages()}')
        DBSession().commit()

        return self.success()

    @permissions(['Manage sources'])
    def delete(self, telescope_id):
        """
        ---
        description: Delete a telescope
        parameters:
          - in: path
            name: telescope_id
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
        t = Telescope.get_if_owned_by(int(telescope_id), self.current_user)
        DBSession().query(Telescope).filter(Telescope.id == int(telescope_id)).delete()
        DBSession().commit()

        return self.success()


class TelescopeByNameHandler(BaseHandler):
    @auth_or_token
    def get(self, telescope_name):
        """
        ---
        description: Retrieve a telescope by name
        parameters:
          - in: path
            name: telescope_name
            required: true
            schema:
              type: string
        responses:
          200:
            content:
              application/json:
                schema: SingleTelescope
          400:
            content:
              application/json:
                schema: Error
        """
        telescope = Telescope.query.filter(Telescope.name == telescope_name).first()
        if telescope is None:
            return self.error("Invalid telescope name.")
        # Ensure user has access to telescope
        _ = Telescope.get_if_owned_by(telescope.id, self.current_user)

        return self.success(data=telescope)
