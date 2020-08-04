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
            dateEntered:
              new Date(
                dateEnteredFormatted.getTime() -
                  dateEnteredFormatted.getTimezoneOffset() * 6000
              )
                .toISOString()
                .split("T")[0] +
              " " +
              new Date(
                dateEnteredFormatted.getTime() -
                  dateEnteredFormatted.getTimezoneOffset() * 6000
              ).toLocaleTimeString([], { hour12: false }),
            lastModified:
              new Date(
                lastModifiedDateFormatted.getTime() -
                  lastModifiedDateFormatted.getTimezoneOffset() * 6000
              )
                .toISOString()
                .split("T")[0] +
              " " +
              new Date(
                lastModifiedDateFormatted.getTime() -
                  lastModifiedDateFormatted.getTimezoneOffset() * 6000
              ).toLocaleTimeString([], { hour12: false }),
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
        // reference: https://www.sitepoint.com/sort-an-array-of-objects-in-javascript/
        function compareValues(key, order = "asc") {
          return function innerSort(a, b) {
            if (!a.hasOwnProperty(key) || !b.hasOwnProperty(key)) {
              // property doesn't exist on either object
              return 0;
            }

            const varA =
              typeof a[key] === "string" ? a[key].toUpperCase() : a[key];
            const varB =
              typeof b[key] === "string" ? b[key].toUpperCase() : b[key];

            let comparison = 0;
            if (varA > varB) {
              comparison = 1;
            } else if (varA < varB) {
              comparison = -1;
            }
            return order === "desc" ? comparison * -1 : comparison;
          };
        }

        const fetchedSpeciesAnnot2 = [];

        let schema_ids = [...Array(res.data.message.length).keys()];

        for (let id in schema_ids) {
          let curSchemaId = parseInt(id) + 1;

          let x_val = [];
          let y_val = [];
          let locus_id = [];

          for (let key in res.data.message[id].loci.sort(
            compareValues("nr_alleles", "desc")
          )) {
            locus_id.push(
              res.data.message[id].loci[key].locus.substring(
                res.data.message[id].loci[key].locus.lastIndexOf("/") + 1
              )
            );
            x_val.push(parseInt(key) + 1);
            y_val.push(res.data.message[id].loci[key].nr_alleles);
          }

          fetchedSpeciesAnnot2.push({
            x: x_val,
            y: y_val,
            type: "bar",
            name: "Schema " + curSchemaId,
            hovertemplate:
              "<b>Number of Alleles</b>: %{y}" +
              "<br><b>Locus_ID</b>: %{text}</br>",
            text: locus_id,
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
