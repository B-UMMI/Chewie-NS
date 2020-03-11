import React, { Component } from "react";
import { connect } from 'react-redux';

import Aux from "../Aux/Aux";
import classes from "./Layout.module.css";
// import Toolbar from "../../components/Navigation/Toolbar/Toolbar";
// import SideDrawer from "../../components/Navigation/SideDrawer/SideDrawer";
import MuiSideDrawer from "../../components/Navigation/MuiSideDrawer/MuiSideDrawer";

class Layout extends Component {
  // state = {
  //   showSideDrawer: false
  // }

  // sideDrawerClosedHandler = () => {
  //   this.setState({showSideDrawer: false});
  // }

  // // Set state when it depends on the old state
  // sideDrawerToggleHandler = () => {
  //   this.setState((prevState) => {
  //     return {showSideDrawer: !this.state.showSideDrawer};
  //   } );
  // }

  render() {
    return (
      <Aux>
        {/* <Toolbar 
          isAuth={this.props.isAuthenticated}
          drawerToggleClicked={this.sideDrawerToggleHandler}/>
        <SideDrawer
          isAuth={this.props.isAuthenticated} 
          open={this.state.showSideDrawer}
          closed={this.sideDrawerClosedHandler} /> */}
        <MuiSideDrawer />
        <main className={classes.Content}>
          {this.props.children}</main>
      </Aux>
    );
  }
}

const mapStateToProps = state => {
  return {
    isAuthenticated: state.auth.token !== null
  };
};

export default connect(mapStateToProps)(Layout);

