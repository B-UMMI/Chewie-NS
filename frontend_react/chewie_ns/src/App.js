import React, { Component } from 'react';
import { Route, Switch, withRouter, Redirect } from "react-router-dom";
import { connect } from "react-redux";

import Layout from "./hoc/Layout/Layout";
import Chewie from "./containers/Chewie/Chewie";
import Auth from './containers/Auth/Auth';
import Logout from './containers/Auth/Logout/Logout';
import Stats from "./containers/Stats/Stats";
import Species from "./containers/Species/Species";
import * as actions from './store/actions/index';

class App extends Component {
  componentDidMount() {
    this.props.onTryAutoSignup();
  }

  render() {

    let routes = (
      <Switch>
        <Route path="/auth" component={Auth} />
        <Route path="/" exact component={Chewie} />
        <Route path="/stats" component={Stats} />
        <Route path="/species/:species_id" component={Species} />
        <Redirect to="/" />
      </Switch>
    );

    if (this.props.isAuthenticated) {
      routes = (
        <Switch>
          <Route path="/logout" component={Logout} />
          <Route path="/stats" component={Stats} />
          <Route path="/" exact component={Chewie} />
          <Redirect to="/" />
        </Switch>
      );
    }

    return (
      <div>
        <Layout>
          {routes}
        </Layout>
      </div>
    );
  }
}

const mapStateToProps = state => {
  return {
    isAuthenticated: state.auth.token !== null
  };
};

const mapDispatchToProps = dispatch => {
  return {
    onTryAutoSignup: () => dispatch(actions.authCheckState())
  };
};


export default withRouter(connect(mapStateToProps, mapDispatchToProps)(App));
