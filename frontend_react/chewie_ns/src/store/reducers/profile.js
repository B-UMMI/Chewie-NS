import * as actionTypes from "../actions/actionTypes";
import { updateObject } from "../utility";

const initialState = {
  profile_data: [],
  error_profile: null,
  loading_profile: false,
};

const profileStart = (state, action) => {
    return updateObject(state, { error_profile: null, loading_profile: true });
  };
  
const profileSuccess = (state, action) => {
    return updateObject(state, {
      cuser_profile: action.cuser_profile,
      error_profile: null,
      loading_profile: false,
    });
  };
  
const profileFail = (state, action) => {
    return updateObject(state, {
      error_profile: action.error_profile,
      loading_profile: false,
    });
  };

const reducer = (state = initialState, action) => {
    switch (action.type) {
      case actionTypes.PROFILE_START:
        return profileStart(state, action);
      case actionTypes.PROFILE_SUCCESS:
        return profileSuccess(state, action);
      case actionTypes.PROFILE_FAIL:
        return profileFail(state, action);
      default:
        return state;
    }
  };
  
export default reducer;
  