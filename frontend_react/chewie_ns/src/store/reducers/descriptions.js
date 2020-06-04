import * as actionTypes from "../actions/actionTypes";
import { updateObject } from "../utility";

const initialState = {
    descriptions: "",
    loading: false, 
    error: false
};

const fetchDescriptionsSuccess = (state, action) => {
    return updateObject(state, {
        descriptions: action.descriptions,
        loading: false
    })
};

const fetchDescriptionsFail = (state, action) => {
    return updateObject(state, { loading: false });
};

const fetchDescriptionsStart = (state, action) => {
    return updateObject(state, { loading: true })
}


const reducer = (state = initialState, action) => {
    switch (action.type) {
        case actionTypes.FECTH_DESCRIPTIONS_START : return fetchDescriptionsStart(state, action);
        case actionTypes.FECTH_DESCRIPTIONS_SUCCESS: return fetchDescriptionsSuccess(state, action);
        case actionTypes.FECTH_DESCRIPTIONS_FAIL: return fetchDescriptionsFail(state, action);

        default: return state;
    }
}

export default reducer;