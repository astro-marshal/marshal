import tornado.web
from sqlalchemy.orm import joinedload
from baselayer.app.access import permissions, auth_or_token
from baselayer.app.handlers.base import BaseHandler
from ..models import DBSession, Group, GroupUser, User


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
              required: false
              schema:
                type: integer
          responses:
            200:
              content:
                application/json:
                  schema: SingleGroup
            400:
              content:
                application/json:
                  schema: Error
        multiple:
          description: Retrieve all groups
          responses:
            200:
              content:
                application/json:
                  schema: ArrayOfGroups
            400:
              content:
                application/json:
                  schema: Error
        """
        if group_id is not None:
            if 'Super admin' in [role.id for role in self.current_user.roles]:
                info = Group.query.options(joinedload(Group.users)).options(
                    joinedload(Group.group_users)).get(group_id)
            else:
                info = Group.get_if_owned_by(
                    group_id, self.current_user,
                    options=[joinedload(Group.users),
                             joinedload(Group.group_users)])
        else:
            info = {}
            info['user_groups'] = list(self.current_user.groups)
            info['all_groups'] = (list(Group.query) if 'Super admin' in
                                  [role.id for role in self.current_user.roles]
                                  else None)
        if info is not None:
            return self.success(info)
        else:
            return self.error(f"Could not load group {group_id}",
                              {"group_id": group_id})

    @permissions(['Manage groups'])
    def post(self):
        """
        ---
        description: Create a new group
        parameters:
          - in: path
            name: group
            schema: Group
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
                          description: New group ID
        """
        data = self.get_json()
        group_admin_emails = [username.strip() for username in
                              data['groupAdmins'].split(',')
                              if username.strip() != '']

        group_admins = list(User.query.filter(User.username.in_(
            group_admin_emails)))

        g = Group(name=data['groupName'])
        DBSession().add_all([
            GroupUser(group=g, user=user, admin=True) for user in
            [self.current_user] + group_admins])
        DBSession().commit()

        self.push_all(action='skyportal/FETCH_GROUPS')
        return self.success({"id": g.id})

    @permissions(['Manage groups'])
    def put(self, group_id):
        """
        ---
        description: Update a group
        parameters:
          - in: path
            name: group
            schema: Group
        responses:
          200:
            content:
              application/json:
                schema: Success
        """
        data = self.get_json()

        g = Group.query.get(group_id)
        g.name = data['groupName']
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
        DBSession().delete(g)
        DBSession().commit()

        return self.success(action='skyportal/FETCH_GROUPS')


class GroupUserHandler(BaseHandler):
    @permissions(['Manage groups'])
    def put(self, group_id, username):
        """
        ---
        description: Update a group user
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
          - in: path
            name: admin
            required: true
            schema:
              type: boolean
        responses:
          200:
            content:
              application/json:
                schema:
                  allOf:
                    - Success
                    - type: object
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
        data = self.get_json()
        try:
            user_id = User.query.filter(User.username == username).first().id
        except AttributeError:
            return self.error('Invalid username.')
        gu = (GroupUser.query.filter(GroupUser.group_id == group_id)
                       .filter(GroupUser.user_id == user_id).first())
        if gu is None:
            gu = GroupUser(group_id=group_id, user_id=user_id)
        gu.admin = data['admin']
        DBSession().add(gu)
        DBSession().commit()

        self.push_all(action='skyportal/REFRESH_GROUP',
                      payload={'group_id': gu.group_id})
        return self.success({'group_id': gu.group_id, 'user_id': gu.user_id,
                             'admin': gu.admin})

    @permissions(['Manage groups'])
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
        user_id = User.query.filter(User.username == username).first().id
        (GroupUser.query.filter(GroupUser.group_id == group_id)
                   .filter(GroupUser.user_id == user_id).delete())
        DBSession().commit()
        self.push_all(action='skyportal/REFRESH_GROUP',
                      payload={'group_id': int(group_id)})
        return self.success()
