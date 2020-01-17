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
        const collator = new Intl.Collator(undefined, {numeric: true, sensitivity: 'base'}); // natural sort
        const fetchedSpeciesAnnot2 = [];
        let x_val = 0;
        let y_val = 0;
        let locus_id = 0;
        let ola2 = {};
        let olaLocus = {};
        let curSchemaId = 0;
        for (let key in res.data.message) {

          curSchemaId = res.data.message[key].schema.value.substring(
            res.data.message[key].schema.value.lastIndexOf("/") + 1
          );

          locus_id = res.data.message[key].locus.value.substring(
            res.data.message[key].locus.value.lastIndexOf("/") + 1
          );

          x_val += 1;

          y_val = res.data.message[key].nr_allele.value;

          if (curSchemaId in ola2) {
            ola2[curSchemaId][[x_val]] = y_val
            olaLocus[curSchemaId][[x_val]] = locus_id
  
          } else if (!(curSchemaId in ola2)) {
            // console.log("works2")
            // console.log(curSchemaId)
            ola2[curSchemaId] = {
              [x_val]: y_val,
            }
            olaLocus[curSchemaId] = {
              [x_val]: locus_id
            }
            x_val = 0
            locus_id = 0
          }
          }
        // console.log("[OLA2]")
        // console.log(ola2)
        
        for (let idx in ola2) {
          fetchedSpeciesAnnot2.push({
            x: Object.keys(ola2[idx]),
            y: Object.values(ola2[idx]).sort(collator.compare).reverse(collator.compare),
            type: "bar",
            name: "Schema " + idx,
            // hovertext: Object.values(olaLocus[idx])
            // line: {
            //   width: 1
            // }
          });
        }
        dispatch(fetchSpeciesAnnotSuccess(fetchedSpeciesAnnot2));
      })
      .catch(err => {
        dispatch(fetchSpeciesAnnotFail(err));
      });
  };
};
