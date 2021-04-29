import * as actionTypes from "../actions/actionTypes";
import { updateObject } from "../utility";

const initialState = {
    mode_data: [],
    total_allele_data: [],
    scatter_data: [],
    mode_data2: [],
    loading: false, 
    error: false
};

const fetchSchemaAlleleModeSuccess = (state, action) => {
    return updateObject(state, {
        mode_data: action.mode_data,
        total_allele_data: action.total_allele_data,
        scatter_data: action.scatter_data,
        mode_data2: action.mode_data2,
        loading: false
    })
};

const fetchSchemaAlleleModeFail = (state, action) => {
    return updateObject(state, { loading: false });
};

const fetchSchemaAlleleModeStart = (state, action) => {
    return updateObject(state, { loading: true })
}


const reducer = (state = initialState, action) => {
    switch (action.type) {
        case actionTypes.FETCH_SCHEMA_ALLELE_MODE_START : return fetchSchemaAlleleModeStart(state, action);
        case actionTypes.FETCH_SCHEMA_ALLELE_MODE_SUCCESS: return fetchSchemaAlleleModeSuccess(state, action);
        case actionTypes.FETCH_SCHEMA_ALLELE_MODE_FAIL: return fetchSchemaAlleleModeFail(state, action);

        default: return state;
    }
}

export default reducer;