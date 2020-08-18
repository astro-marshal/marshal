import React from "react";
import PropTypes from "prop-types";
import { Link } from "react-router-dom";

import Box from "@material-ui/core/Box";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import ListItemText from "@material-ui/core/ListItemText";
import Typography from "@material-ui/core/Typography";

const GroupList = ({ title, groups }) => (
  <Box p={1} border="1px solid #ddd" height="100%" padding="10px">
    <Typography variant="h6">{title}</Typography>

    <List dense>
      {groups &&
        groups
          .filter((group) => !group.single_user_group)
          .map((group) => (
            <Link to={`/group/${group.id}`} key={group.id}>
              <ListItem>
                <ListItemText primary={group.name} />
              </ListItem>
            </Link>
          ))}
    </List>
  </Box>
);

GroupList.propTypes = {
  title: PropTypes.string.isRequired,
  groups: PropTypes.arrayOf(PropTypes.object),
};
GroupList.defaultProps = {
  groups: [],
};

export default GroupList;
