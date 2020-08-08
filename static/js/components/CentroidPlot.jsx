import React, { useEffect, Suspense } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import * as photometryActions from '../ducks/photometry';
import { Vega, VegaLite, createClassFromSpec } from 'react-vega';
import embed from 'vega-embed';
import * as d3 from 'd3';

// Helper functions for computing plot points (taken from GROWTH marshall)
const gcirc = (ra1, dec1, ra2, dec2) => {
  // input deg, haversine formula, return deg
  ra1 = (ra1 / 180) * Math.PI;
  dec1 = (dec1 / 180) * Math.PI;
  ra2 = (ra2 / 180) * Math.PI;
  dec2 = (dec2 / 180) * Math.PI;
  const delDec2 = (dec2 - dec1) * 0.5;
  const delRA2 = (ra2 - ra1) * 0.5;
  return (
    (360 *
      Math.asin(
        Math.sqrt(
          Math.sin(delDec2) * Math.sin(delDec2) +
            Math.cos(dec1) *
              Math.cos(dec2) *
              Math.sin(delRA2) *
              Math.sin(delRA2)
        )
      )) /
    Math.PI
  );
};

const relativeCoord = (ra, dec, refRA, refDec) => {
  const delRA = gcirc(ra, dec, refRA, dec) * 3600 * -Math.sign(ra - refRA);
  const delDec = gcirc(ra, dec, ra, refDec) * 3600 * Math.sign(dec - refDec);
  return { delRA, delDec };
};

// Temporary function for draft
const getReferencePoint = (ras, decs) => {
  const refRA = d3.median(ras);
  const refDec = d3.median(decs);

  return { refRA, refDec };
};

const getCirclePoints = (delRaGroup, delDecGroup) => {
  const thetas = d3.range(0, 2.01 * Math.PI, 0.01);
  const C = Math.max(d3.deviation(delRaGroup), d3.deviation(delDecGroup));
  const medianRA = d3.median(delRaGroup);
  const medianDec = d3.median(delDecGroup);

  const points = thetas.map((theta) => {
    const xx = medianRA + C * Math.cos(theta);
    const yy = medianDec + C * Math.sin(theta);
    return { xx: xx, yy: yy, theta: theta };
  });

  return points;
};

const getMessages = (delRaGroup, delDecGroup) => {
  //r"offset = %.2f $\pm$ %.2f''" %(((np.median(delra_group))**2 + (np.median(deldec_group)**2))**0.5, C)
  const offset = Math.sqrt(
    Math.pow(d3.median(delRaGroup), 2) + Math.pow(d3.median(delDecGroup), 2)
  );
  const C = Math.max(d3.deviation(delRaGroup), d3.deviation(delDecGroup));

  const offsetMessage = {
    x: 0.6,
    y: 0.8,
    message: `offset = ${offset.toFixed(2)} \u00B1 ${C.toFixed(2)}`,
  };

  return [offsetMessage];
};

