import * as actionTypes from "./actionTypes";
import axios from "../../axios-backend";

export const fetchSchemaBoxSuccess = (boxplotData) => {
  return {
    type: actionTypes.FETCH_SCHEMA_BOX_SUCCESS,
    boxplotData: boxplotData,
  };
};

export const fetchSchemaBoxFail = (error) => {
  return {
    type: actionTypes.FETCH_SCHEMA_BOX_FAIL,
    error: error,
  };
};

export const fetchSchemaBoxStart = () => {
  return {
    type: actionTypes.FETCH_SCHEMA_BOX_START,
  };
};

export const fetchSchemaBox = (species_id, schema_id) => {
  return (dispatch) => {
    dispatch(fetchSchemaBoxStart());
    axios
      .get(
        "stats/species/" + species_id + "/schema/" + schema_id + "/lengthStats"
      )
      .then((res) => {
        console.log(res.data);
        let serverData = res.data;
        let boxplotData = [];

        boxplotData.push({
          type: "box",
          name: "Locus Size Variation",
          x: serverData.loci,
          q1: serverData.q1,
          median: serverData.median,
          q3: serverData.q3,
          lowerfence: serverData.min,
          upperfence: serverData.max,
          showlegend: false,
        });

        dispatch(fetchSchemaBoxSuccess(boxplotData));
      })
      .catch((boxErr) => {
        dispatch(fetchSchemaBoxFail(boxErr));
      });
  };
};
