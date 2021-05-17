import axios from "../../axios-backend";

import * as actionTypes from "./actionTypes";

export const profileStart = () => {
  return {
    type: actionTypes.PROFILE_START,
  };
};

export const profileSuccess = (data) => {
  return {
    type: actionTypes.PROFILE_SUCCESS,
    cuser_profile: data,
  };
};

export const profileFail = (error) => {
  return {
    type: actionTypes.PROFILE_FAIL,
    error_profile: error,
  };
};

export const fetchProfile = (token) => {
  return (dispatch) => {
    dispatch(profileStart());
    const url = "/user/current_user/profile";
    const headers = {
      "Content-Type": "application/json",
      Authorization: token,
    };
    axios
      .get(url, {
        headers: headers,
      })
      .then((response) => {
        // console.log(response);

        dispatch(profileSuccess(response.data.table_data));
      })
      .catch((err) => {
        console.log(err);
        // dispatch(authCuserProfileFail(err.response.data.error));
      });
  };
};
