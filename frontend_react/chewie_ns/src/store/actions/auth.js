import axios from "../../axios-backend";

import * as actionTypes from "./actionTypes";

export const authStart = () => {
  return {
    type: actionTypes.AUTH_START,
  };
};

export const authSuccess = (token) => {
  return {
    type: actionTypes.AUTH_SUCCESS,
    token: token,
    // userId: userId
  };
};

export const authFail = (error) => {
  return {
    type: actionTypes.AUTH_FAIL,
    error: error,
  };
};

export const logout = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("expirationDate");
  // localStorage.removeItem('userId');
  return {
    type: actionTypes.AUTH_LOGOUT,
  };
};

export const checkAuthTimeout = (expirationTime) => {
  return (dispatch) => {
    setTimeout(() => {
      dispatch(logout());
    }, expirationTime * 1000);
  };
};

export const auth = (email, password, isSignup) => {
  return (dispatch) => {
    dispatch(authStart());
    const authData = {
      email: email,
      password: password,
    };
    let url = "/user/register_user";
    if (!isSignup) {
      url = "/auth/login";
    }
    axios
      .post(url, authData)
      .then((response) => {
        console.log(response);
        const expirationDate = new Date(new Date().getTime() + 10800 * 1000); // 10800 seconds = 3 hours; Date is in miliseconds
        localStorage.setItem("token", response.data.access_token);
        localStorage.setItem("expirationDate", expirationDate);
        // localStorage.setItem('userId', response.data.localId);
        // dispatch(authSuccess(response.data.idToken, response.data.localId));
        dispatch(authSuccess(response.data.access_token));
        dispatch(checkAuthTimeout(10800));
      })
      .catch((err) => {
        console.log(err);
        dispatch(authFail(err.response.data.error));
      });
  };
};

export const setAuthRedirectPath = (path) => {
  return {
    type: actionTypes.SET_AUTH_REDIRECT_PATH,
    path: path,
  };
};

export const authCheckState = () => {
  return (dispath) => {
    const token = localStorage.getItem("token");
    if (!token) {
      dispath(logout());
    } else {
      const expirationDate = new Date(localStorage.getItem("expirationDate"));
      if (expirationDate <= new Date()) {
        dispath(logout());
      } else {
        // const userId = localStorage.getItem('userId');
        // dispath(authSuccess(token, userId));
        dispath(authSuccess(token));
        dispath(
          checkAuthTimeout(
            (expirationDate.getTime() - new Date().getTime()) / 1000
          )
        );
      }
    }
  };
};

export const authCuserStart = () => {
  return {
    type: actionTypes.AUTH_CUSER_START,
  };
};

export const authCuserSuccess = (cuser) => {
  return {
    type: actionTypes.AUTH_CUSER_SUCCESS,
    cuser: cuser,
  };
};

export const authCuserFail = (error) => {
  return {
    type: actionTypes.AUTH_CUSER_FAIL,
    error: error,
  };
};

export const authCuser = (token) => {
  return (dispatch) => {
    dispatch(authCuserStart());
    const url = "/user/current_user";
    // const token = localStorage.getItem("token");
    const headers = {
      "Content-Type": "application/json",
      Authorization: token,
    };
    axios
      .get(url, {
        headers: headers,
      })
      .then((response) => {
        console.log(response);
        const currentUser = {
          name: response.data.name,
          email: response.data.email,
          username: response.data.username,
          organization: response.data.organization,
          country: response.data.country,
        };
        console.log(currentUser);
        console.log(currentUser.name);
        console.log(currentUser.country);
        dispatch(authCuserSuccess(currentUser));
      })
      .catch((err) => {
        console.log(err);
        // dispatch(authCuserFail(err.response.data.error));
      });
  };
};
