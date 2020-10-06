import React, { useEffect, Suspense, useState } from "react";
import { useSelector, useDispatch } from "react-redux";
import { useHistory } from "react-router-dom";
import PropTypes from "prop-types";

import Paper from "@material-ui/core/Paper";
import Typography from "@material-ui/core/Typography";
import {
  makeStyles,
  createMuiTheme,
  MuiThemeProvider,
  useTheme,
} from "@material-ui/core/styles";
import useMediaQuery from "@material-ui/core/useMediaQuery";
import Button from "@material-ui/core/Button";
import IconButton from "@material-ui/core/IconButton";
import CircularProgress from "@material-ui/core/CircularProgress";
import OpenInNewIcon from "@material-ui/icons/OpenInNew";
import ArrowUpward from "@material-ui/icons/ArrowUpward";
import ArrowDownward from "@material-ui/icons/ArrowDownward";
import SortIcon from "@material-ui/icons/Sort";
import Chip from "@material-ui/core/Chip";
import Box from "@material-ui/core/Box";
import Tooltip from "@material-ui/core/Tooltip";
import MUIDataTable from "mui-datatables";

import * as candidatesActions from "../ducks/candidates";
import ThumbnailList from "./ThumbnailList";
// import CandidateCommentList from "./CandidateCommentList";
import SaveCandidateButton from "./SaveCandidateButton";
import FilterCandidateList from "./FilterCandidateList";
import CandidateAnnotationsList, {
  getAnnotationValueString,
} from "./CandidateAnnotationsList";
import AddSourceGroup from "./AddSourceGroup";

const VegaPlot = React.lazy(() =>
  import(/* webpackChunkName: "VegaPlot" */ "./VegaPlot")
);

const useStyles = makeStyles((theme) => ({
  candidateListContainer: {
    padding: "1rem",
  },
  table: {
    marginTop: "1rem",
  },
  title: {
    marginBottom: "0.625rem",
  },
  pages: {
    margin: "1rem",
    "& > div": {
      display: "inline-block",
      margin: "1rem",
    },
  },
  spinnerDiv: {
    paddingTop: "2rem",
  },
  itemPaddingBottom: {
    paddingBottom: "0.1rem",
  },
  infoItem: {
    display: "flex",
    "& > span": {
      paddingLeft: "0.25rem",
      paddingBottom: "0.1rem",
    },
    flexFlow: "row wrap",
  },
  saveCandidateButton: {
    margin: "0.5rem 0",
  },
  thumbnails: (props) => ({
    minWidth: props.thumbnailsMinWidth,
  }),
  info: (props) => ({
    fontSize: "0.875rem",
    minWidth: props.infoMinWidth,
    maxWidth: props.infoMaxWidth,
  }),
  annotations: (props) => ({
    minWidth: props.annotationsMinWidth,
  }),
  sortButtton: {
    verticalAlign: "top",
    "&:hover": {
      color: theme.palette.primary.main,
    },
  },
  chip: {
    margin: theme.spacing(0.5),
  },
}));

// Hide built-in pagination and tweak responsive column widths
const getMuiTheme = (theme) =>
  createMuiTheme({
    overrides: {
      // MUIDataTableFooter: {
      //   root: {
      //     display: "none",
      //   },
      // },
      MUIDataTableBodyCell: {
        root: {
          padding: `${theme.spacing(1)}px ${theme.spacing(
            0.5
          )}px ${theme.spacing(1)}px ${theme.spacing(1)}px`,
        },
        stackedHeader: {
          verticalAlign: "top",
        },
        stackedCommon: {
          [theme.breakpoints.up("xs")]: { width: "calc(100%)" },
          "&$stackedHeader": {
            display: "none",
            overflowWrap: "break-word",
          },
        },
      },
    },
  });

const defaultNumPerPage = 25;

