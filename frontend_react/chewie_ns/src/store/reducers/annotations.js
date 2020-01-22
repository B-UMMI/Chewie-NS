import * as actionTypes from "../actions/actionTypes";
import { updateObject } from "../utility";

const initialState = {
    annotations: [],
    loading: false, 
    error: false
};

const fetchAnnotationsSuccess = (state, action) => {
    return updateObject(state, {
        annotations: action.annotations,
        loading: false
    })
};

const fetchAnnotationsFail = (state, action) => {
    return updateObject(state, { loading: false });
};

const fetchAnnotationsStart = (state, action) => {
    return updateObject(state, { loading: true })
}


const reducer = (state = initialState, action) => {
    switch (action.type) {
        case actionTypes.FECTH_ANNOTATIONS_START : return fetchAnnotationsStart(state, action);
        case actionTypes.FECTH_ANNOTATIONS_SUCCESS: return fetchAnnotationsSuccess(state, action);
        case actionTypes.FECTH_ANNOTATIONS_FAIL: return fetchAnnotationsFail(state, action);

        default: return state;
    }
}

export default reducer;