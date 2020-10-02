import React from "react";
import PropTypes from "prop-types";
import { makeStyles, useTheme } from "@material-ui/core/styles";
import Select from "@material-ui/core/Select";
import MenuItem from "@material-ui/core/MenuItem";
import InputLabel from "@material-ui/core/InputLabel";
import FormControl from "@material-ui/core/FormControl";
import Chip from "@material-ui/core/Chip";
import Input from "@material-ui/core/Input";

const ITEM_HEIGHT = 48;
const ITEM_PADDING_TOP = 8;

const MenuProps = {
  PaperProps: {
    style: {
      maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
      width: 250,
    },
  },
};

const useStyles = makeStyles((theme) => ({
  formControl: {
    marginTop: theme.spacing(1),
    minWidth: 120,
  },
  chips: {
    display: "flex",
    flexWrap: "wrap",
  },
  chip: {
    margin: 2,
  },
  textarea: {
    "::-webkit-input-placeholder": {
      opacity: 0.2,
    },
    "::-moz-placeholder": {
      opacity: 0.2,
    },
    ":-ms-input-placeholder": {
      opacity: 0.2,
    },
  },
}));

const getStyles = (groupID, groupIDs = [], theme) => ({
  fontWeight:
    groupIDs.indexOf(groupID) === -1
      ? theme.typography.fontWeightRegular
      : theme.typography.fontWeightMedium,
});

const GroupShareSelect = ({
  groupList,
  groupIDs,
  setGroupIDs,
  maxGroups = 2,
}) => {
  const classes = useStyles();
  const theme = useTheme();

  const handleChange = (event) => {
    setGroupIDs(event.target.value);
  };

  const groupIDToName = {};
  groupList.forEach((group) => {
    groupIDToName[group.id] = group.nickname ? group.nickname : group.name;
  });

  return (
    <FormControl className={classes.formControl}>
      <InputLabel id="select-groups-label">Share Data With</InputLabel>
      <Select
        labelId="select-groups-label"
        id="selectGroups"
        multiple
        value={groupIDs}
        onChange={handleChange}
        input={<Input id="selectGroupsChip" />}
        renderValue={(selected) => {
          const numSelected = selected.length;
          if (numSelected <= maxGroups) {
            return (
              <div className={classes.chips}>
                {selected.map((value) => (
                  <Chip
                    key={value}
                    label={groupIDToName[value]}
                    className={classes.chip}
                  />
                ))}
              </div>
            );
          }
          return (
            <div className={classes.chips}>
              <Chip
                key="chip_groups_summary"
                label={`${numSelected} groups`}
                className={classes.chip}
              />
            </div>
          );
        }}
        MenuProps={MenuProps}
      >
        {groupList.map((group) => (
          <MenuItem
            key={group.id}
            value={group.id}
            style={getStyles(group.name, groupIDs, theme)}
          >
            {group.name}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
};

GroupShareSelect.propTypes = {
  groupList: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number,
      name: PropTypes.string,
    })
  ).isRequired,
  groupIDs: PropTypes.arrayOf(PropTypes.number).isRequired,
  setGroupIDs: PropTypes.func.isRequired,
  maxGroups: PropTypes.number,
};

GroupShareSelect.defaultProps = {
  maxGroups: 2,
};

export default GroupShareSelect;
