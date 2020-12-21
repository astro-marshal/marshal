import pytest
from skyportal.models import Base, Candidate

subclasses = Base.__subclasses__()
access_types = ['create', 'read', 'update', 'delete']
parameters = [(c, m) for c in subclasses for m in access_types]


@pytest.mark.parametrize("mode", access_types)
def test_return_type(mode, super_admin_user, public_candidate):
    # load a record into the DB
    results = Candidate.get_records_accessible_by(super_admin_user, mode=mode)
    for instance in results:
        accessible = instance.is_accessible_by(super_admin_user, mode=mode)
        assert type(instance.is_accessible_by(super_admin_user, mode=mode)) is bool
        assert accessible


"""
@pytest.mark.parametrize("cls,mode", parameters)
def test_filter_by_accessibility(cls, mode):
    DBSession().rollback()
    q = cls.accessibility_query(User.id, mode=mode)
    accessible = q.accessibility_target
    q = q.filter(accessible)
    for instance, user, is_accessible in q:
        assert instance.is_accessible_by(user, mode=mode) == is_accessible
"""
