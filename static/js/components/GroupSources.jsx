import React, { useEffect, Suspense } from "react";
import PropTypes from "prop-types";
import { useSelector, useDispatch } from "react-redux";

import TableCell from "@material-ui/core/TableCell";
import TableRow from "@material-ui/core/TableRow";

import Typography from "@material-ui/core/Typography";
import IconButton from "@material-ui/core/IconButton";
import Grid from "@material-ui/core/Grid";
import Chip from "@material-ui/core/Chip";
import Link from "@material-ui/core/Link";
import PictureAsPdfIcon from "@material-ui/icons/PictureAsPdf";
import CircularProgress from "@material-ui/core/CircularProgress";

import MUIDataTable from "mui-datatables";
import { makeStyles } from "@material-ui/core/styles";

import Tooltip from "@material-ui/core/Tooltip";
import GroupIcon from "@material-ui/icons/Group";

import dayjs from "dayjs";

import { ra_to_hours, dec_to_dms } from "../units";
import * as SourcesAction from "../ducks/sources";
import * as GroupAction from "../ducks/group";
import styles from "./CommentList.css";
import ThumbnailList from "./ThumbnailList";
import UserAvatar from "./UserAvatar";
import ShowClassification from "./ShowClassification";

const VegaPlot = React.lazy(() => import("./VegaPlot"));

const useStyles = makeStyles((theme) => ({
  chip: {
    margin: theme.spacing(0.5),
  },
  source: {},
  commentListContainer: {
    height: "15rem",
    overflowY: "scroll",
    padding: "0.5rem 0",
  },
  tableGrid: {
    width: "100%",
  },
}));

