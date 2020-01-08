import React from "react";

import classes from "./NavigationItems.module.css";
import NavigationItem from "./NavigationItem/NavigationItem";
// import GithubButton from "../../UI/GithubButton/GithubButton";

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
    ) : null
    }
    {/* <NavigationItem link="https://github.com/B-UMMI/Nomenclature_Server_docker_compose">Github</NavigationItem> */}
    <NavigationItem link="/stats">Stats</NavigationItem>
  </ul>
);

export default navigationItems;
