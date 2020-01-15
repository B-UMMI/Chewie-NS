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

export const fetchSpecies = spec_id => {
  return dispatch => {
    dispatch(fetchSpeciesStart());
    axios
      .get("stats/species/" + spec_id)
      .then(res => {
        // console.log("[SUCESS]")
        // console.log(res.data.message)
        const fetchedSpecies = [];
        for (let key in res.data.message) {
          // console.log("[KEY]")
          // console.log(key)
          fetchedSpecies.push({
            schema_id:
              res.data.message[key].schema.value[
                res.data.message[key].schema.value.length - 1
              ],
            schema_name: res.data.message[key].name.value,
            user:
              "User: " +
              res.data.message[key].user.value[
                res.data.message[key].user.value.length - 1
              ],
            chewie: res.data.message[key].chewie.value,
            bsr: res.data.message[key].bsr.value,
            ptf: res.data.message[key].ptf.value,
            tl_table: res.data.message[key].tl_table.value,
            minLen: res.data.message[key].minLen.value,
            nr_loci: res.data.message[key].nr_loci.value,
            nr_allele: res.data.message[key].nr_allele.value,
            id: key
          });
        }
        // console.log(fetchedSpecies)
        dispatch(fetchSpeciesSuccess(fetchedSpecies));
      })
      .catch(err => {
        dispatch(fetchSpeciesFail(err));
      });
  };
};

export const fetchSpeciesAnnotSuccess = species_annot => {
  return {
    type: actionTypes.FECTH_SPECIES_ANNOT_SUCCESS,
    species_annot: species_annot
  };
};

export const fetchSpeciesAnnotFail = error => {
  return {
    type: actionTypes.FECTH_SPECIES_ANNOT_FAIL,
    error: error
  };
};

export const fetchSpeciesAnnotStart = () => {
  return {
    type: actionTypes.FECTH_SPECIES_ANNOT_START
  };
};

export const fetchSpeciesAnnot = spec_id => {
  return dispatch => {
    dispatch(fetchSpeciesAnnotStart());
    axios
      .get("stats/species/" + spec_id + "/schema")
      .then(res => {
        // console.log("[SUCESS]")
        // console.log(res.data.message)
        // const collator = new Intl.Collator(undefined, {numeric: true, sensitivity: 'base'}); // natural sort
        const fetchedSpeciesAnnot = [];
        // const x = [];
        // const y = [];
        let ola = {};
        for (let key in res.data.message) {
          // console.log("[KEY]")
          // console.log(key)
          // x.push(
          //   res.data.message[key].locus.value.substring(
          //     res.data.message[key].locus.value.lastIndexOf("/") + 1
          //   )
          // );
          // y.push(res.data.message[key].nr_allele.value);
          ola[res.data.message[key].locus.value.substring(
                res.data.message[key].locus.value.lastIndexOf("/") + 1)] = res.data.message[key].nr_allele.value
        }
        // console.log(ola);
        // console.log(Object.keys(ola));
        // console.log(Object.values(ola));
        // console.log(y);
        fetchedSpeciesAnnot.push({
          x: Object.keys(ola),
          y: Object.values(ola),
          type: "scatter",
          line: {
            width: 1
          }
        });
        console.log(fetchedSpeciesAnnot)
        dispatch(fetchSpeciesAnnotSuccess(fetchedSpeciesAnnot));
      })
      .catch(err => {
        dispatch(fetchSpeciesAnnotFail(err));
      });
  };
};