const GroupSources = ({ route }) => {
  const dispatch = useDispatch();
  const groups = useSelector((state) => state.groups.userAccessible);
  const sources = useSelector((state) => state.sources.groupSources);
  const { taxonomyList } = useSelector((state) => state.taxonomies);
  const classes = useStyles();

  // Color styling
  const userColorTheme = useSelector(
    (state) => state.profile.preferences.theme
  );

  const commentStyle =
    userColorTheme === "dark" ? styles.commentDark : styles.comment;

  // Load the group sources
  useEffect(() => {
    dispatch(GroupAction.fetchGroup(route.id));
    dispatch(SourcesAction.fetchGroupSources({ group_ids: [route.id] }));
  }, [route.id, dispatch]);

  if (!sources) {
    return (
      <div>
        <CircularProgress color="secondary" />
      </div>
    );
  }

  const group_id = parseInt(route.id, 10);

  const groupName = groups.filter((g) => g.id === group_id)[0]?.name || "";

  if (sources.length === 0) {
    return (
      <Grid item>
        <div>
          <Typography
            variant="h4"
            gutterBottom
            color="textSecondary"
            align="center"
          >
            <b>No sources have been saved to {groupName}</b>
          </Typography>
        </div>
      </Grid>
    );
  }

  // This is just passed to MUI datatables options -- not meant to be instantiated directly.
  const renderPullOutRow = (rowData, rowMeta) => {
    const colSpan = rowData.length + 1;
    const source = sources[rowMeta.dataIndex];

    const comments = source.comments || [];

    return (
      <TableRow>
        <TableCell
          style={{ paddingBottom: 0, paddingTop: 0 }}
          colSpan={colSpan}
        >
          <Grid
            container
            direction="row"
            spacing={3}
            justify="center"
            alignItems="center"
          >
            <ThumbnailList
              thumbnails={source.thumbnails}
              ra={source.ra}
              dec={source.dec}
              useGrid={false}
            />
            <Grid item>
              <Suspense fallback={<div>Loading plot...</div>}>
                <VegaPlot dataUrl={`/api/sources/${source.id}/photometry`} />
              </Suspense>
            </Grid>
            <Grid item>
              <div className={classes.commentListContainer}>
                {comments.map(
                  ({
                    id,
                    author,
                    author_info,
                    created_at,
                    text,
                    attachment_name,
                    groups: comment_groups,
                  }) => (
                    <span key={id} className={commentStyle}>
                      <div className={styles.commentUserAvatar}>
                        <UserAvatar
                          size={24}
                          firstName={author_info.first_name}
                          lastName={author_info.last_name}
                          username={author_info.username}
                          gravatarUrl={author_info.gravatar_url}
                        />
                      </div>
                      <div className={styles.commentContent}>
                        <div className={styles.commentHeader}>
                          <span className={styles.commentUser}>
                            <span className={styles.commentUserName}>
                              {author.username}
                            </span>
                          </span>
                          <span className={styles.commentTime}>
                            {dayjs().to(dayjs.utc(`${created_at}Z`))}
                          </span>
                          <div className={styles.commentUserGroup}>
                            <Tooltip
                              title={comment_groups
                                .map((group) => group.name)
                                .join(", ")}
                            >
                              <GroupIcon
                                fontSize="small"
                                viewBox="0 -2 24 24"
                              />
                            </Tooltip>
                          </div>
                        </div>
                        <div className={styles.wrap} name={`commentDiv${id}`}>
                          <div className={styles.commentMessage}>{text}</div>
                        </div>
                        <span>
                          {attachment_name && (
                            <div>
                              Attachment:&nbsp;
                              <a href={`/api/comment/${id}/attachment`}>
                                {attachment_name}
                              </a>
                            </div>
                          )}
                        </span>
                      </div>
                    </span>
                  )
                )}
              </div>
            </Grid>
          </Grid>
        </TableCell>
      </TableRow>
    );
  };

  // This is just passed to MUI datatables options -- not meant to be instantiated directly.
  const renderObjId = (dataIndex) => {
    const objid = sources[dataIndex].id;
    return (
      <a href={`/source/${objid}`} key={`${objid}_objid`}>
        {objid}
      </a>
    );
  };

  const renderAlias = (dataIndex) => {
    const { id: objid, alias } = sources[dataIndex];

    return (
      <a href={`/source/${objid}`} key={`${objid}_alias`}>
        {alias}
      </a>
    );
  };

  // This is just passed to MUI datatables options -- not meant to be instantiated directly.

  const renderRA = (dataIndex) => {
    const source = sources[dataIndex];
    return <div key={`${source.id}_ra`}>{source.ra.toFixed(6)}</div>;
  };

  const renderRASex = (dataIndex) => {
    const source = sources[dataIndex];
    return <div key={`${source.id}_ra_sex`}>{ra_to_hours(source.ra)}</div>;
  };

  // This is just passed to MUI datatables options -- not meant to be instantiated directly.
  const renderDec = (dataIndex) => {
    const source = sources[dataIndex];
    return <div key={`${source.id}_dec`}>{source.dec.toFixed(6)}</div>;
  };

  const renderDecSex = (dataIndex) => {
    const source = sources[dataIndex];
    return <div key={`${source.id}_dec_sex`}>{dec_to_dms(source.dec)}</div>;
  };

  const renderRedshift = (dataIndex) => {
    const source = sources[dataIndex];
    return <div key={`${source.id}_redshift`}>{source.redshift}</div>;
  };

  const renderClassification = (dataIndex) => {
    const source = sources[dataIndex];
    return (
      <Suspense fallback={<div>Loading classifications</div>}>
        <ShowClassification
          classifications={source.classifications.filter((cls) => {
            return cls.groups.find((g) => {
              return g.id === group_id;
            });
          })}
          taxonomyList={taxonomyList}
          shortened
        />
      </Suspense>
    );
  };

  // This is just passed to MUI datatables options -- not meant to be instantiated directly.
  const renderGroups = (dataIndex) => {
    const source = sources[dataIndex];
    return (
      <div key={`${source.id}_groups`}>
        {source.groups.map((group) => (
          <div key={group.name}>
            <Chip
              label={group.name.substring(0, 15)}
              key={group.id}
              size="small"
              className={classes.chip}
            />
            <br />
          </div>
        ))}
      </div>
    );
  };

  const renderDateSaved = (dataIndex) => {
    const source = sources[dataIndex];

    const group = source.groups.find((g) => {
      return g.id === group_id;
    });
    return (
      <div key={`${source.id}_date_saved`}>
        {group.saved_at.substring(0, 19)}
      </div>
    );
  };

  // This is just passed to MUI datatables options -- not meant to be instantiated directly.
  const renderFinderButton = (dataIndex) => {
    const source = sources[dataIndex];
    return (
      <IconButton size="small" key={`${source.id}_actions`}>
        <Link href={`/api/sources/${source.id}/finder`}>
          <PictureAsPdfIcon />
        </Link>
      </IconButton>
    );
  };

  const columns = [
    {
      name: "Source ID",
      options: {
        filter: true,
        customBodyRenderLite: renderObjId,
      },
    },
    {
      name: "Alias",
      options: {
        filter: true,
        display: false,
        customBodyRenderLite: renderAlias,
      },
    },
    {
      name: "RA (deg)",
      options: {
        filter: false,
        customBodyRenderLite: renderRA,
      },
    },
    {
      name: "Dec (deg)",
      options: {
        filter: false,
        customBodyRenderLite: renderDec,
      },
    },
    {
      name: "RA (hh:mm:ss)",
      options: {
        filter: false,
        display: false,
        customBodyRenderLite: renderRASex,
      },
    },
    {
      name: "Dec (dd:mm:ss)",
      options: {
        filter: false,
        display: false,
        customBodyRenderLite: renderDecSex,
      },
    },
    {
      name: "Redshift",
      options: {
        filter: false,
        customBodyRenderLite: renderRedshift,
      },
    },
    {
      name: "Classification",
      options: {
        filter: true,
        customBodyRenderLite: renderClassification,
      },
    },
    {
      name: "Groups",
      options: {
        filter: false,
        customBodyRenderLite: renderGroups,
      },
    },
    {
      name: "Date Saved",
      options: {
        filter: false,
        customBodyRenderLite: renderDateSaved,
      },
    },
    {
      name: "Finder",
      options: {
        filter: false,
        customBodyRenderLite: renderFinderButton,
      },
    },
  ];

  const options = {
    draggableColumns: { enabled: true },
    expandableRows: true,
    renderExpandableRow: renderPullOutRow,
    selectableRows: "none",
  };

  const data = sources.map((source) => [
    source.id,
    source.alias,
    source.ra,
    source.dec,
    ra_to_hours(source.ra),
    dec_to_dms(source.dec),
    source.redshift,
    source.latest_class,
    source.groups.map((group) => {
      return group.name;
    }),
    source.saved_at,
    "", // this last one is for the finder chart
    // (must have the same number of data points as columns)
  ]);

  return (
    <div className={classes.source}>
      <div className={classes.flexTable}>
        <Grid
          container
          direction="column"
          alignItems="center"
          justify="flex-start"
          spacing={3}
        >
          <Grid item>
            <div>
              <Typography
                variant="h4"
                gutterBottom
                color="textSecondary"
                align="center"
              >
                <b>Sources saved to {groupName}</b>
              </Typography>
            </div>
          </Grid>
          <Grid item className={classes.tableGrid}>
            <MUIDataTable
              title="Sources"
              columns={columns}
              data={data}
              options={options}
            />
          </Grid>
          <Grid item>
            <div>
              <Typography
                variant="h4"
                gutterBottom
                color="textSecondary"
                align="center"
              >
                (Refresh page to see updates)
              </Typography>
            </div>
          </Grid>
        </Grid>
      </div>
    </div>
  );
};

GroupSources.propTypes = {
  route: PropTypes.shape({
    id: PropTypes.string,
  }).isRequired,
};

export default GroupSources;
