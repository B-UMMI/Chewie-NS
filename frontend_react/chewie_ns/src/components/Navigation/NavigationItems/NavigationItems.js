import React from "react";

import classes from "./NavigationItems.module.css";
import NavigationItem from "./NavigationItem/NavigationItem";
import IconButton from "@material-ui/core/IconButton";
import GitHubIcon from '@material-ui/icons/GitHub';


const navigationItems = props => (
  <ul className={classes.NavigationItems}>
    <NavigationItem link="/" exact>
      Home
    </NavigationItem>
    {!props.isAuthenticated ? (
      <NavigationItem link="/auth">Authenticate</NavigationItem>
    ) : (
      <NavigationItem link="/logout">Logout</NavigationItem>
    )}
    {props.isAuthenticated ? (
      <NavigationItem link="/species">Species</NavigationItem>
    ) : null}
    <NavigationItem link="/stats">Stats</NavigationItem>
    <IconButton
      href={"https://github.com/B-UMMI/Nomenclature_Server_docker_compose"}
      target={"_blank"}
      rel="noreferrer" // Check --> https://material-ui.com/components/links/#security
    >
      <GitHubIcon fontSize="large" color="action"/>
    </IconButton>
  </ul>
);

export default navigationItems;
