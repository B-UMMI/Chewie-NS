import * as actionTypes from "./actionTypes";
import axios from "../../axios-backend";

export const fetchDescriptionsSuccess = (descriptions) => {
  return {
    type: actionTypes.FECTH_DESCRIPTIONS_SUCCESS,
    descriptions: descriptions,
  };
};

export const fetchDescriptionsFail = (error) => {
  return {
    type: actionTypes.FECTH_DESCRIPTIONS_FAIL,
    error: error,
  };
};

export const fetchDescriptionsStart = () => {
  return {
    type: actionTypes.FECTH_DESCRIPTIONS_START,
  };
};

export const fetchDescriptions = (species_id, schema_id) => {
  return (dispatch) => {
    dispatch(fetchDescriptionsStart());
    axios
      .get(
        "/species/" +
          species_id +
          "/schemas/" +
          schema_id +
          "/description?request_type=check"
      )
      .then((res) => {
        let desc = res.data.description;
        dispatch(fetchDescriptionsSuccess(desc));
      })
      .catch((err) => {
        console.log(err)
        dispatch(fetchDescriptionsFail(err));
      });
  };
};
