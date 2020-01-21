import * as actionTypes from "./actionTypes";
import axios from "../../axios-backend";

export const fetchLocusFastaSuccess = locus_fasta => {
  return {
    type: actionTypes.FECTH_LOCUS_FASTA_SUCCESS,
    locus_fasta: locus_fasta
  };
};

export const fetchLocusFastaFail = error => {
  return {
    type: actionTypes.FECTH_LOCUS_FASTA_FAIL,
    error: error
  };
};

export const fetchLocusFastaStart = () => {
  return {
    type: actionTypes.FECTH_LOCUS_FASTA_START
  };
};

export const fetchLocusFasta = locus_id => {
  return dispatch => {
    dispatch(fetchLocusFastaStart());
    axios
      .get("loci/" + locus_id + "/fasta")
      .then(res => {
        console.log(res);
        dispatch(fetchLocusFastaSuccess());
      })
      .catch(fastaErr => {
        dispatch(fetchLocusFastaFail(fastaErr));
      });
  };
};

export const fetchLocusUniprotSuccess = locus_uniprot => {
    return {
      type: actionTypes.FECTH_LOCUS_UNIPROT_SUCCESS,
      locus_uniprot: locus_uniprot
    };
  };
  
  export const fetchLocusUniprotFail = error => {
    return {
      type: actionTypes.FECTH_LOCUS_UNIPROT_FAIL,
      error: error
    };
  };
  
  export const fetchLocusUniprotStart = () => {
    return {
      type: actionTypes.FECTH_LOCUS_UNIPROT_START
    };
  };
  
  export const fetchLocusUniprot = locus_id => {
    return dispatch => {
      dispatch(fetchLocusUniprotStart());
      axios
        .get("loci/" + locus_id + "/uniprot")
        .then(res => {
          console.log(res);
          dispatch(fetchLocusUniprotSuccess(res));
        })
        .catch(uniprotErr => {
          dispatch(fetchLocusUniprotFail(uniprotErr));
        });
    };
  };
