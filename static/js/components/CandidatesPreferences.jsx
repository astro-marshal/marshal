import React, { useState, useEffect } from "react";
import { useSelector, useDispatch } from "react-redux";
import { useForm, Controller } from "react-hook-form";

import Select from "@material-ui/core/Select";
import MenuItem from "@material-ui/core/MenuItem";
import Typography from "@material-ui/core/Typography";
import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import Input from "@material-ui/core/Input";
import InputLabel from "@material-ui/core/InputLabel";
import Chip from "@material-ui/core/Chip";
import TextField from "@material-ui/core/TextField";
import FormControlLabel from "@material-ui/core/FormControlLabel";
import Checkbox from "@material-ui/core/Checkbox";
import SaveIcon from "@material-ui/icons/Save";
import { makeStyles, useTheme } from "@material-ui/core/styles";

import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";

import * as candidatesActions from "../ducks/candidates";
import * as profileActions from "../ducks/profile";
import Responsive from "./Responsive";
import FoldBox from "./FoldBox";
import FormValidationError from "./FormValidationError";
import { allowedClasses } from "./ClassificationForm";
import {
  savedStatusSelectOptions,
  rejectedStatusSelectOptions,
} from "./FilterCandidateList";
import ScanningProfilesList from "./ScanningProfilesList";

dayjs.extend(utc);

const useStyles = makeStyles(() => ({
  filterListContainer: {
    padding: "1rem",
    display: "flex",
    flexFlow: "column nowrap",
  },
  button: {
    marginTop: "1rem",
  },
  formRow: {
    margin: "1rem 0",
    "& > div": {
      width: "100%",
    },
  },
  redshiftField: {
    display: "inline-block",
    marginRight: "0.5rem",
  },
  savedStatusSelect: {
    margin: "1rem 0",
    "& input": {
      fontSize: "1rem",
    },
  },
}));

function getStyles(classification, selectedClassifications, theme) {
  return {
    fontWeight:
      selectedClassifications.indexOf(classification) === -1
        ? theme.typography.fontWeightRegular
        : theme.typography.fontWeightMedium,
  };
}

