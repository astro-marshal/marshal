import React, { useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import PropTypes from "prop-types";

import IconButton from "@material-ui/core/IconButton";
import VisibilityIcon from "@material-ui/icons/Visibility";
import VisibilityOffIcon from "@material-ui/icons/VisibilityOff";
import Tooltip from "@material-ui/core/Tooltip";

import * as Actions from "../ducks/rejected_candidates";

const ButtonVisible = (objID) => {
  const dispatch = useDispatch();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const handleSubmit = async () => {
    setIsSubmitting(true);
    await dispatch(Actions.addToRejected(objID));
    setIsSubmitting(false);
  };
  return (
    <Tooltip title="click to hide candidate from scanning page">
      <IconButton
        onClick={handleSubmit}
        data-testid={`rejected-visible_${objID}`}
        disabled={isSubmitting}
      >
        <VisibilityIcon />
      </IconButton>
    </Tooltip>
  );
};

const ButtonInvisible = (objID) => {
  const dispatch = useDispatch();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const handleSubmit = async () => {
    setIsSubmitting(true);
    await dispatch(Actions.removeFromRejected(objID));
    setIsSubmitting(false);
  };

  return (
    <Tooltip title="click to make candidate visible on scanning page">
      <IconButton
        onClick={handleSubmit}
        data-testid={`rejected_invisible_${objID}`}
        disabled={isSubmitting}
      >
        <VisibilityOffIcon />
      </IconButton>
    </Tooltip>
  );
};

const RejectButton = ({ objID }) => {
  const { rejected_candidates } = useSelector(
    (state) => state.rejected_candidates
  );

  if (!objID) {
    return null;
  }
  if (rejected_candidates.includes(objID)) {
    return ButtonInvisible(objID);
  }
  return ButtonVisible(objID);
};

RejectButton.propTypes = {
  objID: PropTypes.string.isRequired,
};

export default RejectButton;
