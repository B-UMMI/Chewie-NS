import React from "react";

import classes from "./NavigationItems.module.css";
import NavigationItem from "./NavigationItem/NavigationItem";

// Material UI components
import IconButton from "@material-ui/core/IconButton";
// import GitHubIcon from '@material-ui/icons/GitHub';
import SvgIcon from '@material-ui/core/SvgIcon';
import { mdiApi } from '@mdi/js';
import { mdiGithubCircle } from '@mdi/js';


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
    <NavigationItem link="/stats">Schemas</NavigationItem>
    {/* <NavigationItem link="/annotations">Annotations</NavigationItem> */}
    <IconButton
      href={"https://194.210.120.209/api/NS/api/docs"}
      target={"_blank"}
      rel="noopener noreferrer" // Check --> https://material-ui.com/components/links/#security
    >
      <SvgIcon fontSize="large" htmlColor="#EEEEEE"> <path d={mdiApi} /> </SvgIcon>
    </IconButton>
    <IconButton
      href={"https://github.com/B-UMMI/Nomenclature_Server_docker_compose"}
      target={"_blank"}
      rel="noopener noreferrer"
    >
      {/* <GitHubIcon fontSize="large" color="action" /> */}
      <SvgIcon fontSize="large" htmlColor="#EEEEEE"> <path d={mdiGithubCircle} /> </SvgIcon>
    </IconButton>
  </ul>
);

export default navigationItems;
