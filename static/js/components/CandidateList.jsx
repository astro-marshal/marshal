import React, { useEffect, Suspense } from "react";
import { useSelector, useDispatch } from "react-redux";
import { Link } from "react-router-dom";

import Paper from "@material-ui/core/Paper";
import Typography from "@material-ui/core/Typography";
import { makeStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import Button from "@material-ui/core/Button";

import * as candidatesActions from "../ducks/candidates";
import ThumbnailList from "./ThumbnailList";
import CandidateCommentList from "./CandidateCommentList";
import SaveCandidateButton from "./SaveCandidateButton";
import FilterCandidateList from "./FilterCandidateList";

const VegaPlot = React.lazy(() =>
  import(/* webpackChunkName: "VegaPlot" */ "./VegaPlot")
);

const useStyles = makeStyles(() => ({
  candidateListContainer: {
    padding: "1rem",
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
}));

const CandidateList = () => {
  const classes = useStyles();

  const {
    candidates,
    pageNumber,
    lastPage,
    totalMatches,
    numberingStart,
    numberingEnd,
  } = useSelector((state) => state.candidates);

  const userGroups = useSelector((state) => state.groups.user);

  const dispatch = useDispatch();

  useEffect(() => {
    if (candidates === null) {
      dispatch(candidatesActions.fetchCandidates());
    }
  }, [candidates, dispatch]);

  const handleClickNextPage = () => {
    dispatch(candidatesActions.fetchCandidates({ pageNumber: pageNumber + 1 }));
  };

  const handleClickPreviousPage = () => {
    dispatch(candidatesActions.fetchCandidates({ pageNumber: pageNumber - 1 }));
  };

  return (
    <Paper elevation={1}>
      <div className={classes.candidateListContainer}>
        <Typography variant="h6" className={classes.title}>
          Scan candidates for sources
        </Typography>
        <FilterCandidateList
          userGroups={userGroups}
          handleClickNextPage={handleClickNextPage}
          handleClickPreviousPage={handleClickPreviousPage}
          pageNumber={pageNumber}
          numberingStart={numberingStart}
          numberingEnd={numberingEnd}
          lastPage={lastPage}
          totalMatches={totalMatches}
        />
        <Table className={classes.table}>
          <TableHead>
            <TableRow>
              <TableCell>Last detected</TableCell>
              <TableCell>Images</TableCell>
              <TableCell>Info</TableCell>
              <TableCell>Photometry</TableCell>
              <TableCell>Autoannotations</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {!!candidates &&
              candidates.map((candidateObj) => {
                const thumbnails = candidateObj.thumbnails.filter(
                  (t) => t.type !== "dr8"
                );
                return (
                  <TableRow key={candidateObj.id}>
                    <TableCell>
                      {candidateObj.last_detected && (
                        <div>
                          <div>
                            {
                              String(candidateObj.last_detected)
                                .split(".")[0]
                                .split("T")[1]
                            }
                          </div>
                          <div>
                            {
                              String(candidateObj.last_detected)
                                .split(".")[0]
                                .split("T")[0]
                            }
                          </div>
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      <ThumbnailList
                        ra={candidateObj.ra}
                        dec={candidateObj.dec}
                        thumbnails={thumbnails}
                        size="8rem"
                      />
                    </TableCell>
                    <TableCell>
                      ID:&nbsp;
                      <Link to={`/candidate/${candidateObj.id}`}>
                        {candidateObj.id}
                      </Link>
                      <br />
                      {candidateObj.is_source ? (
                        <div>
                          <Link
                            to={`/source/${candidateObj.id}`}
                            style={{
                              color: "red",
                              texTableCellecoration: "underline",
                            }}
                          >
                            Previously Saved
                          </Link>
                        </div>
                      ) : (
                        <div>
                          NOT SAVED
                          <br />
                          <SaveCandidateButton
                            candidate={candidateObj}
                            userGroups={userGroups}
                          />
                        </div>
                      )}
                      <b>Coordinates</b>
                      :&nbsp;
                      {candidateObj.ra}
                      &nbsp;
                      {candidateObj.dec}
                      <br />
                      Gal. Coords (l,b):&nbsp;
                      {candidateObj.gal_lon.toFixed(1)}, &nbsp;
                      {candidateObj.gal_lat.toFixed(1)}
                      <br />
                    </TableCell>
                    <TableCell>
                      <Suspense fallback={<div>Loading plot...</div>}>
                        <VegaPlot
                          dataUrl={`/api/sources/${candidateObj.id}/photometry`}
                        />
                      </Suspense>
                    </TableCell>
                    <TableCell>
                      {candidateObj.comments && (
                        <CandidateCommentList
                          comments={candidateObj.comments}
                        />
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
          </TableBody>
        </Table>
      </div>
      <div className={classes.pages}>
        <div>
          <Button
            variant="contained"
            onClick={handleClickPreviousPage}
            disabled={pageNumber === 1}
            size="small"
          >
            Previous Page
          </Button>
        </div>
        <div>
          <i>
            Displaying&nbsp;
            {numberingStart}-{numberingEnd}
            &nbsp; of&nbsp;
            {totalMatches}
            &nbsp; candidates.
          </i>
        </div>
        <div>
          <Button
            variant="contained"
            onClick={handleClickNextPage}
            disabled={lastPage}
            size="small"
          >
            Next Page
          </Button>
        </div>
      </div>
    </Paper>
  );
};

export default CandidateList;
