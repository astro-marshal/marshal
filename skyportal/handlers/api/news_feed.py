from sqlalchemy import desc
from baselayer.app.access import auth_or_token
from ..base import BaseHandler
from ...models import DBSession, Source, Photometry, Comment, GroupSource


class NewsFeedHandler(BaseHandler):
    @auth_or_token
    def get(self):
        """
        ---
        description: Retrieve summary of recent activity
        responses:
          200:
            content:
              application/json:
                schema:
                  allOf:
                    - Success
                    - type: object
                      properties:
                        comments:
                          type: arrayOfComments
                          description: Newest comments
                        sources:
                          type: arrayOfSources
                          description: Newest updated sources
                        photometry:
                          type: arrayOfPhotometry
                          description: Newest photometry entries
          400:
            content:
              application/json:
                schema: Error
        """
        if (self.current_user.preferences and 'newsFeed' in self.current_user.preferences
            and 'numItems' in self.current_user.preferences['newsFeed']):
            n_items = min(int(self.current_user.preferences['newsFeed']['numItems']),
                          20)
        else:
            n_items = 5

        def fetch_newest(model):
            if model == Source:
                source_id_attr = 'id'
            else:
                source_id_attr = 'source_id'
            return model.query.filter(getattr(model, source_id_attr).in_(
                DBSession.query(GroupSource.source_id).filter(
                    GroupSource.group_id.in_([g.id for g in self.current_user.groups])
                ))).order_by(desc(model.created_at)).limit(n_items).all()

        sources = fetch_newest(Source)
        photometry = fetch_newest(Photometry)
        comments = fetch_newest(Comment)
        news_feed_items = [{'type': 'source', 'time': s.created_at,
                            'message': f'New source {s.id}'} for s in sources]
        news_feed_items.extend([{'type': 'comment', 'time': c.created_at,
                                 'message': f'{c.author}: {c.text} ({c.source_id})'}
                                for c in comments])
        news_feed_items.sort(key=lambda x: x['time'], reverse=True)
        news_feed_items = news_feed_items[:n_items]

        return self.success(data={'news_feed_items': news_feed_items})
