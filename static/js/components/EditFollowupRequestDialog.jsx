import React, { useState } from "react";
import { useDispatch } from "react-redux";
import PropTypes from "prop-types";
import Dialog from "@material-ui/core/Dialog";
import DialogContent from "@material-ui/core/DialogContent";
import Form from "@rjsf/material-ui";
import * as Actions from "../ducks/source";

const EditFollowupRequestDialog = ({
  followupRequest,
  instrumentFormParams,
}) => {
  const dispatch = useDispatch();
  const [open, setOpen] = useState(false);

  const handleClickOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleSubmit = ({ formData }) => {
    const json = {
      instrument_id: followupRequest.instrument.id,
      obj_id: followupRequest.obj_id,
      payload: formData,
    };
    dispatch(Actions.editFollowupRequest(json, followupRequest.id));
    handleClose();
  };

  return (
    <span key={followupRequest.id}>
      <button
        type="button"
        onClick={handleClickOpen}
        name={`editRequest_${followupRequest.id}`}
      >
        Edit
      </button>
      <Dialog open={open} onClose={handleClose} style={{ position: "fixed" }}>
        <DialogContent>
          <Form
            schema={
              instrumentFormParams[followupRequest.instrument.id].formSchema
            }
            uiSchema={
              instrumentFormParams[followupRequest.instrument.id].uiSchema
            }
            onSubmit={handleSubmit}
          />
        </DialogContent>
      </Dialog>
    </span>
  );
};

EditFollowupRequestDialog.propTypes = {
  followupRequest: PropTypes.shape({
    requester: PropTypes.shape({
      id: PropTypes.number,
      username: PropTypes.string,
    }),
    instrument: PropTypes.shape({
      id: PropTypes.number,
      name: PropTypes.string,
    }),
    start_date: PropTypes.string,
    end_date: PropTypes.string,
    priority: PropTypes.string,
    status: PropTypes.string,
    obj_id: PropTypes.string,
    id: PropTypes.number,
  }).isRequired,
  instrumentFormParams: PropTypes.shape({
    formSchema: PropTypes.objectOf(PropTypes.any),
    uiSchema: PropTypes.objectOf(PropTypes.any),
    implementedMethods: PropTypes.objectOf(PropTypes.any),
  }).isRequired,
};

export default EditFollowupRequestDialog;
