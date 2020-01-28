import * as actionTypes from "./actionTypes";
import axios from "../../axios-backend";

export const fetchSchemaAlleleModeSuccess = (mode_data, total_allele_data) => {
  return {
    type: actionTypes.FETCH_SCHEMA_ALLELE_MODE_SUCCESS,
    mode_data: mode_data,
    total_allele_data: total_allele_data
  };
};

export const fetchSchemaAlleleModeFail = error => {
  return {
    type: actionTypes.FETCH_SCHEMA_ALLELE_MODE_FAIL,
    error: error
  };
};

export const fetchSchemaAlleleModeStart = () => {
  return {
    type: actionTypes.FETCH_SCHEMA_ALLELE_MODE_START
  };
};

export const fetchSchemaAlleleMode = (species_id, schema_id) => {
  return dispatch => {
    dispatch(fetchSchemaAlleleModeStart());
    axios
      .get("stats/species/" + species_id + "/schema/" + schema_id + "/loci")
      .then(res => {
        // console.log(res.data.message);
        let allele_mode = [];
        let locus_name = [];
        let mode_data = [];
        for (let key in res.data.mode) {
          allele_mode.push(res.data.mode[key].alleles_mode);
          locus_name.push(res.data.mode[key].locus_name);
        }
        // console.log(fastaData.join("\n"));
        // console.log(allele_mode);
        // console.log(locus_name);
        mode_data.push({
          x: allele_mode,
          y: locus_name,
          type: "histogram",
          name: "Distribution of allele mode sizes per gene"
        })

        let locus_name2 = [];
        let nr_alleles = [];
        let total_al_data = [];
        for (let key in res.data.total_alleles) {
            locus_name2.push(res.data.total_alleles[key].locus_name);
            nr_alleles.push(res.data.total_alleles[key].nr_alleles);
        }
        total_al_data.push({
            x: nr_alleles,
            y: locus_name2,
            type: "histogram",
            name: "Total alleles"
        })
        // console.log(plot_data)
        dispatch(fetchSchemaAlleleModeSuccess(mode_data, total_al_data));
      })
      .catch(modeErr => {
        dispatch(fetchSchemaAlleleModeFail(modeErr));
      });
  };
};
