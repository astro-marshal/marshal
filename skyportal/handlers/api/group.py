import uuid
import python_http_client.exceptions
from sqlalchemy.orm import joinedload
from marshmallow.exceptions import ValidationError
from baselayer.app.access import permissions, auth_or_token
from baselayer.app.env import load_env
from ..base import BaseHandler
from .user import add_user_and_setup_groups
from ...models import (
    DBSession,
    Filter,
    Group,
    GroupStream,
    GroupUser,
    Invitation,
    Stream,
    User,
    Token,
)

_, cfg = load_env()


class GroupHandler(BaseHandler):
    @auth_or_token
    def get(self, group_id=None):
        """
        ---
        single:
          description: Retrieve a group
          parameters:
            - in: path
              name: group_id
              required: true
              schema:
                type: integer
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
                            allOf:
                              - $ref: '#/components/schemas/Group'
                              - type: object
                                properties:
                                  users:
                                    type: array
                                    items:
                                      - $ref: '#/components/schemas/User'
                                    description: List of group users
            400:
              content:
                application/json:
                  schema: Error
        multiple:
          description: Retrieve all groups
          parameters:
            - in: query
              name: name
              schema:
                type: string
              description: Fetch by name (exact match)
            - in: query
              name: includeSingleUserGroups
              schema:
                type: boolean
              description: |
                Bool indicating whether to include single user groups.
                Defaults to false.
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
                              user_groups:
                                type: array
                                items:
                                  $ref: '#/components/schemas/Group'
                                description: List of groups current user is a member of.
                              user_accessible_groups:
                                type: array
                                items:
                                  $ref: '#/components/schemas/Group'
                                description: |
                                  List of groups current user can access, not including
                                  single user groups.
                              all_groups:
                                type: array
                                items:
                                  $ref: '#/components/schemas/Group'
                                description: |
                                  List of all groups, optionally including single user
                                  groups if query parameter `includeSingleUserGroups` is
                                  `true`.
            400:
              content:
                application/json:
                  schema: Error
        """
        if group_id is not None:
            if 'Manage groups' in [acl.id for acl in self.current_user.acls]:
                group = (
                    Group.query.options(joinedload(Group.users))
                    .options(joinedload(Group.group_users))
                    .get(group_id)
                )
            else:
                group = (
                    Group.query.options(
                        [joinedload(Group.users).load_only(User.id, User.username)]
                    )
                    .options(joinedload(Group.group_users))
                    .get(group_id)
                )
                if group is not None and group.id not in [
                    g.id for g in self.current_user.accessible_groups
                ]:
                    return self.error('Insufficient permissions.')
            if group is not None:
                group = group.to_dict()
                # Do not include User.groups to avoid circular reference
                group['users'] = [
                    {'id': user.id, 'username': user.username}
                    for user in group['users']
                ]
                # grab streams:
                streams = (
                    DBSession()
                    .query(Stream)
                    .join(GroupStream)
                    .filter(GroupStream.group_id == group_id)
                    .all()
                )
                group['streams'] = streams
                # grab filters:
                filters = (
                    DBSession().query(Filter).filter(Filter.group_id == group_id).all()
                )
                group['filters'] = filters

                return self.success(data=group)
            return self.error(f"Could not load group with ID {group_id}")
        group_name = self.get_query_argument("name", None)
        if group_name is not None:
            groups = Group.query.filter(Group.name == group_name).all()
            # Ensure access
            if not all(
                [group in self.current_user.accessible_groups for group in groups]
            ):
                return self.error("Insufficient permissions")
            return self.success(data=groups)

        include_single_user_groups = self.get_query_argument(
            "includeSingleUserGroups", False
        )
        info = {}
        info['user_groups'] = list(self.current_user.groups)
        info['user_accessible_groups'] = [
            g for g in self.current_user.accessible_groups if not g.single_user_group
        ]
        all_groups_query = Group.query
        if (not include_single_user_groups) or (
            isinstance(include_single_user_groups, str)
            and include_single_user_groups.lower() == "false"
        ):
            all_groups_query = all_groups_query.filter(
                Group.single_user_group.is_(False)
            )
        info["all_groups"] = all_groups_query.all()
        return self.success(data=info)

    @permissions(['Manage groups'])
    def post(self):
        """
        ---
        description: Create a new group
        requestBody:
          content:
            application/json:
              schema:
                allOf:
                  - $ref: '#/components/schemas/GroupNoID'
                  - type: object
                    properties:
                      group_admins:
                        type: array
                        items:
                          type: string
                        description: |
                          List of emails of users to be group admins. Current user will
                          automatically be added as a group admin.
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
                              description: New group ID
        """
        data = self.get_json()

        group_admin_emails = [
            e.strip() for e in data.get('group_admins', []) if e.strip()
        ]
        group_admins = list(User.query.filter(User.username.in_(group_admin_emails)))
        if self.current_user not in group_admins and not isinstance(
            self.current_user, Token
        ):
            group_admins.append(self.current_user)

        g = Group(name=data['name'])
        DBSession().add(g)
        DBSession().flush()
        DBSession().add_all(
            [GroupUser(group=g, user=user, admin=True) for user in group_admins]
        )
        DBSession().commit()

        self.push_all(action='skyportal/FETCH_GROUPS')
        return self.success(data={"id": g.id})

    @permissions(['Manage groups'])
    def put(self, group_id):
        """
        ---
        description: Update a group
        parameters:
          - in: path
            name: group_id
            schema:
              type: integer
        requestBody:
          content:
            application/json:
              schema: GroupNoID
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
        data = self.get_json()
        data['id'] = group_id

        schema = Group.__schema__()
        try:
            schema.load(data)
        except ValidationError as e:
            return self.error(
                'Invalid/missing parameters: ' f'{e.normalized_messages()}'
            )
        DBSession().commit()

        return self.success(action='skyportal/FETCH_GROUPS')

    @permissions(['Manage groups'])
    def delete(self, group_id):
        """
        ---
        description: Delete a group
        parameters:
          - in: path
            name: group_id
            required: true
            schema:
              type: integer
        responses:
          200:
            content:
              application/json:
                schema: Success
        """
        g = Group.query.get(group_id)
        if g.name == cfg["misc"]["public_group_name"]:
            return self.error("Cannot delete site-wide public group.")
        DBSession().delete(g)
        DBSession().commit()

        self.push_all(
            action='skyportal/REFRESH_GROUP', payload={'group_id': int(group_id)}
        )
        self.push_all(action='skyportal/FETCH_GROUPS')
        return self.success()


class GroupUserHandler(BaseHandler):
    @auth_or_token
    def post(self, group_id, *ignored_args):
        """
        ---
        description: Add a group user
        parameters:
          - in: path
            name: group_id
            required: true
            schema:
              type: integer
        requestBody:
          content:
            application/json:
              schema:
                type: object
                properties:
                  username:
                    type: string
                  admin:
                    type: boolean
                required:
                  - username
                  - admin
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
                            group_id:
                              type: integer
                              description: Group ID
                            user_id:
                              type: integer
                              description: User ID
                            admin:
                              type: boolean
                              description: Boolean indicating whether user is group admin
        """
        current_groupuser = (
            GroupUser.query.filter(GroupUser.group_id == group_id)
            .filter(GroupUser.user_id == self.current_user.id)
            .first()
        )
        if (
            len(
                {"System admin", "Manage users", "Manage groups"}.intersection(
                    set(self.current_user.permissions)
                )
            )
            == 0
            and not current_groupuser.admin
        ):
            return self.error("Inadequate permissions.")

        data = self.get_json()

        username = data.pop("username", None)
        if username is None:
            return self.error("Username must be specified")

        admin = data.pop("admin", False)
        group_id = int(group_id)
        group = Group.query.get(group_id)
        if group.single_user_group:
            return self.error("Cannot add users to single-user groups.")
        user = User.query.filter(User.username == username.lower()).first()
        if user is None:
            groups = Group.query.filter(Group.id == group_id).all()
            if cfg["invitations.enabled"]:
                invite_token = str(uuid.uuid4())
                DBSession.add(
                    Invitation(
                        token=invite_token,
                        groups=groups,
                        admin_for_groups=[admin],
                        user_email=username,
                        invited_by=self.associated_user_object,
                    )
                )
                user_id = None
            else:
                user_id = add_user_and_setup_groups(
                    username=username,
                    roles=["Full user"],
                    group_ids_and_admin=[[group_id, admin]],
                )
        else:
            user_id = user.id
            # Just add new GroupUser
            gu = (
                GroupUser.query.filter(GroupUser.group_id == group_id)
                .filter(GroupUser.user_id == user_id)
                .first()
            )
            if gu is None:
                DBSession.add(
                    GroupUser(group_id=group_id, user_id=user_id, admin=admin)
                )
            else:
                return self.error(
                    "Specified user is already associated with this group."
                )
        try:
            DBSession().commit()
        except python_http_client.exceptions.UnauthorizedError:
            return self.error(
                "Twilio Sendgrid authorization error. Please ensure "
                "valid Sendgrid API key is set in server environment as "
                "per their setup docs."
            )

        self.push_all(action='skyportal/REFRESH_GROUP', payload={'group_id': group_id})
        return self.success(
            data={'group_id': group_id, 'user_id': user_id, 'admin': admin}
        )

    @auth_or_token
    def delete(self, group_id, username):
        """
        ---
        description: Delete a group user
        parameters:
          - in: path
            name: group_id
            required: true
            schema:
              type: integer
          - in: path
            name: username
            required: true
            schema:
              type: string
        responses:
          200:
            content:
              application/json:
                schema: Success
        """
        current_groupuser = (
            GroupUser.query.filter(GroupUser.group_id == group_id)
            .filter(GroupUser.user_id == self.current_user.id)
            .first()
        )
        if (
            len(
                {"System admin", "Manage users", "Manage groups"}.intersection(
                    set(self.current_user.permissions)
                )
            )
            == 0
            and not current_groupuser.admin
        ):
            return self.error("Inadequate permissions.")

        group = Group.query.get(group_id)
        if group.single_user_group:
            return self.error("Cannot delete users from single user groups.")
        user_id = User.query.filter(User.username == username).first().id
        (
            GroupUser.query.filter(GroupUser.group_id == group_id)
            .filter(GroupUser.user_id == user_id)
            .delete()
        )
        DBSession().commit()
        self.push_all(
            action='skyportal/REFRESH_GROUP', payload={'group_id': int(group_id)}
        )
        return self.success()


class GroupStreamHandler(BaseHandler):
    @permissions(['System admin'])
    def post(self, group_id, *ignored_args):
        """
        ---
        description: Add alert stream access to group
        parameters:
          - in: path
            name: group_id
            required: true
            schema:
              type: integer
        requestBody:
          content:
            application/json:
              schema:
                type: object
                properties:
                  stream_id:
                    type: integer
                required:
                  - stream_id
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
                            group_id:
                              type: integer
                              description: Group ID
                            stream_id:
                              type: integer
                              description: Stream ID
        """
        data = self.get_json()
        group_id = int(group_id)
        # group = Group.query.filter(Group.id == group_id).first()
        group = (
            Group.query.options(joinedload(Group.users))
            .options(joinedload(Group.group_users))
            .get(group_id)
        )
        if group is None:
            return self.error("Specified group_id does not exist.")
        stream_id = data.get('stream_id')
        stream = Stream.query.filter(Stream.id == stream_id).first()
        if stream is None:
            return self.error("Specified stream_id does not exist.")
        else:
            # TODO ensure all current group users have access to this stream
            # TODO do the check

            # Add new GroupStream
            gs = GroupStream.query.filter(
                GroupStream.group_id == group_id, GroupStream.stream_id == stream_id
            ).first()
            if gs is None:
                DBSession.add(GroupStream(group_id=group_id, stream_id=stream_id))
            else:
                return self.error(
                    "Specified stream is already associated with this group."
                )
        DBSession().commit()

        self.push_all(action='skyportal/REFRESH_GROUP', payload={'group_id': group_id})
        return self.success(data={'group_id': group_id, 'stream_id': stream_id})

    @permissions(['System admin'])
    def delete(self, group_id, stream_id):
        """
        ---
        description: Delete an alert stream from group
        parameters:
          - in: path
            name: group_id
            required: true
            schema:
              type: integer
          - in: path
            name: stream_id
            required: true
            schema:
              type: integer
        responses:
          200:
            content:
              application/json:
                schema: Success
        """
        stream = Stream.query.filter(Stream.id == int(stream_id)).first()
        stream_id = stream.id
        if stream is None:
            return self.error("Specified stream_id does not exist.")
        else:
            (
                GroupStream.query.filter(GroupStream.group_id == group_id)
                .filter(GroupStream.stream_id == stream_id)
                .delete()
            )
            DBSession().commit()
            self.push_all(
                action='skyportal/REFRESH_GROUP', payload={'group_id': int(group_id)}
            )
            return self.success()
