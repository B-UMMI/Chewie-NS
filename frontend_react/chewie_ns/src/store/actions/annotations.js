import * as actionTypes from "./actionTypes";
import axios from "../../axios-backend";

export const fetchAnnotationsSuccess = annotations => {
  return {
    type: actionTypes.FECTH_ANNOTATIONS_SUCCESS,
    annotations: annotations
  };
};

export const fetchAnnotationsFail = error => {
  return {
    type: actionTypes.FECTH_ANNOTATIONS_FAIL,
    error: error
  };
};

export const fetchAnnotationsStart = () => {
  return {
    type: actionTypes.FECTH_ANNOTATIONS_START
  };
};

export const fetchAnnotations = (species_id, schema_id) => {
  return dispatch => {
    dispatch(fetchAnnotationsStart());
    axios
      .get("/stats/species/" + species_id + "/schema/" + schema_id + "/annotations")
      .then(res => {
        // console.log(res);
        let annotTableData = [];
        // let annotTableData2 = [];
        // let curLabel = "";
        // let schemaIds = [];
        // let locusIds = [];
        // let speciesNames = [];
        for (let key in res.data.message) {
          annotTableData.push({
            uniprot_label: res.data.message[key].UniprotLabel.value,
            uniprot_uri: res.data.message[key].UniprotURI.value,
            //species: res.data.message[key].species.value,
            // schema: res.data.message[key].schema.value.substring(
            //   res.data.message[key].schema.value.lastIndexOf("/") + 1
            // ),
            locus: res.data.message[key].locus.value.substring(
              res.data.message[key].locus.value.lastIndexOf("/") + 1
            ),
            locus_name: res.data.message[key].name.value,
            alleles_mode: parseInt(res.data.message[key].mode)
          });
        }
        // console.log(annotTableData2)
        dispatch(fetchAnnotationsSuccess(annotTableData));
      })
      .catch(annotErr => {
        dispatch(fetchAnnotationsFail(annotErr));
      });
  };
};
