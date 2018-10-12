import { connect } from 'react-redux';

import SearchBox from '../components/SearchBox';
import * as Action from '../actions';


const mapDispatchToProps = (dispatch, ownProps) => (
  {
    filterSources: formState => {
      formState['pageNumber'] = ownProps.pageNumber;
      console.log("searchBox formState upon clicking submit:", formState);
      return dispatch(Action.submitSourceFilterParams(formState));
    },
    fetchSources: formState => dispatch(
      Action.fetchSources()
    )
  }
);

export default connect(null, mapDispatchToProps)(SearchBox);
