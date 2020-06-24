import React from "react";
import ReactDOM from "react-dom";
import { BrowserRouter } from "react-router-dom";
import { Provider } from "react-redux";
import { createStore, applyMiddleware, compose, combineReducers } from "redux";
import thunk from "redux-thunk";

import "./index.css";
import App from "./App";
import * as serviceWorker from "./serviceWorker";

// Reducer imports
import authReducer from "./store/reducers/auth";
import statsReducer from "./store/reducers/stats";
import speciesReducer from "./store/reducers/species";
import schemaReducer from "./store/reducers/schema";
import locusReducer from "./store/reducers/locus";
import annotationsReducer from "./store/reducers/annotations";
import descriptionsReducer from "./store/reducers/descriptions";
import sequencesReducer from "./store/reducers/sequences";

const composeEnhancers = window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ || compose;

// Combine reducers into a single reducer
const rootReducer = combineReducers({
  auth: authReducer,
  stats: statsReducer,
  species: speciesReducer,
  schema: schemaReducer,
  locus: locusReducer,
  annotations: annotationsReducer,
  descriptions: descriptionsReducer,
  sequences: sequencesReducer,
});

// Create the react-redux store
// It works as central warehouse for state variables.
const store = createStore(
  rootReducer,
  composeEnhancers(applyMiddleware(thunk))
);

const app = (
  <Provider store={store}>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </Provider>
);

ReactDOM.render(app, document.getElementById("root"));

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: http://bit.ly/CRA-PWA
serviceWorker.unregister();