const CandidatesPreferences = () => {
  const preferences = useSelector((state) => state.profile.preferences);
  const classes = useStyles();
  const theme = useTheme();
  const dispatch = useDispatch();

  const userAccessibleGroups = useSelector(
    (state) => state.groups.userAccessible
  );

  const ITEM_HEIGHT = 48;
  const MenuProps = {
    PaperProps: {
      style: {
        maxHeight: ITEM_HEIGHT * 4.5,
        width: 250,
      },
    },
  };

  // Get unique classification names, in alphabetical order
  const { taxonomyList } = useSelector((state) => state.taxonomies);
  const latestTaxonomyList = taxonomyList.filter((t) => t.isLatest);
  let classifications = [];
  latestTaxonomyList.forEach((taxonomy) => {
    const currentClasses = allowedClasses(taxonomy.hierarchy).map(
      (option) => option.class
    );
    classifications = classifications.concat(currentClasses);
  });
  classifications = Array.from(new Set(classifications)).sort();

  const [selectedClassifications, setSelectedClassifications] = useState([]);

  const { handleSubmit, getValues, control, errors, reset } = useForm();

  useEffect(() => {
    reset({
      groupIDs: Array(userAccessibleGroups.length).fill(false),
    });
    // Don't want to reset everytime the component rerenders and
    // the defaultStartDate is updated, so ignore ESLint here
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reset, userAccessibleGroups]);

  // Set initial form values in the redux state
  useEffect(() => {
    dispatch(
      candidatesActions.setFilterFormData({
        savedStatus: "all",
      })
    );
    // Don't want to reset everytime the component rerenders and
    // the defaultStartDate is updated, so ignore ESLint here
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dispatch]);

  let formState = getValues({ nest: true });

  const validateGroups = () => {
    formState = getValues({ nest: true });
    return formState.groupIDs.filter((value) => Boolean(value)).length >= 1;
  };

  const [addDialogOpen, setAddDialogOpen] = useState(false);

  const onSubmit = async (formData) => {
    const groupIDs = userAccessibleGroups.map((g) => g.id);
    const selectedGroupIDs = groupIDs.filter(
      (ID, idx) => formData.groupIDs[idx]
    );
    const data = {
      id: Math.random().toString(36).substr(2, 5), // Assign a random ID to the profile
      groupIDs: selectedGroupIDs,
      savedStatus: formData.savedStatus,
      default: true,
    };
    // decide if to show rejected candidates
    if (formData.rejectedStatus) {
      data.rejectedStatus = formData.rejectedStatus;
    }
    // Convert dates to ISO for parsing on back-end
    if (formData.timeRange) {
      data.timeRange = formData.timeRange;
    }
    if (formData.classifications.length > 0) {
      data.classifications = formData.classifications;
    }
    if (formData.redshiftMinimum && formData.redshiftMaximum) {
      data.redshiftMinimum = formData.redshiftMinimum;
      data.redshiftMaximum = formData.redshiftMaximum;
    }

    // Add new profile as the default in the preferences
    const currentProfiles = preferences.scanningProfiles || [];
    currentProfiles.forEach((profile) => {
      profile.default = false;
    });
    currentProfiles.push(data);
    const prefs = {
      scanningProfiles: currentProfiles,
    };
    dispatch(profileActions.updateUserPreferences(prefs));
    setAddDialogOpen(false);
  };

  return (
    <div>
      <Typography variant="h6">Default Scanning Profiles</Typography>
      <ScanningProfilesList />
      <div className={classes.button}>
        <Button
          variant="contained"
          onClick={() => {
            setAddDialogOpen(true);
          }}
        >
          Add new scanning profile
        </Button>
      </div>
      <Dialog
        open={addDialogOpen}
        onClose={() => {
          setAddDialogOpen(false);
        }}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
      >
        <DialogTitle id="alert-dialog-title">
          Save a set of scanning options as your default
        </DialogTitle>
        <DialogContent>
          <div className={classes.filterListContainer}>
            <form onSubmit={handleSubmit(onSubmit)}>
              <div className={classes.formRow}>
                <Controller
                  render={({ onChange, value }) => (
                    <TextField
                      id="time-range"
                      label="Time range (hours before now)"
                      type="number"
                      value={value}
                      inputProps={{ step: 1 }}
                      InputLabelProps={{
                        shrink: true,
                      }}
                      onChange={(event) => onChange(event.target.value)}
                    />
                  )}
                  name="timeRange"
                  control={control}
                  defaultValue="24"
                />
              </div>
              <div className={classes.savedStatusSelect}>
                <InputLabel id="savedStatusSelectLabel">
                  Show only candidates which passed a filter from the selected
                  groups...
                </InputLabel>
                <Controller
                  labelId="savedStatusSelectLabel"
                  as={Select}
                  name="savedStatus"
                  control={control}
                  input={<Input data-testid="savedStatusSelect" />}
                  defaultValue="all"
                >
                  {savedStatusSelectOptions.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Controller>
              </div>
              <div className={classes.formRow}>
                <InputLabel id="classifications-select-label">
                  Classifications
                </InputLabel>
                <Controller
                  labelId="classifications-select-label"
                  render={({ onChange, value }) => (
                    <Select
                      id="classifications-select"
                      multiple
                      value={value}
                      onChange={(event) => {
                        setSelectedClassifications(event.target.value);
                        onChange(event.target.value);
                      }}
                      input={<Input id="classifications-select" />}
                      renderValue={(selected) => (
                        <div className={classes.chips}>
                          {selected.map((classification) => (
                            <Chip
                              key={classification}
                              label={classification}
                              className={classes.chip}
                            />
                          ))}
                        </div>
                      )}
                      MenuProps={MenuProps}
                    >
                      {classifications.map((classification) => (
                        <MenuItem
                          key={classification}
                          value={classification}
                          style={getStyles(
                            classification,
                            selectedClassifications,
                            theme
                          )}
                        >
                          {classification}
                        </MenuItem>
                      ))}
                    </Select>
                  )}
                  name="classifications"
                  control={control}
                  defaultValue={[]}
                />
              </div>
              <div className={classes.formRow}>
                {errors.redshiftMinimum && (
                  <FormValidationError message="Both redshift minimum/maximum must be defined" />
                )}
                <InputLabel id="redshift-select-label">Redshift</InputLabel>
                <div className={classes.redshiftField}>
                  <Controller
                    render={({ onChange, value }) => (
                      <TextField
                        id="minimum-redshift"
                        label="Minimum"
                        type="number"
                        value={value}
                        inputProps={{ step: 0.001 }}
                        size="small"
                        margin="dense"
                        InputLabelProps={{
                          shrink: true,
                        }}
                        onChange={(event) => onChange(event.target.value)}
                      />
                    )}
                    name="redshiftMinimum"
                    labelId="redshift-select-label"
                    control={control}
                    defaultValue=""
                  />
                </div>
                <div className={classes.redshiftField}>
                  <Controller
                    render={({ onChange, value }) => (
                      <TextField
                        id="maximum-redshift"
                        label="Maximum"
                        type="number"
                        value={value}
                        inputProps={{ step: 0.001 }}
                        size="small"
                        margin="dense"
                        InputLabelProps={{
                          shrink: true,
                        }}
                        onChange={(event) => onChange(event.target.value)}
                      />
                    )}
                    name="redshiftMaximum"
                    control={control}
                    defaultValue=""
                  />
                </div>
              </div>
              <div className={classes.formRow}>
                <InputLabel id="rejectedCandidatesLabel">
                  Show/hide rejected candidates
                </InputLabel>
                <Controller
                  labelId="rejectedCandidatesLabel"
                  as={Select}
                  name="rejectedStatus"
                  control={control}
                  input={<Input data-testid="rejectedStatusSelect" />}
                  defaultValue="hide"
                >
                  {rejectedStatusSelectOptions.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Controller>
              </div>
              <div>
                <Responsive
                  element={FoldBox}
                  title="Program Selection"
                  mobileProps={{ folded: true }}
                >
                  {errors.groupIDs && (
                    <FormValidationError message="Select at least one group." />
                  )}
                  {userAccessibleGroups.map((group, idx) => (
                    <FormControlLabel
                      key={group.id}
                      control={
                        <Controller
                          render={({ onChange, value }) => (
                            <Checkbox
                              onChange={(event) => {
                                onChange(event.target.checked);
                              }}
                              checked={value}
                              data-testid={`filteringFormGroupCheckbox-${group.id}`}
                            />
                          )}
                          name={`groupIDs[${idx}]`}
                          control={control}
                          rules={{ validate: validateGroups }}
                          defaultValue={false}
                        />
                      }
                      label={group.name}
                    />
                  ))}
                </Responsive>
              </div>
              <div className={classes.button}>
                <Button
                  variant="contained"
                  type="submit"
                  endIcon={<SaveIcon />}
                  color="primary"
                >
                  Save
                </Button>
              </div>
            </form>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CandidatesPreferences;
