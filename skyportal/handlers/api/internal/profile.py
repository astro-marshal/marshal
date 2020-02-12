from baselayer.app.access import auth_or_token
from ...base import BaseHandler
from ....models import User


class ProfileHandler(BaseHandler):
    @auth_or_token
    def get(self):
        """
        ---
        description: Retrieve user profile
        responses:
          200:
            content:
              application/json:
                schema: SingleUser
        """
        user = (User.query.filter(User.username == self.current_user.username)
                    .first())
        user_roles = [role.id for role in user.roles]
        user_acls = [acl.id for acl in user.acls]
        user_tokens = [{'id': token.id,
                        'name': token.name,
                        'acls': [acl.id for acl in token.acls],
                        'created_at': token.created_at}
                       for token in user.tokens]
        return self.success(data={'username': self.current_user.username,
                                  'roles': user_roles,
                                  'acls': user_acls,
                                  'tokens': user_tokens})
