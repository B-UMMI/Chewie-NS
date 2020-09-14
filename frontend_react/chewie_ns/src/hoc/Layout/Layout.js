import React, { Component } from "react";
import { connect } from "react-redux";

// Chewie local imports
import Aux from "../Aux/Aux";
import classes from "./Layout.module.css";
import MuiSideDrawer from "../../components/Navigation/MuiSideDrawer/MuiSideDrawer";

class Layout extends Component {
  render() {
    return (
      <Aux>
        <MuiSideDrawer />
        <main className={classes.Content}>{this.props.children}</main>
      </Aux>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    isAuthenticated: state.auth.token !== null,
  };
};

export default connect(mapStateToProps)(Layout);
