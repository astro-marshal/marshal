import React from "react";
import PropTypes from "prop-types";

import { useDispatch } from "react-redux";
import Button from "@material-ui/core/Button";
import DeleteIcon from "@material-ui/icons/Delete";
import IconButton from "@material-ui/core/IconButton";

import { showNotification } from "baselayer/components/Notifications";

import * as groupActions from "../ducks/group";
import * as groupsActions from "../ducks/groups";

const ManageUserButtons = ({ group, loadedId, user, isAdmin }) => {
  const dispatch = useDispatch();

  let numAdmins = 0;
  group?.users?.forEach((groupUser) => {
    if (groupUser?.admin) {
      numAdmins += 1;
    }
  });

  const toggleUserAdmin = async (usr) => {
    const result = await dispatch(
      groupsActions.updateGroupUser(loadedId, {
        userID: usr.id,
        admin: !isAdmin(usr),
      })
    );
    if (result.status === "success") {
      dispatch(
        showNotification(
          "User admin status for this group successfully updated."
        )
      );
      dispatch(groupActions.fetchGroup(loadedId));
    }
  };
  return (
    <div>
      <Button
        size="small"
        onClick={() => {
          toggleUserAdmin(user);
        }}
        disabled={isAdmin(user) && numAdmins === 1}
      >
        <span style={{ whiteSpace: "nowrap" }}>
          {isAdmin(user) ? "Revoke admin status" : "Grant admin status"}
        </span>
      </Button>
      <IconButton
        edge="end"
        aria-label="delete"
        data-testid={`delete-${user.username}`}
        onClick={() =>
          dispatch(
            groupsActions.deleteGroupUser({
              userID: user.id,
              group_id: group.id,
            })
          )
        }
        disabled={isAdmin(user) && numAdmins === 1}
      >
        <DeleteIcon />
      </IconButton>
    </div>
  );
};

ManageUserButtons.propTypes = {
  loadedId: PropTypes.number.isRequired,
  user: PropTypes.shape({
    id: PropTypes.number,
    username: PropTypes.string,
  }).isRequired,
  isAdmin: PropTypes.func.isRequired,
  group: PropTypes.shape(PropTypes.object).isRequired,
};

export default ManageUserButtons;