// The Vega-Lite specifications for the centroid plot
const spec = (inputData) => {
  return {
    $schema: 'https://vega.github.io/schema/vega-lite/v4.json',
    width: 450,
    height: 450,
    background: 'transparent',
    layer: [
      // Render nuclear-to-host circle
      {
        data: {
          values: inputData['circlePoints'],
        },
        transform: [
          { calculate: '0.8 * cos(datum.theta)', as: 'x' },
          { calculate: '0.8 * sin(datum.theta)', as: 'y' },
        ],
        mark: {
          type: 'line',
        },
        encoding: {
          x: {
            field: 'x',
            type: 'quantitative',
          },
          y: {
            field: 'y',
            type: 'quantitative',
          },
          order: { field: 'theta', type: 'quantitative' },
          fill: {
            value: '#ccd2db',
          },
          fillOpacity: { value: 0.5 },
          strokeOpacity: { value: 0 },
        },
      },

      // Render 1 sigma boundary circle
      {
        data: {
          values: inputData['circlePoints'],
        },
        mark: {
          type: 'line',
          point: 'true',
        },
        encoding: {
          x: {
            field: 'xx',
            type: 'quantitative',
          },
          y: {
            field: 'yy',
            type: 'quantitative',
          },
          order: { field: 'theta', type: 'quantitative' },
          color: {
            value: 'red',
            legend: {
              values: ['\u03A3'],
              orient: 'bottom-right',
            },
          },
          strokeWidth: { value: 2 },
        },
      },

      // Render main scatter plot
      {
        data: {
          values: inputData['photometryData'],
        },
        mark: {
          type: 'point',
          filled: true,
        },
        encoding: {
          x: {
            field: 'delRA',
            type: 'quantitative',
            axis: {
              title: '\u0394RA (arcsec)',
              titleFontSize: 14,
              titlePadding: 8,
            },
          },
          y: {
            field: 'delDec',
            type: 'quantitative',
            axis: {
              title: '\u0394Dec (arcsec)',
              titleFontSize: 14,
              titlePadding: 8,
            },
          },
          tooltip: [
            { field: 'id', type: 'quantitative' },
            { field: 'delRA', type: 'quantitative' },
            { field: 'delDec', type: 'quantitative' },
            { field: 'ra', type: 'quantitative', title: 'RA' },
            { field: 'dec', type: 'quantitative', title: 'Dec' },
          ],
          color: {
            field: 'filter',
            type: 'nominal',
            scale: { range: ['#2f5492', '#ff7f0e', '#2ca02c'] },
            legend: {
              title: 'Filter',
              titleFontSize: 14,
              labelFontSize: 12,
              titleLimit: 240,
              lableLimit: 240,
              rowPadding: 4,
            },
          },
          shape: {
            field: 'filter',
            type: 'nominal',
            scale: { range: ['circle', 'square', 'triangle'] },
          },
          size: { value: 35 },
          fillOpacity: { value: 1.0 },
          strokeOpacity: { value: 0 },
        },
      },

      // Render center point (nearest object position relative to mode of the // nearest references) - currently just the one reference
      {
        data: {
          values: inputData['centerPoint'],
        },
        mark: {
          type: 'point',
          shape: 'cross',
          size: '100',
        },
        encoding: {
          x: {
            field: 'x',
            type: 'quantitative',
          },
          y: {
            field: 'y',
            type: 'quantitative',
          },
          fill: { value: 'black' },
        },
      },

      // Render text messages
      {
        data: {
          values: inputData['messages'],
        },
        mark: {
          type: 'text',
          fontSize: 14,
          fontWeight: 500,
        },
        encoding: {
          text: { field: 'message', type: 'nominal' },
          x: {
            field: 'x',
            type: 'quantitative',
          },
          y: {
            field: 'y',
            type: 'quantitative',
          },
        },
      },
    ],
  };
};

const processData = (photometry) => {
  let ras = Object.values(photometry).map((point) => {
    return point.ra;
  });
  let decs = Object.values(photometry).map((point) => {
    return point.dec;
  });

  // For now, set single reference nearest object to median values for the RA // and Dec in the photometry
  const { refRA, refDec } = getReferencePoint(ras, decs);

  var delRaGroup = [];
  var delDecGroup = [];
  const photometryAsArray = Object.values(photometry).map((point) => {
    const { delRA, delDec } = relativeCoord(point.ra, point.dec, refRA, refDec);
    delRaGroup.push(delRA);
    delDecGroup.push(delDec);
    return {
      ...point,
      delRA: delRA,
      delDec: delDec,
    };
  });

  // Sigma circle
  const circlePoints = getCirclePoints(delRaGroup, delDecGroup);

  // Text notifications
  const messages = getMessages(delRaGroup, delDecGroup);

  return {
    photometryData: photometryAsArray,
    circlePoints: circlePoints,
    centerPoint: [{ x: 0.0, y: 0.0 }],
    messages: messages,
  };
};

const CentroidPlot = (props) => {
  const { sourceId, className } = props;
  const dispatch = useDispatch();
  const photometry = useSelector((state) => state.photometry[sourceId]);

  useEffect(() => {
    if (!photometry) {
      dispatch(photometryActions.fetchSourcePhotometry(sourceId));
    }
  }, [photometry, dispatch]);

  const plotData = photometry ? processData(photometry) : {};
  console.log(plotData);
  return (
    <div
      ref={(node) => {
        embed(node, spec(plotData), {
          actions: false,
        });
      }}
    />
  );
};

export default CentroidPlot;
