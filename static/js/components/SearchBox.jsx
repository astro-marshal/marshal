import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { useDispatch } from 'react-redux';

import * as Actions from '../ducks/sources';

import styles from "./SearchBox.css";

// Custom Components:
import CustomInput from './CustomInput';
import CheckBox from './CheckBox';


const SearchBox = ({ sources }) => {
  const dispatch = useDispatch();

  const [formState, setFormState] = useState({
    sourceID: "",
    ra: "",
    dec: "",
    radius: "",
    startDate: "",
    endDate: "",
    simbadClass: "",
    hasTNSname: false
  });

  const handleInputChange = (event) => {
    const newState = {};
    newState[event.target.name] = event.target.type === 'checkbox' ?
      event.target.checked : event.target.value;
    setFormState({
      ...formState,
      ...newState
    });
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    dispatch(Actions.submitSourceFilterParams(formState));
  };

  const handleReset = (event) => {
    setFormState({
      sourceID: "",
      ra: "",
      dec: "",
      radius: "",
      startDate: "",
      endDate: "",
      simbadClass: "",
      hasTNSname: false
    });
    dispatch(Actions.fetchSources());
  };

  const handleClickNextPage = (event) => {
    event.preventDefault();
    const vals = { ...formState, pageNumber: sources.pageNumber + 1 };
    dispatch(Actions.submitSourceFilterParams(vals));
  };

  const handleClickPreviousPage = (event) => {
    event.preventDefault();
    const vals = { ...formState, pageNumber: sources.pageNumber - 1 };
    dispatch(Actions.submitSourceFilterParams(vals));
  };

  return (
    <div className={styles.searchBoxWrapper}>
      <h4> Filter Sources </h4>
      <div className={styles.searchBox}>
        <form className={styles.searchBoxForm}>
          <div className={styles.searchBoxFormInner}>
            <h5 className={styles.searchBoxFormHeader}> Filter by Name or ID </h5>
            <div className={styles.searchBoxFormInputs}>
              <div className={styles.col12}>
                <CustomInput
                  label="Source ID/Name (can be substring)"
                  type="text"
                  name="sourceID"
                  value={formState.sourceID}
                  onChange={handleInputChange}
                  size="6"
                />
              </div>
            </div>
          </div>
          <div className={styles.searchBoxFormInner}>
            <h5 className={styles.searchBoxFormHeader}> Filter by Position </h5>
            <div className={styles.searchBoxFormInputs}>
              <div className={styles.col4}>
                <CustomInput
                  label="RA (degrees)"
                  type="text"
                  name="ra"
                  value={formState.ra}
                  onChange={handleInputChange}
                  size="6"
                />
              </div>
              <div className={styles.col4}>
                <CustomInput
                  label="Dec (degrees)"
                  type="text"
                  name="dec"
                  value={formState.dec}
                  onChange={handleInputChange}
                  size="6"
                />
              </div>
              <div className={styles.col4}>
                <CustomInput
                  label="Radius (degrees)"
                  type="text"
                  name="radius"
                  value={formState.radius}
                  onChange={handleInputChange}
                  size="6"
                />
              </div>
            </div>
          </div>
          {/* Required format: %Y-%m-%dT%H:%M:%S in UTC time, e.g. 2012-08-30T00:00:00 */}
          <div className={styles.searchBoxFormInner}>
            <h5 className={styles.searchBoxFormHeader}> Filter by Time Last Detected (UTC)</h5>
            <div className={styles.searchBoxFormInputs}>
              <div className={styles.col6}>
                <CustomInput
                  format="UTC"
                  label="Start Date"
                  type="text"
                  name="startDate"
                  value={formState.startDate}
                  onChange={handleInputChange}
                  placeholder="2012-08-30T00:00:00"
                  size="6"
                />
              </div>
              <div className={styles.col6}>
                <CustomInput
                  format="UTC"
                  label="End Date"
                  type="text"
                  name="endDate"
                  value={formState.endDate}
                  onChange={handleInputChange}
                  placeholder="2012-08-30T00:00:00"
                  size="6"
                />
              </div>
            </div>
          </div>
          <div className={styles.searchBoxFormInner}>
            <h5 className={styles.searchBoxFormHeader}> Filter by Simbad Class </h5>
            <div className={styles.searchBoxFormInputs}>
              <div className={styles.col12}>
                <CustomInput
                  label="Class Name"
                  type="text"
                  name="simbadClass"
                  value={formState.simbadClass}
                  onChange={handleInputChange}
                  size="6"
                />
              </div>
            </div>
          </div>
          <div className={styles.searchBoxFormInner}>
            <div className={styles.searchBoxFormInputs}>
              <div className={styles.col4}>
                <CheckBox
                  type="checkbox"
                  label="Must Have TNS Name: "
                  name="hasTNSname"
                  checked={formState.hasTNSname}
                  onChange={handleInputChange}
                  size="6"
                />
              </div>
              <div className={styles.col4}>
                <input
                  type="submit"
                  className={styles.inputSubmitButton}
                  disabled={sources.queryInProgress}
                  onClick={handleSubmit}
                />
              </div>
              <div className={styles.col4}>
                <button
                  className={styles.inputSubmitButton}
                  type="button"
                  onClick={handleReset}
                >
                  Reset
                </button>
              </div>
            </div>
          </div>

        </form>
      </div>
      {
        sources && (
          <div className={styles.tableSubTitle}>
            <div style={{ display: "inline-block" }}>
              <button
                className={styles.inlineButton}
                type="button"
                onClick={handleClickPreviousPage}
                disabled={sources.pageNumber === 1}
              >
                View Previous 100 Sources
              </button>
            </div>
            <div style={{ display: "inline-block" }}>
              <i>
                Displaying&nbsp;
                {sources.sourceNumberingStart}
                -
                {sources.sourceNumberingEnd}
                &nbsp;
                of&nbsp;
                {sources.totalMatches}
                &nbsp;
                matching sources.
              </i>
            </div>
            <div style={{ display: "inline-block" }}>
              <button
                className={styles.inlineButton}
                type="button"
                onClick={handleClickNextPage}
                disabled={sources.lastPage}
              >
                View Next 100 Sources
              </button>
            </div>
          </div>
        )
      }
    </div>
  );
};

SearchBox.propTypes = {
  sources: PropTypes.InstanceOf(Array).isRequired
};

export default SearchBox;
