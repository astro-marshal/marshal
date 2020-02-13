import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';

import SearchBox from './SearchBox';
import * as sourcesActions from '../ducks/sources';
import UninitializedDBMessage from './UninitializedDBMessage';

import styles from './SourceList.css';

const SourceList = () => {
  const sources = useSelector(
    (state) => state.sources
  );

  const sourceTableEmpty = useSelector(
    (state) => state.dbInfo.source_table_empty
  );

  const dispatch = useDispatch();

  useEffect(() => {
    if (!sources.latest) {
      dispatch(sourcesActions.fetchSources());
    }
  }, []);

  if (sourceTableEmpty) {
    return <UninitializedDBMessage />;
  }
  if (sources) {
    return (
      <div className={styles.SourceListWrapper}>
        <h2>
          Sources
        </h2>

        <SearchBox sources={sources} />
        {
          !sources.queryInProgress && (
            <table id="tab">
              <thead>
                <tr className={styles.outerHeading}>
                  <th />
                  <th />
                  <th colSpan="2">
                    Position
                  </th>
                  <th colSpan="4">
                    Type
                  </th>
                  <th colSpan="2">
                    Gaia
                  </th>
                  <th />
                  <th />
                  <th />
                  <th />
                </tr>

                <tr className={styles.innerHeading}>
                  <th>
                    Last detected
                  </th>
                  <th>
                    Name
                  </th>
                  <th>
                    RA
                  </th>
                  <th>
                    DEC
                  </th>
                  <th>
                    varstar
                  </th>
                  <th>
                    transient
                  </th>
                  <th>
                    disagree
                  </th>
                  <th>
                    is_roid
                  </th>
                  <th>
                    Gmag
                  </th>
                  <th>
                    T
                    <sub>
                      eff
                    </sub>
                  </th>
                  <th>
                    Score
                  </th>
                  <th>
                    N detections
                  </th>
                  <th>
                    Simbad Class
                  </th>
                  <th>
                    TNS Name
                  </th>
                </tr>
              </thead>
              <tbody>
                {
<<<<<<< HEAD
                  sources.latest && sources.latest.map((source, idx) => (
                    <tr className={styles.tableRow} key={source.id}>
=======
                  sources.latest && sources.latest.map((source) => (
                    <tr key={source.id}>
>>>>>>> 3f7425b5521ecd199746b6018e8721ae2869b5b3
                      <td>
                        {source.last_detected && String(source.last_detected).split(".")[0]}
                      </td>
                      <td>
                        <Link to={`/source/${source.id}`}>
                          {source.id}
                        </Link>
                      </td>
                      <td>
                        {source.ra && Number(source.ra).toFixed(3)}
                      </td>
                      <td>
                        {source.dec && Number(source.dec.toFixed(4))}
                      </td>
                      <td>
                        {source.varstar.toString()}
                      </td>
                      <td>
                        {source.transient.toString()}
                      </td>
                      <td>
                        {(source.transient === source.varstar).toString()}
                      </td>
                      <td>
                        {source.is_roid.toString()}
                      </td>
                      <td>
                        {source.gaia_info && Number(JSON.parse(source.gaia_info).Gmag).toFixed(2)}
                      </td>
                      <td>
                        {source.gaia_info &&
                         JSON.parse(source.gaia_info).Teff &&
                         Number(JSON.parse(source.gaia_info).Teff).toFixed(1)}
                      </td>
                      <td>
                        {Number(source.score).toFixed(2)}
                      </td>
                      <td>
                        {source.detect_photometry_count}
                      </td>
                      <td>
                        {source.simbad_class}
                      </td>
                      <td>
                        {source.tns_name}
                      </td>
                    </tr>
                  ))
                }
              </tbody>
            </table>
          )
        }
        {
          sources.queryInProgress && (
            <div>
              <br />
              <br />
              <i>
                Query in progress...
              </i>
            </div>
          )
        }
      </div>
    );
  } else {
    return "Loading sources...";
  }
};

export default SourceList;
