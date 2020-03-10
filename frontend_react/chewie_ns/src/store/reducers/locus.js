import * as actionTypes from "../actions/actionTypes";
import { updateObject } from "../utility";

const initialState = {
    locus_fasta: [],
    locus_uniprot: [], 
    fasta_data: [],
    scatter_data: [],
    basic_stats: [],
    blastxQuery: [],
    blastnQuery: [],
    loading: false, 
    error: false
};

const fetchLocusFastaSuccess = (state, action) => {
    return updateObject(state, {
        locus_fasta: action.locus_fasta,
        fasta_data: action.fasta_data,
        scatter_data: action.scatter_data,
        basic_stats: action.basic_stats,
        blastxQuery: action.blastxQuery,
        blastnQuery: action.blastnQuery,
        loading: false
    })
};

const fetchLocusFastaFail = (state, action) => {
    return updateObject(state, { loading: false });
};

const fetchLocusFastaStart = (state, action) => {
    return updateObject(state, { loading: true })
}

const fetchLocusUniprotFail = (state, action) => {
    return updateObject(state, { loading: false });
};

const fetchLocusUniprotStart = (state, action) => {
    return updateObject(state, { loading: true })
}

const fetchLocusUniprotSuccess = (state, action) => {
    return updateObject(state, {
        locus_uniprot: action.locus_uniprot,
        loading: false
    })
};

const reducer = (state = initialState, action) => {
    switch (action.type) {
        case actionTypes.FECTH_LOCUS_FASTA_START : return fetchLocusFastaStart(state, action);
        case actionTypes.FECTH_LOCUS_FASTA_SUCCESS: return fetchLocusFastaSuccess(state, action);
        case actionTypes.FECTH_LOCUS_FASTA_FAIL: return fetchLocusFastaFail(state, action);
        case actionTypes.FECTH_LOCUS_UNIPROT_START : return fetchLocusUniprotStart(state, action);
        case actionTypes.FECTH_LOCUS_UNIPROT_SUCCESS: return fetchLocusUniprotSuccess(state, action);
        case actionTypes.FECTH_LOCUS_UNIPROT_FAIL: return fetchLocusUniprotFail(state, action);

        default: return state;
    }
}

export default reducer;
