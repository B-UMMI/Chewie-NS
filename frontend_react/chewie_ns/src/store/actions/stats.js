import * as actionTypes from './actionTypes';
import axios from '../../axios-backend';

export const fetchStatsSuccess = (stats) => {
    return {
        type: actionTypes.FECTH_STATS_SUCCESS,
        stats: stats
    }
};

export const fetchStatsFail = (error) => {
    return {
        type: actionTypes.FECTH_STATS_FAIL,
        error: error
    }
};

export const fetchStatsStart = () => {
    return {
        type: actionTypes.FECTH_STATS_START,
    }
};

export const fetchStats = () => {
    return dispatch => {
        dispatch(fetchStatsStart());
        axios.get('/species/stats')
            .then(res => {
                // console.log("[action]")
                // console.log(res.data.message[0])
                // console.log("FOR")
                const fetchedStats = [];
                for (let key in res.data.message[0]) {
                    // console.log(key + ": " + res.data.message[0][key].value)
                    fetchedStats.push({
                        data: key + ": " + res.data.message[0][key].value,
                        id: key
                    });
                }
                // console.log(fetchedStats)
                dispatch(fetchStatsSuccess(fetchedStats));
            })
            .catch(err => {
                dispatch(fetchStatsFail(err));
            });
    }
}