import * as actionTypes from "./actionTypes";
import axios from "../../axios-backend";
import _ from "lodash";

export const fetchSpeciesSuccess = (species) => {
  return {
    type: actionTypes.FECTH_SPECIES_SUCCESS,
    species: species,
  };
};

export const fetchSpeciesFail = (error) => {
  return {
    type: actionTypes.FECTH_SPECIES_FAIL,
    error: error,
  };
};

export const fetchSpeciesStart = () => {
  return {
    type: actionTypes.FECTH_SPECIES_START,
  };
};

export const fetchSpecies = (spec_id) => {
  return (dispatch) => {
    dispatch(fetchSpeciesStart());
    axios
      .get("stats/species/" + spec_id + "/totals")
      .then((res) => {
        // console.log("[SUCESS]")
        // console.log(res.data.message)
        const fetchedSpecies = [];
        for (let key in res.data.message) {
          let dateEnteredFormatted = new Date(
            res.data.message[key].dateEntered
          );
          let lastModifiedDateFormatted = new Date(
            res.data.message[key].last_modified
          );
          fetchedSpecies.push({
            schema_id:
              res.data.message[key].uri[res.data.message[key].uri.length - 1],
            schema_name: res.data.message[key].name,
            user: res.data.message[key].user,
            chewie: res.data.message[key].chewBBACA_version,
            dateEntered: new Date(
              dateEnteredFormatted.getTime() -
                dateEnteredFormatted.getTimezoneOffset() * 6000
            )
              .toISOString()
              .split("T")[0],
            lastModified: new Date(
              lastModifiedDateFormatted.getTime() -
                lastModifiedDateFormatted.getTimezoneOffset() * 6000
            )
              .toISOString()
              .split("T")[0],
            lastModifiedISO: res.data.message[key].last_modified,
            bsr: res.data.message[key].bsr,
            ptf: res.data.message[key].prodigal_training_file,
            tl_table: res.data.message[key].translation_table,
            minLen: res.data.message[key].minimum_locus_length,
            sizeThresh: res.data.message[key].size_threshold,
            nr_loci: res.data.message[key].nr_loci,
            nr_allele: res.data.message[key].nr_alleles,
            id: key,
          });
        }
        // console.log(fetchedSpecies)
        dispatch(fetchSpeciesSuccess(fetchedSpecies));
      })
      .catch((err) => {
        dispatch(fetchSpeciesFail(err));
      });
  };
};

export const fetchSpeciesAnnotSuccess = (species_annot) => {
  return {
    type: actionTypes.FECTH_SPECIES_ANNOT_SUCCESS,
    species_annot: species_annot,
  };
};

export const fetchSpeciesAnnotFail = (error) => {
  return {
    type: actionTypes.FECTH_SPECIES_ANNOT_FAIL,
    error: error,
  };
};

export const fetchSpeciesAnnotStart = () => {
  return {
    type: actionTypes.FECTH_SPECIES_ANNOT_START,
  };
};

export const fetchSpeciesAnnot = (spec_id) => {
  return (dispatch) => {
    dispatch(fetchSpeciesAnnotStart());
    axios
      .get("stats/species/" + spec_id + "/schema/loci/nr_alleles")
      .then((res) => {
        console.log(res);
        const fetchedSpeciesAnnot2 = [];
        let x_val = 0;
        let y_val = 0;
        let locus_id = 0;
        let ola2 = {};
        let ola3 = {};
        let ola4 = {};
        let ola22 = [];
        let olaLocus = {};

        // let curSchemaId = res.data.message[0].schema.substring(
        //   res.data.message[0].schema.lastIndexOf("/") + 1
        // );

        let schema_ids = [...Array(res.data.message.length).keys()];

        for (let id in schema_ids) {
          let curSchemaId = parseInt(id) + 1;

          for (let key in res.data.message[id].loci) {
            locus_id = res.data.message[id].loci[key].locus.substring(
              res.data.message[id].loci[key].locus.lastIndexOf("/") + 1
            );

            x_val += 1;

            y_val = res.data.message[id].loci[key].nr_alleles;

            if (curSchemaId in ola2) {
              ola2[curSchemaId][[x_val]] = y_val;
              olaLocus[curSchemaId][[x_val]] = locus_id;
              ola3[curSchemaId].push(y_val);
              ola4[curSchemaId][[locus_id]] = y_val;
            } else if (!(curSchemaId in ola2)) {
              // console.log("works2")
              // console.log(curSchemaId)
              ola2[curSchemaId] = {
                [x_val]: y_val,
              };

              ola22.push(y_val);

              ola3[curSchemaId] = ola22;

              ola4[curSchemaId] = {
                [locus_id]: y_val,
              };

              // ola22.push(
              //   {[x_val]: y_val}
              // )
              olaLocus[curSchemaId] = {
                [x_val]: locus_id,
                // [locus_id]: y_val
              };
              x_val = 0;
              locus_id = 0;
              ola22 = [];
            }
          }
        }
        console.log("[OLA4]");
        console.log(ola4);

        for (let idx in ola4) {
          // console.log(ola4[idx])

          let sorted = _(ola4[idx])
            .toPairs()
            .value()
            .sort((a, b) => b[1] - a[1]);

          let s_loci_id = sorted.map((arr2) => arr2[0]);

          let s_nr_alleles = sorted.map((arr2) => arr2[1]);

          // console.log(s_loci_id)
          // console.log(s_nr_alleles)

          fetchedSpeciesAnnot2.push({
            x: Object.keys(ola2[idx]),
            y: s_nr_alleles,
            type: "bar",
            name: "Schema " + idx,
            hovertemplate:
              "<b>Number of Alleles</b>: %{y}" +
              "<br><b>Locus_ID</b>: %{text}</br>",
            text: s_loci_id,
            //hoverinfo: "y+text"
            // line: {
            //   width: 1
            // }
          });
        }
        dispatch(fetchSpeciesAnnotSuccess(fetchedSpeciesAnnot2));
      })
      .catch((err) => {
        console.log(err);
        dispatch(fetchSpeciesAnnotFail(err));
      });
  };
};
