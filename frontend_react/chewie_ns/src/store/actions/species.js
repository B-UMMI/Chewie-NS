import * as actionTypes from "./actionTypes";
import axios from "../../axios-backend";

export const fetchSpeciesSuccess = species => {
  return {
    type: actionTypes.FECTH_SPECIES_SUCCESS,
    species: species
  };
};

export const fetchSpeciesFail = error => {
  return {
    type: actionTypes.FECTH_SPECIES_FAIL,
    error: error
  };
};

export const fetchSpeciesStart = () => {
  return {
    type: actionTypes.FECTH_SPECIES_START
  };
};

export const fetchSpecies = token => {
  return dispatch => {
    dispatch(fetchSpeciesStart());
    axios
      .get("/species/list", {
        headers: {
          Authorization: token
        }
      })
      .then(res => {
        // console.log("[SUCESS]")
        // console.log(res.data)
        const fetchedSpecies = [];
        for (let key in res.data) {
            // console.log(key)
            fetchedSpecies.push({
                species_id: res.data[key].species.value,
                species_name: res.data[key].name.value,
                id: key
            });
        }
        dispatch(fetchSpeciesSuccess(fetchedSpecies));
      })
      .catch(err => {
        dispatch(fetchSpeciesFail(err));
      });
  };
};
