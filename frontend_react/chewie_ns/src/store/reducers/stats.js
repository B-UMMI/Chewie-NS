import * as actionTypes from "../actions/actionTypes";
import { updateObject } from "../utility";

const initialState = {
    stats: [],
    loading: false, 
    error: false
};

const fetchStatsSuccess = (state, action) => {
    // console.log("[stats reducer action]")
    // console.log(action)
    return updateObject(state, {
        stats: action.stats,
        loading: false
    })
};

const fetchStatsFail = (state, action) => {
    return updateObject(state, { loading: false });
};

const fetchStatsStart = (state, action) => {
    return updateObject(state, { loading: true })
}

const reducer = (state = initialState, action) => {
    switch (action.type) {
        case actionTypes.FECTH_STATS_START : return fetchStatsStart(state, action);
        case actionTypes.FECTH_STATS_SUCCESS: return fetchStatsSuccess(state, action);
        case actionTypes.FECTH_STATS_FAIL: return fetchStatsFail(state, action);
        default: return state;
    }
}

export default reducer;