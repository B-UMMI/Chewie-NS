import * as actionTypes from "../actions/actionTypes";
import { updateObject } from "../utility";

const initialState = {
  contribData: [],
  loading: false,
  error: false,
};

const fetchAlleleContributionSuccess = (state, action) => {
  return updateObject(state, {
    contribData: action.contribData,
    loading: false,
  });
};

const fetchAlleleContributionFail = (state, action) => {
  return updateObject(state, { loading: false });
};

const fetchAlleleContributionStart = (state, action) => {
  return updateObject(state, { loading: true });
};

const reducer = (state = initialState, action) => {
  switch (action.type) {
    case actionTypes.FETCH_ALLELE_CONTRIBUTIONS_START:
      return fetchAlleleContributionStart(state, action);
    case actionTypes.FETCH_ALLELE_CONTRIBUTIONS_SUCCESS:
      return fetchAlleleContributionSuccess(state, action);
    case actionTypes.FETCH_ALLELE_CONTRIBUTIONS_FAIL:
      return fetchAlleleContributionFail(state, action);

    default:
      return state;
  }
};

export default reducer;
