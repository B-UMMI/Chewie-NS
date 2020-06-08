import * as actionTypes from "../actions/actionTypes";
import { updateObject } from "../utility";

const initialState = {
    sequence_data: [],
    loading: false, 
    error: false
};

const fetchSequenceSuccess = (state, action) => {
    return updateObject(state, {
        sequence_data: action.sequence_data,
        loading: false
    })
};

const fetchSequenceFail = (state, action) => {
    return updateObject(state, { loading: false });
};

const fetchSequenceStart = (state, action) => {
    return updateObject(state, { loading: true })
}


const reducer = (state = initialState, action) => {
    switch (action.type) {
        case actionTypes.FECTH_SEQUENCES_START : return fetchSequenceStart(state, action);
        case actionTypes.FECTH_SEQUENCES_SUCCESS: return fetchSequenceSuccess(state, action);
        case actionTypes.FECTH_SEQUENCES_FAIL: return fetchSequenceFail(state, action);

        default: return state;
    }
}

export default reducer;