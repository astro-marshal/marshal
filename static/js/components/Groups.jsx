import React from "react";
import { useSelector } from "react-redux";

import { makeStyles } from "@material-ui/core/styles";
import Paper from "@material-ui/core/Paper";

import GroupManagement from "./GroupManagement";
import GroupList from "./GroupList";
import NewGroupForm from "./NewGroupForm";
import NonMemberGroupList from "./NonMemberGroupList";

const useStyles = makeStyles(() => ({
  // Hide drag handle icon since this isn't the home page
  widgetIcon: {
    display: "none",
  },
  widgetPaperDiv: {
    padding: "1rem",
    height: "100%",
  },
  widgetPaperFillSpace: {
    height: "100%",
  },
}));

const Groups = () => {
  const classes = useStyles();
  const { roles } = useSelector((state) => state.profile);
  const { user: userGroups, all: allGroups } = useSelector(
    (state) => state.groups
  );

  if (userGroups.length === 0 || allGroups === null) {
    return <h3>Loading...</h3>;
  }

  const nonMemberGroups = allGroups.filter(
    (g) => !g.single_user_group && !userGroups.map((ug) => ug.id).includes(g.id)
  );

  return (
    <div>
      <Paper elevation={1}>
        <GroupList title="My Groups" groups={userGroups} classes={classes} />
      </Paper>
      {!!nonMemberGroups.length && (
        <>
          <br />
          <NonMemberGroupList groups={nonMemberGroups} />
        </>
      )}
      <NewGroupForm />
      {roles.includes("Super admin") && <GroupManagement />}
    </div>
  );
};

export default Groups;