const CustomSortToolbar = ({
  selectedAnnotationItem,
  rowsPerPage,
  setQueryInProgress,
  loaded,
}) => {
  const classes = useStyles();

  const [ascending, setAscending] = useState(null);
  const dispatch = useDispatch();
  useEffect(() => {
    setAscending(null);
  }, [selectedAnnotationItem]);

  // ESLint rule is disabled below because we don't want to reload data on a new
  // annotation item select every time until the sort button is actually clicked
  useEffect(() => {
    const dispatchSort = async () => {
      const data = {
        pageNumber: 1,
        numPerPage: rowsPerPage,
        sortByAnnotationOrigin: selectedAnnotationItem.origin,
        sortByAnnotationKey: selectedAnnotationItem.key,
        sortByAnnotationOrder: ascending ? "asc" : "desc",
      };
      await dispatch(candidatesActions.fetchCandidates(data));
      setQueryInProgress(false);
    };

    if (ascending !== null) {
      dispatchSort();
    }
  }, [ascending, dispatch, rowsPerPage, setQueryInProgress]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSort = () => {
    setQueryInProgress(true);
    setAscending(ascending === null ? true : !ascending);
  };

  // Wait until sorted data is received before rendering the toolbar
  return loaded ? (
    <Tooltip title="Sort on Selected Annotation">
      <span>
        <IconButton
          onClick={handleSort}
          disabled={selectedAnnotationItem === null}
          className={classes.sortButtton}
        >
          <span>
            <SortIcon />
            {ascending !== null && ascending && <ArrowUpward />}
            {ascending !== null && !ascending && <ArrowDownward />}
          </span>
        </IconButton>
      </span>
    </Tooltip>
  ) : (
    <span />
  );
};

CustomSortToolbar.propTypes = {
  selectedAnnotationItem: PropTypes.shape({
    origin: PropTypes.string.isRequired,
    key: PropTypes.string.isRequired,
  }),
  setQueryInProgress: PropTypes.func.isRequired,
  rowsPerPage: PropTypes.number.isRequired,
  loaded: PropTypes.bool.isRequired,
};

CustomSortToolbar.defaultProps = {
  selectedAnnotationItem: null,
};

const CandidateList = () => {
  const history = useHistory();
  const [queryInProgress, setQueryInProgress] = useState(false);
  const [rowsPerPage, setRowsPerPage] = useState(defaultNumPerPage);
  // Maintain the three thumbnails in a row for larger screens
  const largeScreen = useMediaQuery((theme) => theme.breakpoints.up("md"));
  const thumbnailsMinWidth = largeScreen ? "30rem" : 0;
  const infoMinWidth = largeScreen ? "7rem" : 0;
  const infoMaxWidth = "14rem";
  const annotationsMinWidth = largeScreen ? "10rem" : 0;
  const classes = useStyles({
    thumbnailsMinWidth,
    infoMinWidth,
    infoMaxWidth,
    annotationsMinWidth,
  });
  const theme = useTheme();
  const {
    candidates,
    pageNumber,
    lastPage,
    totalMatches,
    numberingStart,
    numberingEnd,
    selectedAnnotationItem,
  } = useSelector((state) => state.candidates);

  const userAccessibleGroups = useSelector(
    (state) => state.groups.userAccessible
  );

  const dispatch = useDispatch();

  useEffect(() => {
    if (candidates === null) {
      setQueryInProgress(true);
      dispatch(
        candidatesActions.fetchCandidates({ numPerPage: defaultNumPerPage })
      );
    } else {
      setQueryInProgress(false);
    }
  }, [candidates, dispatch]);

  const candidateHasAnnotationItem = (candidateObj) => {
    const annotation = candidateObj.annotations.find(
      (a) => a.origin === selectedAnnotationItem.origin
    );
    if (annotation === undefined) {
      return false;
    }
    return selectedAnnotationItem.key in annotation.data;
  };

  const getCandidateAnnotationValue = (candidateObj) => {
    const annotation = candidateObj.annotations.find(
      (a) => a.origin === selectedAnnotationItem.origin
    );
    return getAnnotationValueString(
      annotation.data[selectedAnnotationItem.key]
    );
  };

  const renderThumbnails = (dataIndex) => {
    const candidateObj = candidates[dataIndex];
    return (
      <div className={classes.thumbnails}>
        <ThumbnailList
          ra={candidateObj.ra}
          dec={candidateObj.dec}
          thumbnails={candidateObj.thumbnails}
          size="9rem"
        />
      </div>
    );
  };

  const renderInfo = (dataIndex) => {
    const candidateObj = candidates[dataIndex];
    return (
      <div className={classes.info}>
        <span className={classes.itemPaddingBottom}>
          <b>ID:</b>&nbsp;
          <a
            href={`/candidate/${candidateObj.id}`}
            target="_blank"
            rel="noreferrer"
          >
            {candidateObj.id}&nbsp;
            <OpenInNewIcon fontSize="inherit" />
          </a>
        </span>
        <br />
        {candidateObj.is_source ? (
          <div>
            <div className={classes.itemPaddingBottom}>
              <Chip
                size="small"
                label="Previously Saved"
                clickable
                onClick={() => history.push(`/source/${candidateObj.id}`)}
                onDelete={() =>
                  window.open(`/source/${candidateObj.id}`, "_blank")
                }
                deleteIcon={<OpenInNewIcon />}
                color="primary"
              />
            </div>
            <div className={classes.saveCandidateButton}>
              <AddSourceGroup
                source={{
                  id: candidateObj.id,
                  currentGroupIds: candidateObj.saved_groups.map((g) => g.id),
                }}
                userGroups={userAccessibleGroups}
              />
            </div>
            <div className={classes.infoItem}>
              <b>Saved groups: </b>
              <span>
                {candidateObj.saved_groups.map((group) => (
                  <Chip
                    label={
                      group.nickname
                        ? group.nickname.substring(0, 15)
                        : group.name.substring(0, 15)
                    }
                    key={group.id}
                    size="small"
                    className={classes.chip}
                  />
                ))}
              </span>
            </div>
          </div>
        ) : (
          <div>
            <Chip
              size="small"
              label="NOT SAVED"
              className={classes.itemPaddingBottom}
            />
            <br />
            <div className={classes.saveCandidateButton}>
              <SaveCandidateButton
                candidate={candidateObj}
                userGroups={userAccessibleGroups}
              />
            </div>
          </div>
        )}
        {candidateObj.last_detected && (
          <div className={classes.infoItem}>
            <b>Last detected: </b>
            <span>
              {String(candidateObj.last_detected).split(".")[0].split("T")[1]}
              &nbsp;&nbsp;
              {String(candidateObj.last_detected).split(".")[0].split("T")[0]}
            </span>
          </div>
        )}
        <div className={classes.infoItem}>
          <b>Coordinates: </b>
          <span>
            {candidateObj.ra}&nbsp;&nbsp;{candidateObj.dec}
          </span>
        </div>
        <div className={classes.infoItem}>
          <b>Gal. Coords (l,b): </b>
          <span>
            {candidateObj.gal_lon.toFixed(3)}&nbsp;&nbsp;
            {candidateObj.gal_lat.toFixed(3)}
          </span>
        </div>
        {selectedAnnotationItem !== null &&
          candidateHasAnnotationItem(candidateObj) && (
            <div className={classes.infoItem}>
              <b>
                {selectedAnnotationItem.key} ({selectedAnnotationItem.origin}):
              </b>
              <span>{getCandidateAnnotationValue(candidateObj)}</span>
            </div>
          )}
      </div>
    );
  };

  const renderPhotometry = (dataIndex) => {
    const candidateObj = candidates[dataIndex];
    return (
      <Suspense fallback={<CircularProgress />}>
        <VegaPlot dataUrl={`/api/sources/${candidateObj.id}/photometry`} />
      </Suspense>
    );
  };

  const renderAutoannotations = (dataIndex) => {
    const candidateObj = candidates[dataIndex];
    return (
      <div className={classes.annotations}>
        {candidateObj.annotations && (
          <CandidateAnnotationsList annotations={candidateObj.annotations} />
        )}
      </div>
    );
  };

  const handlePageChange = async (page, numPerPage) => {
    setQueryInProgress(true);
    // API takes 1-indexed page number
    const data = { pageNumber: page + 1, numPerPage };
    await dispatch(candidatesActions.fetchCandidates(data));
    setQueryInProgress(false);
  };

  const handleTableChange = (action, tableState) => {
    setRowsPerPage(tableState.rowsPerPage);
    switch (action) {
      case "changePage":
      case "changeRowsPerPage":
        handlePageChange(tableState.page, tableState.rowsPerPage);
        break;
      default:
    }
  };

  const columns = [
    {
      name: "Images",
      label: "Images",
      options: {
        customBodyRenderLite: renderThumbnails,
        sort: false,
        filter: false,
      },
    },
    {
      name: "Info",
      label: "Info",
      options: {
        customBodyRenderLite: renderInfo,
        filter: false,
      },
    },
    {
      name: "Photometry",
      label: "Photometry",
      options: {
        customBodyRenderLite: renderPhotometry,
        sort: false,
        filter: false,
      },
    },
    {
      name: "Autoannotations",
      label: "Autoannotations",
      options: {
        customBodyRenderLite: renderAutoannotations,
        sort: false,
        filter: false,
      },
    },
  ];

  return (
    <Paper elevation={1}>
      <div className={classes.candidateListContainer}>
        <Typography variant="h6" className={classes.title}>
          Scan candidates for sources
        </Typography>
        <FilterCandidateList
          userAccessibleGroups={userAccessibleGroups}
          pageNumber={pageNumber}
          numberingStart={numberingStart}
          numberingEnd={numberingEnd}
          lastPage={lastPage}
          totalMatches={totalMatches}
          setQueryInProgress={setQueryInProgress}
        />
        <Box
          display={queryInProgress ? "block" : "none"}
          className={classes.spinnerDiv}
        >
          <CircularProgress />
        </Box>
        <Box display={queryInProgress ? "none" : "block"}>
          <MuiThemeProvider theme={getMuiTheme(theme)}>
            <MUIDataTable
              // Reset key to reset page number
              // https://github.com/gregnb/mui-datatables/issues/1166
              key={`table_${pageNumber}`}
              columns={columns}
              data={candidates !== null ? candidates : []}
              className={classes.table}
              options={{
                responsive: "vertical",
                filter: true,
                filterType: "custom",
                confirmFilters: true,
                search: false,
                print: false,
                download: false,
                sort: false,
                count: totalMatches,
                selectableRows: "none",
                enableNestedDataAccess: ".",
                rowsPerPage,
                rowsPerPageOptions: [1, 25, 50, 75, 100, 200],
                jumpToPage: true,
                serverSide: true,
                page: pageNumber - 1,
                pagination: true,
                onTableChange: handleTableChange,
                // eslint-disable-next-line react/display-name
                customToolbar: () => (
                  <CustomSortToolbar
                    selectedAnnotationItem={selectedAnnotationItem}
                    rowsPerPage={rowsPerPage}
                    setQueryInProgress={setQueryInProgress}
                    loaded={!queryInProgress}
                  />
                ),
              }}
            />
          </MuiThemeProvider>
        </Box>
      </div>
      <div className={classes.pages}>
        <div>
          <Button
            variant="contained"
            onClick={() => {
              window.scrollTo({ top: 0 });
            }}
            size="small"
          >
            Back to top <ArrowUpward />
          </Button>
        </div>
      </div>
    </Paper>
  );
};

export default CandidateList;
