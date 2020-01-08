import * as actionTypes from "../actions/actionTypes";
import { updateObject } from "../utility";

const initialState = {
    species: [],
    loading: false, 
    error: false
};

const fetchSpeciesSuccess = (state, action) => {
    return updateObject(state, {
        species: action.species,
        loading: false
    })
};

const fetchSpeciesFail = (state, action) => {
    return updateObject(state, { loading: false });
};

const fetchSpeciesStart = (state, action) => {
    return updateObject(state, { loading: true })
}

const reducer = (state = initialState, action) => {
    switch (action.type) {
        case actionTypes.FECTH_SPECIES_START : return fetchSpeciesStart(state, action);
        case actionTypes.FECTH_SPECIES_SUCCESS: return fetchSpeciesSuccess(state, action);
        case actionTypes.FECTH_SPECIES_FAIL: return fetchSpeciesFail(state, action);
        default: return state;
    }
}

export default reducer;