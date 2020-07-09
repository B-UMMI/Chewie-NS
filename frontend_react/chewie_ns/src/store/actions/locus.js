import * as actionTypes from "./actionTypes";
import axios from "../../axios-backend";

export const fetchLocusFastaSuccess = (
  locus_fasta,
  fasta_data,
  scatter_data,
  basic_stats,
  blastxQuery,
  blastnQuery
) => {
  return {
    type: actionTypes.FECTH_LOCUS_FASTA_SUCCESS,
    locus_fasta: locus_fasta,
    fasta_data: fasta_data,
    scatter_data: scatter_data,
    basic_stats: basic_stats,
    blastxQuery: blastxQuery,
    blastnQuery: blastnQuery,
  };
};

export const fetchLocusFastaFail = (error) => {
  return {
    type: actionTypes.FECTH_LOCUS_FASTA_FAIL,
    error: error,
  };
};

export const fetchLocusFastaStart = () => {
  return {
    type: actionTypes.FECTH_LOCUS_FASTA_START,
  };
};

export const fetchLocusFasta = (locus_id) => {
  return (dispatch) => {
    dispatch(fetchLocusFastaStart());
    axios
      .get("loci/" + locus_id + "/fasta")
      .then((res) => {
        //console.log(res.data.Fasta[0]);
        const median = (arr) => {
          const mid = Math.floor(arr.length / 2),
            nums = [...arr].sort((a, b) => a - b);
          return arr.length % 2 !== 0
            ? nums[mid]
            : (nums[mid - 1] + nums[mid]) / 2;
        };

        let allele_ids = [];
        let nucSeqLen = [];
        let histogram_data = [];
        let scatter_data = [];
        let basic_stats = [];
        let fastaData = [];
        let blastData = [];
        const locusName = res.data.Fasta[0].name.value;
        for (let key in res.data.Fasta) {
          allele_ids.push(res.data.Fasta[key].allele_id.value);
          nucSeqLen.push(res.data.Fasta[key].nucSeqLen.value);

          fastaData.push(
            ">" +
              locusName +
              "_" +
              res.data.Fasta[key].allele_id.value +
              "\n" +
              res.data.Fasta[key].nucSeq.value
          );
          // blastData.push(">" + locusName + "_" + res.data.Fasta[key].allele_id.value + "%0A" + res.data.Fasta[key].nucSeq.value)
        }

        blastData.push(
          ">" +
            locusName +
            "_" +
            res.data.Fasta[0].allele_id.value +
            "%0A" +
            res.data.Fasta[0].nucSeq.value
        );

        // let concatBlastDATA = blastData.join("%0A");

        let blastxQuery =
          "https://blast.ncbi.nlm.nih.gov/Blast.cgi?PROGRAM=blastx&PAGE_TYPE=BlastSearch&LINK_LOC=blasthome&QUERY=" +
          blastData;
        let blastnQuery =
          "https://blast.ncbi.nlm.nih.gov/Blast.cgi?PROGRAM=blastn&PAGE_TYPE=BlastSearch&LINK_LOC=blasthome&QUERY=" +
          blastData;

        const min_len = Math.min(...nucSeqLen.map(Number));
        const max_len = Math.max(...nucSeqLen.map(Number));
        const median_len = median(nucSeqLen.map(Number));

        basic_stats.push({
          num_alleles: nucSeqLen.length,
          size_range: min_len.toString() + "-" + max_len.toString(),
          median: median_len,
        });

        histogram_data.push({
          x: nucSeqLen,
          y: allele_ids,
          type: "histogram",
          name: "Locus Details",
        });
        scatter_data.push({
          x: allele_ids,
          y: nucSeqLen,
          type: "scatter",
          name: "Locus Details",
          mode: "markers",
        });
        dispatch(
          fetchLocusFastaSuccess(
            histogram_data,
            fastaData,
            scatter_data,
            basic_stats,
            blastxQuery,
            blastnQuery
          )
        );
      })
      .catch((fastaErr) => {
        dispatch(fetchLocusFastaFail(fastaErr));
      });
  };
};

export const fetchLocusUniprotSuccess = (locus_uniprot) => {
  return {
    type: actionTypes.FECTH_LOCUS_UNIPROT_SUCCESS,
    locus_uniprot: locus_uniprot,
  };
};

export const fetchLocusUniprotFail = (error) => {
  return {
    type: actionTypes.FECTH_LOCUS_UNIPROT_FAIL,
    error: error,
  };
};

export const fetchLocusUniprotStart = () => {
  return {
    type: actionTypes.FECTH_LOCUS_UNIPROT_START,
  };
};

export const fetchLocusUniprot = (locus_id) => {
  return (dispatch) => {
    dispatch(fetchLocusUniprotStart());
    axios
      .get("loci/" + locus_id)
      .then((res) => {
        console.log("res.data");
        console.log(res.data[0]);
        let uniprot_annot = [];
        uniprot_annot.push({
          locus_label: res.data[0].name.value,
          uniprot_label: res.data[0].UniprotLabel.value,
          uniprot_submitted_name: res.data[0].UniprotName.value,
          uniprot_uri: res.data[0].UniprotURI.value,
          user_annotation: res.data[0].UserAnnotation.value,
          custom_annotation: res.data[0].CustomAnnotation.value,
        });
        console.log("Uniprot annot");
        console.log(uniprot_annot);
        dispatch(fetchLocusUniprotSuccess(uniprot_annot));
      })
      .catch((uniprotErr) => {
        dispatch(fetchLocusUniprotFail(uniprotErr));
      });
  };
};
