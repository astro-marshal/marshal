from marshmallow.exceptions import ValidationError
from tdtax import schema, validate
from jsonschema.exceptions import ValidationError as JSONValidationError

from baselayer.app.access import permissions, auth_or_token
from ..base import BaseHandler
from ...models import DBSession, Taxonomy, Group


class TaxonomyHandler(BaseHandler):
    @auth_or_token
    def get(self, taxonomy_id):
        """
        ---
        description: Retrieve a taxonomy
        parameters:
          - in: path
            name: taxonomy_id
            required: true
            schema:
              type: integer
        responses:
          200:
            content:
              application/json:
                schema: SingleTaxonomy
          400:
            content:
              application/json:
                schema: Error
        """
        taxonomy = Taxonomy. \
            get_taxonomy_usable_by_user(
                        taxonomy_id,
                        self.current_user
            )
        if taxonomy is None:
            return self.error(
                'Taxonomy does not exist or is not available to user.'
            )

        if not isinstance(taxonomy, list):
            self.error('Problem retreiving taxonomy')

        return self.success(data=taxonomy[0])

    @permissions(['Post Taxonomy'])
    def post(self):
        """
        ---
        description: Post new taxonomy
        requestBody:
          content:
            application/json:
              schema:
                type: object
                properties:
                  name:
                    type: string
                    description: |
                      Short string to make this taxonomy memorable
                      to end users.
                  hierarchy:
                    type: object
                    description: |
                       Nested JSON describing the taxonomy
                       which should be validated against
                       a schema before entry
                  group_ids:
                    type: array
                    items:
                      type: integer
                    description: |
                      List of group IDs corresponding to which groups should be
                      able to view comment. Defaults to all of requesting user's
                      groups.
                  version:
                    type: string
                    description: |
                      Semantic version of this taxonomy name
                  provenance:
                    type: string
                    description: |
                      Identifier (e.g., URL or git hash) that
                      uniquely ties this taxonomy back
                      to an origin or place of record
                  isLatest:
                    type: boolean
                    description: |
                      Consider this version of the taxonomy with this
                      name the latest? Defaults to True.
                required:
                  - name
                  - hierarchy
                  - version

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
                            comment_id:
                              type: integer
                              description: New taxonomy ID
        """
        data = self.get_json()
        name = data.get('name', None)
        if name is None:
            return self.error(f"A name must be provided for a taxonomy")

        version = data.get('version', None)
        if version is None:
            return self.error(
                f"A version string must be provided for a taxonomy"
            )

        others = (
            Taxonomy.query
            .filter(Taxonomy.name == name)
            .filter(Taxonomy.version == version)
            .all()
        )

        if len(others) != 0:
            return self.error(
                f"That version/name combination is already "
                "present. If you really want to replace this "
                "then delete the appropriate entry."
            )

        # Ensure a valid taxonomy
        hierarchy = data.get('hierarchy', None)
        if hierarchy is None:
            return self.error(f"A JSON of the taxonomy must be given")

        try:
            validate(hierarchy, schema)
        except JSONValidationError:
            return self.error(
                f"Hierarchy does not validate against the schema."
            )

        # establish the groups to use
        user_group_ids = [g.id for g in self.current_user.groups]
        group_ids = data.pop("group_ids", user_group_ids)
        if group_ids == []:
            group_ids = user_group_ids
        group_ids = [gid for gid in group_ids if gid in user_group_ids]
        if not group_ids:
            return self.error(f"Invalid group IDs field ({group_ids}): "
                              "You must provide one or more valid group IDs.")
        groups = Group.query.filter(Group.id.in_(group_ids)).all()

        provenance = data.get('provenance', None)

        # update others with this name
        # TODO: deal with the same name but different groups?
        isLatest = data.get('isLatest', True)
        if isLatest:
            DBSession().query(Taxonomy) \
                       .filter(Taxonomy.name == name) \
                       .update({'isLatest': False})

        taxonomy = Taxonomy(
            name=name,
            hierarchy=hierarchy,
            provenance=provenance,
            version=version,
            isLatest=isLatest,
            groups=groups
        )

        DBSession().add(taxonomy)
        DBSession().commit()

        return self.success(data={'taxonomy_id': taxonomy.id})

    @permissions(['Delete Taxonomy'])
    def delete(self, taxonomy_id):
        """
        ---
        description: Delete a taxonomy
        parameters:
          - in: path
            name: taxonomy_id
            required: true
            schema:
              type: integer
        responses:
          200:
            content:
              application/json:
                schema: Success
        """
        user = self.associated_user_object.username
        roles = (self.current_user.roles if hasattr(self.current_user, 'roles') else [])
        c = Taxonomy.query.get(taxonomy_id)
        if c is None:
            return self.error("Invalid taxonomy ID")

        Taxonomy.query.filter_by(id=taxonomy_id).delete()
        DBSession().commit()

        return self.success()
