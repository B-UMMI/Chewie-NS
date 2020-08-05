import * as actionTypes from "./actionTypes";
import axios from "../../axios-backend";

export const fetchAnnotationsSuccess = (annotations) => {
  return {
    type: actionTypes.FECTH_ANNOTATIONS_SUCCESS,
    annotations: annotations,
  };
};

export const fetchAnnotationsFail = (error) => {
  return {
    type: actionTypes.FECTH_ANNOTATIONS_FAIL,
    error: error,
  };
};

export const fetchAnnotationsStart = () => {
  return {
    type: actionTypes.FECTH_ANNOTATIONS_START,
  };
};

export const fetchAnnotations = (species_id, schema_id) => {
  return (dispatch) => {
    dispatch(fetchAnnotationsStart());
    axios
      .get(
        "/stats/species/" + species_id + "/schema/" + schema_id + "/annotations"
      )
      .then((res) => {
        // console.log(res);
        let annotTableData = [];
        for (let key in res.data.message) {
          annotTableData.push({
            uniprot_label: res.data.message[key].UniprotName,
            uniprot_uri: res.data.message[key].UniprotURI,
            user_annotation: res.data.message[key].UserAnnotation,
            custom_annotation: res.data.message[key].CustomAnnotation,
            locus: parseInt(
              res.data.message[key].locus.substring(
                res.data.message[key].locus.lastIndexOf("/") + 1
              )
            ),
            locus_name: res.data.message[key].name,
            alleles_mode: parseInt(res.data.message[key].mode),
            nr_alleles: parseInt(res.data.message[key].nr_alleles),
            min: parseInt(res.data.message[key].min),
            max: parseInt(res.data.message[key].max),
            size_range:
              res.data.message[key].min.toString() +
              "-" +
              res.data.message[key].max.toString(),
          });
        }
        // console.log(annotTableData)
        const annotTableDataSorted = annotTableData.sort((a, b) => {
          return a.locus - b.locus;
        });
        dispatch(fetchAnnotationsSuccess(annotTableDataSorted));
      })
      .catch((annotErr) => {
        dispatch(fetchAnnotationsFail(annotErr));
      });
  };
};
