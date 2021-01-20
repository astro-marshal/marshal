import React, { useState, useEffect } from "react";
import { useSelector, useDispatch } from "react-redux";

import Badge from "@material-ui/core/Badge";
import MUINotificationsIcon from "@material-ui/icons/NotificationsOutlined";
import IconButton from "@material-ui/core/IconButton";
import Popover from "@material-ui/core/Popover";
import { makeStyles } from "@material-ui/core/styles";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import Divider from "@material-ui/core/Divider";
import Button from "@material-ui/core/Button";

import * as userNotificationsActions from "../ducks/userNotifications";

const useStyles = makeStyles((theme) => ({
  root: {
    width: "100%",
    maxWidth: 360,
    backgroundColor: theme.palette.background.paper,
  },
  readMessage: {
    fontWeight: "normal",
  },
  unreadMessage: {
    fontWeight: "bold",
  },
  centered: {
    display: "flex",
    justifyContent: "center",
  },
}));

const Notifications = () => {
  const classes = useStyles();
  const dispatch = useDispatch();
  const notifications = useSelector((state) => state.userNotifications);

  const [unreadCount, setUnreadCount] = useState(
    notifications ? notifications.filter((n) => !n.read).length : 0
  );

  useEffect(() => {
    if (notifications === null) {
      dispatch(userNotificationsActions.fetchNotifications());
    } else {
      setUnreadCount(notifications.filter((n) => !n.read).length);
    }
  }, [dispatch, notifications]);

  // Popover logic
  const [anchorEl, setAnchorEl] = React.useState(null);
  const handleClickOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };
  const handleClose = () => {
    setAnchorEl(null);
  };
  const open = Boolean(anchorEl);

  const deleteAllNotifications = () => {
    dispatch(userNotificationsActions.deleteAllNotifications());
    handleClose();
  };

  const markAllRead = () => {
    dispatch(userNotificationsActions.updateAllNotifications({ read: true }));
  };

  const markRead = (notificationID) => {
    dispatch(
      userNotificationsActions.updateNotification({
        notificationID,
        data: { read: true },
      })
    );
  };

  const deleteNotification = (notificationID) => {
    dispatch(userNotificationsActions.deleteNotification(notificationID));
  };

  return (
    <>
      <IconButton
        onClick={handleClickOpen}
        style={{ marginTop: "0.6rem", marginRight: "1rem" }}
      >
        <Badge
          badgeContent={unreadCount}
          color={unreadCount > 0 ? "secondary" : "primary"}
        >
          <MUINotificationsIcon fontSize="large" color="primary" />
        </Badge>
      </IconButton>
      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{
          vertical: "bottom",
          horizontal: "center",
        }}
        transformOrigin={{
          vertical: "top",
          horizontal: "center",
        }}
      >
        <div className={classes.root}>
          <List className={classes.root}>
            {notifications &&
              notifications.map((notification) => (
                <>
                  <ListItem
                    key={notification.id}
                    button={!!notification.url}
                    component={notification.url ? "a" : "li"}
                    href={notification.url ? notification.url : "#"}
                    className={
                      notification.read
                        ? classes.readMessage
                        : classes.unreadMessage
                    }
                    onClick={() => {
                      markRead(notification.id);
                    }}
                  >
                    {notification.text}
                  </ListItem>
                  <ListItem className={classes.centered}>
                    <Button
                      size="small"
                      onClick={() => {
                        markRead(notification.id);
                      }}
                    >
                      Mark read
                    </Button>
                    |
                    <Button
                      size="small"
                      onClick={() => {
                        deleteNotification(notification.id);
                      }}
                    >
                      Delete
                    </Button>
                  </ListItem>
                  <Divider />
                </>
              ))}
            {notifications && notifications.length > 0 && (
              <ListItem className={classes.centered}>
                <Button onClick={markAllRead}>Mark all read</Button>|
                <Button onClick={deleteAllNotifications}>Delete all</Button>
              </ListItem>
            )}
            {(!notifications || notifications.length === 0) && (
              <ListItem className={classes.centered}>
                <em>No notifications</em>
              </ListItem>
            )}
          </List>
        </div>
      </Popover>
    </>
  );
};

export default Notifications;