import * as groupsActions from './ducks/groups';
import * as profileActions from './ducks/profile';
import * as sysInfoActions from './ducks/sysInfo';
import * as dbInfoActions from './ducks/dbInfo';
import * as configActions from './ducks/config';
import * as newsFeedActions from './ducks/newsFeed';
import * as topSourcesActions from './ducks/topSources';
import * as instrumentsActions from './ducks/instruments';
import * as observingRunsActions from './ducks/observingRuns';
import * as telescopesActions from './ducks/telescopes';
import * as taxonomyActions from './ducks/taxonomies';

export default function hydrate() {
  return (dispatch) => {
    dispatch(configActions.fetchConfig());
    dispatch(sysInfoActions.fetchSystemInfo());
    dispatch(dbInfoActions.fetchDBInfo());
    dispatch(profileActions.fetchUserProfile());
    dispatch(groupsActions.fetchGroups());
    dispatch(newsFeedActions.fetchNewsFeed());
    dispatch(topSourcesActions.fetchTopSources());
    dispatch(instrumentsActions.fetchInstruments());
    dispatch(instrumentsActions.fetchInstrumentObsParams());
    dispatch(observingRunsActions.fetchObservingRuns());
    dispatch(telescopesActions.fetchTelescopes());
    dispatch(taxonomyActions.fetchTaxonomies());
  };
}
