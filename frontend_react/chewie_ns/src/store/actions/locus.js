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
        // console.log(res);
        let allele_ids = [];
        let nucSeqLen = [];
        let plot_data = [];
        for (let key in res.data.Fasta) {
          allele_ids.push(res.data.Fasta[key].allele_id.value)
          nucSeqLen.push((res.data.Fasta[key].nucSeq.value).length)
        }
        // console.log(allele_ids);
        // console.log(nucSeqLen);
        plot_data.push({
          x: nucSeqLen,
          y: allele_ids,
          type: "histogram",
          name: "Locus Details"
        })
        dispatch(fetchLocusFastaSuccess(plot_data));
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
          // console.log(res.data);
          let uniprot_annot = [];
          uniprot_annot.push({
            uniprot_label: res.data.UniprotInfo[0].UniprotLabel.value,
            uniprot_submitted_name: res.data.UniprotInfo[0].UniprotSName.value,
            uniprot_uri: res.data.UniprotInfo[0].UniprotURI.value
          })
          dispatch(fetchLocusUniprotSuccess(uniprot_annot));
        })
        .catch(uniprotErr => {
          dispatch(fetchLocusUniprotFail(uniprotErr));
        });
    };
  };
