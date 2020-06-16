import * as actionTypes from "./actionTypes";
import axios from "../../axios-backend";

export const fetchSchemaAlleleModeSuccess = (mode_data, total_allele_data, scatter_data, mode_data2) => {
  return {
    type: actionTypes.FETCH_SCHEMA_ALLELE_MODE_SUCCESS,
    mode_data: mode_data,
    total_allele_data: total_allele_data,
    scatter_data: scatter_data,
    mode_data2: mode_data2
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
      .get("stats/species/" + species_id + "/schema/" + schema_id + "/modes")
      .then(res => {
        console.log(res.data);
        let query = "stats/species/" + species_id + "/schema/" + schema_id + "/modes";
        let allele_mode = [];
        let locus_name = [];
        let mode_data = [];
        let mode_data2 = [];
        for (let key in res.data.mode) {
          allele_mode.push(res.data.mode[key].alleles_mode);
          locus_name.push(res.data.mode[key].locus_name);

          mode_data2.push({
            locus_name: res.data.mode[key].locus_name,
            mode: res.data.mode[key].alleles_mode
          })
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
        
        let locus_id = [];
        let nr_alleles_scatter = [];
        let scatter_data = [];
        let scatter_data_mean = [];
        let scatter_data_median = [];
        let scatter_data_mode = [];
        for (let key in res.data.scatter_data) {
          locus_id.push(parseInt(res.data.scatter_data[key].locus_id))
          nr_alleles_scatter.push(res.data.scatter_data[key].nr_alleles);
          scatter_data_mean.push(res.data.scatter_data[key].alleles_mean);
          scatter_data_median.push(res.data.scatter_data[key].alleles_median);
          scatter_data_mode.push(res.data.scatter_data[key].alleles_mode);
        }
        scatter_data.push({
          x: scatter_data_mode,
          y: nr_alleles_scatter,
          type: "scatter",
          name: "Mode",
          mode: "markers",
          marker: {
            opacity: 0.7,
            size: 4
          },
          hovertemplate: '<b>ID</b>: %{text}',
          text: locus_id
        },
        {
          x: scatter_data_mean,
          y: nr_alleles_scatter,
          type: "scatter",
          name: "Mean",
          mode: "markers",
          marker: {
            opacity: 0.7,
            size: 4
          },
          hovertemplate: '<b>ID</b>: %{text}',
          text: locus_id
        },
        {
          x: scatter_data_median,
          y: nr_alleles_scatter,
          type: "scatter",
          name: "Median",
          mode: "markers",
          marker: {
            opacity: 0.7,
            size: 4
          },
          hovertemplate: '<b>ID</b>: %{text}',
          text: locus_id
        })
        // console.log(plot_data)
        // let chewie = [];
        // chewie.push(mode_data, total_al_data, scatter_data, mode_data2)
        // localStorage.setItem(query, JSON.stringify(chewie));
        dispatch(fetchSchemaAlleleModeSuccess(mode_data, total_al_data, scatter_data, mode_data2));
      })
      .catch(modeErr => {
        dispatch(fetchSchemaAlleleModeFail(modeErr));
      });
  };
};
