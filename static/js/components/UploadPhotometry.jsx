import React, { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useParams, Link } from "react-router-dom";
import MUIDataTable from "mui-datatables";
import TextareaAutosize from "@material-ui/core/TextareaAutosize";
import Select from "@material-ui/core/Select";
import MenuItem from "@material-ui/core/MenuItem";
import Button from "@material-ui/core/Button";
import InputLabel from "@material-ui/core/InputLabel";
import FormControl from "@material-ui/core/FormControl";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import Box from "@material-ui/core/Box";
import Typography from "@material-ui/core/Typography";
import { makeStyles } from "@material-ui/core/styles";
import { useForm, Controller } from "react-hook-form";

import FormValidationError from "./FormValidationError";
import * as Actions from "../ducks/source";


const textAreaPlaceholderText = `mjd,flux,fluxerr,zp,magsys,instrument_id,filter
58001.,22.,1.,30.,ab,1,ztfg
58002.,23.,1.,30.,ab,1,ztfg
58003.,22.,1.,30.,ab,1,ztfg`;

const UploadPhotometryForm = () => {
  const dispatch = useDispatch();
  const { instrumentList } = useSelector((state) => state.instruments);
  const [showPreview, setShowPreview] = useState(false);
  const [csvData, setCsvData] = useState({});
  const [successMessage, setSuccessMessage] = useState("");
  const { id } = useParams();
  const { handleSubmit, errors, reset, control, getValues } = useForm();
  let formState = getValues();

  const validateCsvData = () => {
    setSuccessMessage(null);
    formState = getValues();
    if (!formState.csvData) {
      return "Missing CSV data";
    }
    const delim = new RegExp(formState.delimiter);
    let [header, ...dataRows] = formState.csvData.trim().split("\n");
    header = header.split(delim);
    dataRows = dataRows.map((row) => row.split(delim));
    const headerLength = header.length;
    if (!(headerLength >= 2)) {
      return "Invalid input: Too few columns";
    }
    if (!(dataRows.length >= 1)) {
      return "Invalid input: There must be a header row and one or more data rows";
    }
    if (!dataRows.every((row) => row.length === headerLength)) {
      return "Invalid input: All data rows must have the same number of columns as header row";
    }
    // eslint-disable-next-line no-restricted-syntax
    for (const col of ["mjd", "filter", "magsys"]) {
      if (!header.includes(col)) {
        return `Invalid input: Missing required column: ${col}`;
      }
    }
    if (!header.includes("flux") && !header.includes("mag")) {
      return "Invalid input: Missing required column: one of either mag or flux";
    }
    if (header.includes("flux") && (!header.includes("zp"))) {
      return "Invalid input: missing required column: zp";
    }
    if (header.includes("flux") && (!header.includes("fluxerr"))) {
      return "Invalid input: missing required column: fluxerr";
    }
    if (header.includes("mag") && (!header.includes("limiting_mag"))) {
      return "Invalid input: missing required column: limiting_mag";
    }
    if (formState.instrumentID === "multiple" && !header.includes("instrument_id")) {
      return "Invalid input: missing required column: instrument_id";
    }
    return true;
  };

  const handleClickPreview = async (data) => {
    let [header, ...dataRows] = data.csvData.trim().split("\n");
    const delim = new RegExp(data.delimiter);
    header = header.split(delim);
    dataRows = dataRows.map((row) => row.split(delim));
    setCsvData({
      columns: header,
      data: dataRows
    });
    setShowPreview(true);
  };

  const handleReset = () => {
    reset({
      delimiter: ",",
      csvData: "",
      instrumentID: "multiple"
    }, {
      dirty: false
    });
    setCsvData({});
  };

  const handleClickSubmit = async () => {
    formState = getValues();
    const data = {
      obj_id: id,
    };
    if (formState.instrumentID !== "multiple") {
      data.instrument_id = formState.instrumentID;
    }
    csvData.columns.forEach((col, idx) => {
      data[col] = csvData.data.map((row) => row[idx]);
    });
    const result = await dispatch(Actions.uploadPhotometry(data));
    if (result.status === "success") {
      handleReset();
      const rootURL = `${window.location.protocol}//${window.location.host}`;
      setSuccessMessage(`Upload successful. Your bulk upload ID is ${result.data.bulk_upload_id}
                        To delete these data, use a valid token to make a request of the form:
                        curl -X DELETE -i -H "Authorization: token <your_token_id>" \
                        ${rootURL}/api/photometry/bulk_delete/${result.data.bulk_upload_id}`);
    }
  };

  const useStyles = makeStyles((theme) => ({
    formControl: {
      margin: theme.spacing(1),
      minWidth: 120,
    }
  }));
  const classes = useStyles();

  return (
    <div>
      <Typography variant="h5">
        Upload photometry for source&nbsp;
        <Link to={`/source/${id}`} role="link">
          {id}
        </Link>
      </Typography>
      <Card>
        <CardContent>
          <form onSubmit={handleSubmit(handleClickPreview)}>
            <Box m={1}>
              {
                errors.instrumentID && (
                  <FormValidationError
                    message="Select an instrument"
                  />
                )
              }
              <FormControl variant="filled" className={classes.formControl}>
                <InputLabel id="instrumentSelectLabel">
                  Instrument
                </InputLabel>
                <Controller
                  as={(
                    <Select labelId="instrumentSelectLabel">
                      <MenuItem value="multiple" key={0}>
                        Multiple (requires instrument_id column below)
                      </MenuItem>
                      {
                        instrumentList.map((instrument) => (
                          <MenuItem value={instrument.id} key={instrument.id}>
                            {`${instrument.name} (ID: ${instrument.id})`}
                          </MenuItem>
                        ))
                      }
                    </Select>
                  )}
                  name="instrumentID"
                  rules={{ required: true }}
                  control={control}
                  defaultValue=""
                />
              </FormControl>
            </Box>
            <Box m={1}>
              <em>
                Required fields (flux-space):
                mjd,flux,fluxerr,zp,magsys,filter[,instrument_id]
                <br />
                Required fields (mag-space):
                mjd,mag,magerr,limiting_mag,magsys,filter[,instrument_id]
              </em>
            </Box>
            <Box component="span" m={1}>
              {
                errors.csvData && (
                  <FormValidationError
                    message={errors.csvData.message}
                  />
                )
              }
              <FormControl>
                <Controller
                  as={(
                    <TextareaAutosize
                      name="csvData"
                      placeholder={textAreaPlaceholderText}
                      style={{ height: "20em", width: "40em" }}
                    />
                  )}
                  name="csvData"
                  control={control}
                  rules={{ validate: validateCsvData }}
                />
              </FormControl>
            </Box>
            <Box component="span" m={1}>
              <FormControl>
                <InputLabel id="delimiter-label">Delimiter</InputLabel>
                <Controller
                  as={(
                    <Select labelId="delimiter-label">
                      <MenuItem value=",">
                        Comma
                      </MenuItem>
                      <MenuItem value={`\\s+`}>
                        Whitespace
                      </MenuItem>
                    </Select>
                  )}
                  name="delimiter"
                  control={control}
                  rules={{ required: true }}
                  defaultValue=","
                />
              </FormControl>
            </Box>
            <Box m={1}>
              <Box component="span" m={1}>
                <FormControl>
                  <Button
                    variant="contained"
                    type="submit"
                  >
                    Preview in Tabular Form
                  </Button>
                </FormControl>
              </Box>
              <Box component="span" m={1}>
                <FormControl>
                  <Button variant="contained" onClick={handleReset}>
                    Clear Form
                  </Button>
                </FormControl>
              </Box>
            </Box>
          </form>
        </CardContent>
      </Card>
      {
        (showPreview && csvData.columns) && (
          <div>
            <br />
            <br />
            <Card>
              <CardContent>
                <Box component="span" m={1}>
                  <MUIDataTable
                    title="Data Preview"
                    columns={csvData.columns}
                    data={csvData.data}
                    options={(
                      {
                        search: false,
                        filter: false,
                        selectableRows: "none",
                        download: false,
                        print: false
                      }
                    )}
                  />
                </Box>
              </CardContent>
            </Card>
            <br />
            <Box component="span" m={1}>
              <Button variant="contained" onClick={handleClickSubmit}>
                Upload Photometry
              </Button>
            </Box>
          </div>
        )
      }
      {
        (successMessage && !formState.dirty) && (
          <div style={{ whiteSpace: "pre-line" }}>
            <br />
            <font color="blue">
              {successMessage}
            </font>
          </div>
        )
      }
    </div>
  );
};

export default UploadPhotometryForm;
