import * as actionTypes from "../actions/actionTypes";
import { updateObject } from "../utility";

const initialState = {
    boxplotData: [],
    loading: false, 
    error: false
};

const fetchSchemaBoxSuccess = (state, action) => {
    return updateObject(state, {
        boxplotData: action.boxplotData,
        loading: false
    })
};

const fetchSchemaBoxFail = (state, action) => {
    return updateObject(state, { loading: false });
};

const fetchSchemaBoxStart = (state, action) => {
    return updateObject(state, { loading: true })
}


const reducer = (state = initialState, action) => {
    switch (action.type) {
        case actionTypes.FETCH_SCHEMA_BOX_START : return fetchSchemaBoxStart(state, action);
        case actionTypes.FETCH_SCHEMA_BOX_SUCCESS: return fetchSchemaBoxSuccess(state, action);
        case actionTypes.FETCH_SCHEMA_BOX_FAIL: return fetchSchemaBoxFail(state, action);

        default: return state;
    }
}

export default reducer;