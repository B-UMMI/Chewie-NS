import * as actionTypes from "../actions/actionTypes";
import { updateObject } from "../utility";

const initialState = {
    stats: [],
    loading: false, 
    error: false
};

const fetchStatsSuccess = (state, action) => {
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

const fetchStatsSpeciesSuccess = (state, action) => {
    return updateObject(state, {
        stats: action.stats,
        loading: false
    })
};

const fetchStatsSpeciesFail = (state, action) => {
    return updateObject(state, { loading: false });
};

const fetchStatsSpeciesStart = (state, action) => {
    return updateObject(state, { loading: true })
}

const reducer = (state = initialState, action) => {
    switch (action.type) {
        case actionTypes.FECTH_STATS_START : return fetchStatsStart(state, action);
        case actionTypes.FECTH_STATS_SUCCESS: return fetchStatsSuccess(state, action);
        case actionTypes.FECTH_STATS_FAIL: return fetchStatsFail(state, action);
        case actionTypes.FECTH_STATS_SPECIES_START : return fetchStatsSpeciesStart(state, action);
        case actionTypes.FECTH_STATS_SPECIES_SUCCESS: return fetchStatsSpeciesSuccess(state, action);
        case actionTypes.FECTH_STATS_SPECIES_FAIL: return fetchStatsSpeciesFail(state, action);
        default: return state;
    }
}

export default reducer;
