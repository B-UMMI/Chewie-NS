import * as actionTypes from "./actionTypes";
import axios from "../../axios-backend";

export const fetchStatsSuccess = stats => {
  return {
    type: actionTypes.FECTH_STATS_SUCCESS,
    stats: stats
  };
};

export const fetchStatsFail = error => {
  return {
    type: actionTypes.FECTH_STATS_FAIL,
    error: error
  };
};

export const fetchStatsStart = () => {
  return {
    type: actionTypes.FECTH_STATS_START
  };
};

export const fetchStats = () => {
  return dispatch => {
    dispatch(fetchStatsStart());
    axios
      .get("/stats/species")
      .then(res => {
        console.log("[action]");
        const fetchedStats = [];
        for (let key in res.data.message[0]) {
          fetchedStats.push({
            data: key + ": " + res.data.message[0][key].value,
            id: key
          });
        }
        dispatch(fetchStatsSuccess(fetchedStats));
      })
      .catch(err => {
        dispatch(fetchStatsFail(err));
      });
  };
};

export const fetchStatsSpeciesSuccess = (stats) => {
  return {
    type: actionTypes.FECTH_STATS_SPECIES_SUCCESS,
    stats: stats
  };
};

export const fetchStatsSpeciesFail = error => {
  return {
    type: actionTypes.FECTH_STATS_SPECIES_FAIL,
    error: error
  };
};

export const fetchStatsSpeciesStart = () => {
  return {
    type: actionTypes.FECTH_STATS_SPECIES_START
  };
};

export const fetchStatsSpecies = () => {
  return dispatch => {
    dispatch(fetchStatsSpeciesStart());
    axios
      .get("/stats/species")
      .then(res => {
        const fetchedSpeciesStats = [];
        const speciesDict = {};
        for (let key in res.data.message) {
          fetchedSpeciesStats.push({
            species_id:
              res.data.message[key].species.value[
                res.data.message[key].species.value.length - 1
              ],
            species_name: res.data.message[key].name.value,
            nr_schemas: res.data.message[key].schemas.value,
            ptf: res.data.message[key].ptf.value,
            id: key
          });

          let speciesId =
            res.data.message[key].species.value[
              res.data.message[key].species.value.length - 1
            ];
          let speciesName = res.data.message[key].name.value;

          speciesDict[speciesId] = speciesName;

        }
        localStorage.setItem('speciesD', JSON.stringify(speciesDict));
        console.log(fetchedSpeciesStats);
        dispatch(fetchStatsSpeciesSuccess(fetchedSpeciesStats));
      })
      .catch(err => {
        dispatch(fetchStatsSpeciesFail(err));
      });
  };
};
