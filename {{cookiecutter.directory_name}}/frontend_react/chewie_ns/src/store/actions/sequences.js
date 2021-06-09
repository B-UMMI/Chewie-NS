import * as actionTypes from "./actionTypes";
import axios from "../../axios-backend";

export const fetchSequenceSuccess = (sequence_data) => {
  return {
    type: actionTypes.FECTH_SEQUENCES_SUCCESS,
    sequence_data: sequence_data,
  };
};

export const fetchSequenceFail = (error) => {
  return {
    type: actionTypes.FECTH_SEQUENCES_FAIL,
    error: error,
  };
};

export const fetchSequenceStart = () => {
  return {
    type: actionTypes.FECTH_SEQUENCES_START,
  };
};

export const fetchSequence = (sequence) => {
  return (dispatch) => {
    dispatch(fetchSequenceStart());
    if (!/^[ATCG]+$/.test(sequence)) {
      axios
        .get("sequences/seq_info?seq_id=" + sequence)
        .then((res) => {
          let sequence_data = [];

          for (let key in res.data.result) {
            let species_id = res.data.result[key].schemas.value.split("/")[6];

            let species_name = res.data.result[key].name.value;

            let schema_id = res.data.result[key].schemas.value.substring(
              res.data.result[key].schemas.value.lastIndexOf("/") + 1
            );

            let locusId = res.data.result[key].locus.value.substring(
              res.data.result[key].locus.value.lastIndexOf("/") + 1
            );

            sequence_data.push({
              schemas_url:
                "https://chewbbaca.online/species/" +
                species_id +
                "/schemas/" +
                schema_id,
              schemas_id: schema_id,
              locus_url:
                "https://chewbbaca.online/species/" +
                species_id +
                "/schemas/" +
                schema_id +
                "/locus/" +
                locusId,
              locus_id: locusId,
              species_name: species_name,
              alleles: res.data.number_alleles_loci,
            });
          }

          dispatch(fetchSequenceSuccess(sequence_data));
        })
        .catch((seqErr) => {
          dispatch(fetchSequenceFail(seqErr));
        });
    } else {
      axios
        .get("sequences/seq_info?sequence=" + sequence)
        .then((res) => {
          let sequence_data = [];

          for (let key in res.data.result) {
            let species_id = res.data.result[key].schemas.value.split("/")[6];

            let species_name = res.data.result[key].name.value;

            let schema_id = res.data.result[key].schemas.value.substring(
              res.data.result[key].schemas.value.lastIndexOf("/") + 1
            );

            let locusId = res.data.result[key].locus.value.substring(
              res.data.result[key].locus.value.lastIndexOf("/") + 1
            );

            sequence_data.push({
              schemas_url:
                "https://chewbbaca.online/species/" +
                species_id +
                "/schemas/" +
                schema_id,
              schemas_id: schema_id,
              locus_url:
                "https://chewbbaca.online/species/" +
                species_id +
                "/schemas/" +
                schema_id +
                "/locus/" +
                locusId,
              locus_id: locusId,
              species_name: species_name,
              alleles: res.data.number_alleles_loci,
            });
          }

          dispatch(fetchSequenceSuccess(sequence_data));
        })
        .catch((seqErr) => {
          dispatch(fetchSequenceFail(seqErr));
        });
    }
  };
};
