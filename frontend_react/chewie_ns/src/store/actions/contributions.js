import * as actionTypes from "./actionTypes";
import axios from "../../axios-backend";

export const fetchAlleleContributionSuccess = (contribData) => {
  return {
    type: actionTypes.FETCH_ALLELE_CONTRIBUTIONS_SUCCESS,
    contribData: contribData,
  };
};

export const fetchAlleleContributionFail = (error) => {
  return {
    type: actionTypes.FETCH_ALLELE_CONTRIBUTIONS_FAIL,
    error: error,
  };
};

export const fetchAlleleContributionStart = () => {
  return {
    type: actionTypes.FETCH_ALLELE_CONTRIBUTIONS_START,
  };
};

export const fetchAlleleContribution = (species_id, schema_id) => {
  return (dispatch) => {
    dispatch(fetchAlleleContributionStart());
    axios
      .get(
        "stats/species/" +
          species_id +
          "/schema/" +
          schema_id +
          "/contributions"
      )
      .then((res) => {
        console.log(res.data);
        let serverData = res.data;
        if (serverData === "undefined") {
          dispatch(fetchAlleleContributionSuccess(serverData));
        } else {
          let contribData = [];

          contribData.push({
            type: "scattergl",
            mode: "markers",
            name: "Allele Timeline Information",
            x: serverData.syncDates,
            y: serverData.newAlleles,
            showlegend: false,
          });

          dispatch(fetchAlleleContributionSuccess(contribData));
        }
      })
      .catch((contribErr) => {
        dispatch(fetchAlleleContributionFail(contribErr));
      });
  };
};
