from baselayer.app.handlers.base import BaseHandler
from baselayer.app.access import permissions, auth_or_token
from ..models import User, Token, DBSession
from ..model_util import create_token

import tornado.web


class TokenHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        """
        ---
        description: Generate new token
        parameters:
          - in: path
            name: token
            schema: Token
        responses:
          200:
            content:
              application/json:
                schema: Success
        """
        data = self.get_json()

        user = (User.query.filter(User.username == self.current_user.username)
                    .first())
        user_acls = {acl.id for acl in user.acls}
        requested_acls = {k.replace('acls_', '') for k, v in data.items() if
                          k.startswith('acls_') and v == True}
        token_acls = requested_acls & user_acls
        token_id = create_token(group_id=data['group_id'],
                                permissions=token_acls,
                                created_by_id=user.id,
                                description=data['description'])
        return self.success(token_id, 'skyportal/FETCH_USER_PROFILE')

    @auth_or_token
    def delete(self, token_id):
        """
        ---
        description: Delete a token
        parameters:
          - in: path
            name: token_id
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
        t = Token.get_if_owned_by(token_id, self.current_user)
        if t is not None:
            DBSession.delete(t)
            DBSession.commit()

            return self.success(action='skyportal/FETCH_USER_PROFILE')
        else:
            return self.error('Either the specified token does not exist, '
                              'or the user does not have the necessary '
                              'permissions to delete it.')
