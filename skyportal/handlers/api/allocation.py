from ..base import BaseHandler
from ...models import DBSession, Allocation
from baselayer.app.access import auth_or_token, permissions, AccessError
from marshmallow.exceptions import ValidationError


class AllocationHandler(BaseHandler):
    @auth_or_token
    def get(self, allocation_id=None):
        """
        ---
        single:
          description: Retrieve an allocation
          parameters:
            - in: path
              name: allocation_id
              required: true
              schema:
                type: integer
          responses:
            200:
               content:
                application/json:
                  schema: SingleAllocation
            400:
              content:
                application/json:
                  schema: Error
        multiple:
          description: Retrieve all allocations
          parameters:
          - in: query
            name: instrument_id
            nullable: true
            schema:
              type: number
            description: Instrument ID to retrieve allocations for
          responses:
            200:
              content:
                application/json:
                  schema: ArrayOfAllocations
            400:
              content:
                application/json:
                  schema: Error
        """

        # get owned allocations
        allocations = Allocation.query_records_accessible_by(
            self.current_user, mode="read"
        )
        if allocation_id is not None:
            try:
                allocation_id = int(allocation_id)
            except ValueError:
                return self.error("Allocation ID must be an integer.")
            allocations = allocations.filter(Allocation.id == allocation_id).all()
            if len(allocations) == 0:
                return self.error("Could not retrieve allocation.")
            return self.success(data=allocations[0])

        instrument_id = self.get_query_argument('instrument_id', None)
        if instrument_id is not None:
            allocations = allocations.filter(Allocation.instrument_id == instrument_id)

        allocations = allocations.all()
        return self.success(data=allocations)

    @permissions(['Manage allocations'])
    def post(self):
        """
        ---
        description: Post new allocation on a robotic instrument
        requestBody:
          content:
            application/json:
              schema: AllocationNoID
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
                              description: New allocation ID
        """

        data = self.get_json()
        try:
            allocation = Allocation.__schema__().load(data=data)
        except ValidationError as e:
            return self.error(
                f'Error parsing posted allocation: "{e.normalized_messages()}"'
            )

        DBSession().add(allocation)
        self.enforce_permissions_on_next_flush()

        try:
            DBSession().commit()
        except AccessError as e:
            return self.error(e.args[0])

        return self.success(data={"id": allocation.id})

    @permissions(['Manage allocations'])
    def put(self, allocation_id):
        """
        ---
        description: Update an allocation on a robotic instrument
        parameters:
          - in: path
            name: allocation_id
            required: true
            schema:
              type: integer
        requestBody:
          content:
            application/json:
              schema: AllocationNoID
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
        allocation_id = int(allocation_id)
        allocation = Allocation.query.get(allocation_id)

        if allocation is None:
            return self.error('No such allocation')

        data = self.get_json()
        data['id'] = allocation_id

        schema = Allocation.__schema__()
        try:
            schema.load(data, partial=True)
        except ValidationError as e:
            return self.error(
                'Invalid/missing parameters: ' f'{e.normalized_messages()}'
            )

        self.enforce_permissions_on_next_flush()

        try:
            DBSession().commit()
        except AccessError as e:
            return self.error(e.args[0])

        return self.success()

    @permissions(['Manage allocations'])
    def delete(self, allocation_id):
        """
        ---
        description: Delete allocation.
        parameters:
          - in: path
            name: allocation_id
            required: true
            schema:
              type: string
        responses:
          200:
            content:
              application/json:
                schema: Success
        """
        allocation = Allocation.query.get(int(allocation_id))
        DBSession().delete(allocation)
        self.enforce_permissions_on_next_flush()

        try:
            DBSession().commit()
        except AccessError as e:
            return self.error(e.args[0])
        return self.success()
