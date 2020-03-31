import React, { Component } from "react";
import { connect } from "react-redux";
import clsx from "clsx";

// Material UI imports
import { withStyles } from "@material-ui/core/styles";
import Drawer from "@material-ui/core/Drawer";
import CssBaseline from "@material-ui/core/CssBaseline";
import AppBar from "@material-ui/core/AppBar";
import Toolbar from "@material-ui/core/Toolbar";
import List from "@material-ui/core/List";
import Typography from "@material-ui/core/Typography";
import Divider from "@material-ui/core/Divider";
import IconButton from "@material-ui/core/IconButton";
import MenuIcon from "@material-ui/icons/Menu";
import ChevronLeftIcon from "@material-ui/icons/ChevronLeft";
import ChevronRightIcon from "@material-ui/icons/ChevronRight";
import ListItem from "@material-ui/core/ListItem";
import ListItemIcon from "@material-ui/core/ListItemIcon";
import ListItemText from "@material-ui/core/ListItemText";
import HomeIcon from "@material-ui/icons/Home";
import DescriptionIcon from "@material-ui/icons/Description";
import InfoIcon from "@material-ui/icons/Info";
import GitHubIcon from "@material-ui/icons/GitHub";
import ChromeReaderModeIcon from "@material-ui/icons/ChromeReaderMode";
import Button from "@material-ui/core/Button";
import SvgIcon from "@material-ui/core/SvgIcon";
import Tooltip from "@material-ui/core/Tooltip";

// Material Design Icon import
import { mdiApi } from "@mdi/js";

// React Router Dom import
import { Link } from "react-router-dom";

const drawerWidth = 240;

const styles = theme => ({
  root: {
    display: "flex"
  },
  appBar: {
    zIndex: theme.zIndex.drawer + 1,
    transition: theme.transitions.create(["margin", "width"], {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen
    })
  },
  appBarShift: {
    marginLeft: drawerWidth,
    width: `calc(100% - ${drawerWidth}px)`,
    transition: theme.transitions.create(["margin", "width"], {
      easing: theme.transitions.easing.easeOut,
      duration: theme.transitions.duration.enteringScreen
    })
  },
  menuButton: {
    // marginRight: theme.spacing(2)
    marginRight: 36
  },
  hide: {
    display: "none"
  },
  drawer: {
    width: drawerWidth,
    flexShrink: 0,
    whiteSpace: "nowrap"
  },
  drawerOpen: {
    width: drawerWidth,
    // backgroundColor: "#3b3b3b",
    transition: theme.transitions.create("width", {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.enteringScreen
    })
  },
  drawerClose: {
    transition: theme.transitions.create("width", {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen
    }),
    overflowX: "hidden",
    width: theme.spacing(7) + 1,
    [theme.breakpoints.up("sm")]: {
      width: theme.spacing(9) + 1
    }
  },
  // drawerPaper: {
  //   width: drawerWidth
  // },
  drawerHeader: {
    display: "flex",
    alignItems: "center",
    padding: theme.spacing(0, 1),
    ...theme.mixins.toolbar,
    justifyContent: "flex-end"
  },
  content: {
    flexGrow: 1,
    padding: theme.spacing(3)
    // transition: theme.transitions.create("margin", {
    //   easing: theme.transitions.easing.sharp,
    //   duration: theme.transitions.duration.leavingScreen
    // }),
    // marginLeft: -drawerWidth
  },
  // contentShift: {
  //   transition: theme.transitions.create("margin", {
  //     easing: theme.transitions.easing.easeOut,
  //     duration: theme.transitions.duration.enteringScreen
  //   }),
  //   marginLeft: 0
  // },
  title: {
    flexGrow: 1
  }
});

class PersistentDrawerLeft extends Component {
  state = {
    open: false
  };

  handleDrawerOpen = () => {
    this.setState({ open: true });
  };

  handleDrawerClose = () => {
    this.setState({ open: false });
  };

  render() {
    const { classes } = this.props;

    return (
      <div className={classes.root}>
        <CssBaseline />
        <AppBar
          position="fixed"
          className={clsx(classes.appBar, {
            [classes.appBarShift]: this.state.open
          })}
          color="primary"
          style={{ backgroundColor: "#3b3b3b" }}
        >
          <Toolbar>
            <IconButton
              color="inherit"
              aria-label="open drawer"
              onClick={() => this.handleDrawerOpen()}
              edge="start"
              className={clsx(
                classes.menuButton,
                this.state.open && classes.hide
              )}
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" className={classes.title}>
              Chewie-NS
            </Typography>
            {/* <Button color="inherit" component={Link} to="/auth">
              Login
            </Button> */}
            {!this.props.isAuthenticated ? (
              <Button color="inherit" component={Link} to="/auth">
                Login
              </Button>
            ) : (
              <Button color="inherit" component={Link} to="/logout">
                Logout
              </Button>
            )}
          </Toolbar>
        </AppBar>
        <Drawer
          variant="permanent"
          className={clsx(classes.drawer, {
            [classes.drawerOpen]: this.state.open,
            [classes.drawerClose]: !this.state.open
          })}
          // anchor="left"
          open={this.state.open}
          classes={{
            paper: clsx({
              [classes.drawerOpen]: this.state.open,
              [classes.drawerClose]: !this.state.open
            })
          }}
        >
          <div className={classes.drawerHeader}>
            <IconButton onClick={() => this.handleDrawerClose()}>
              {this.props.theme.direction === "rtl" ? (
                <ChevronLeftIcon />
              ) : (
                <ChevronRightIcon />
              )}
            </IconButton>
          </div>
          <Divider />
          <List>
            <Tooltip title="Home">
              <ListItem button component={Link} to="/">
                <ListItemIcon>
                  <HomeIcon />
                </ListItemIcon>
                <ListItemText primary={"Home"} />
              </ListItem>
            </Tooltip>
            <Tooltip title="Schemas">
              <ListItem button component={Link} to="/stats">
                <ListItemIcon>
                  <DescriptionIcon />
                </ListItemIcon>
                <ListItemText primary={"Schemas"} />
              </ListItem>
            </Tooltip>
          </List>
          <Divider />
          <List>
            <Tooltip title="About Us">
              <ListItem button component={Link} to="/about">
                <ListItemIcon>
                  <InfoIcon />
                </ListItemIcon>
                <ListItemText primary={"About Us"} />
              </ListItem>
            </Tooltip>
            <Tooltip title="Github">
              <ListItem
                button
                component="a"
                href={
                  "https://github.com/B-UMMI/Nomenclature_Server_docker_compose"
                }
                target={"_blank"}
                rel="noopener noreferrer"
              >
                <ListItemIcon>
                  <GitHubIcon />
                </ListItemIcon>
                <ListItemText primary={"Github"} />
              </ListItem>
            </Tooltip>
            <Tooltip title="Read the Docs WIP">
              <ListItem button>
                <ListItemIcon>
                  <ChromeReaderModeIcon />
                </ListItemIcon>
                <ListItemText primary={"Read The Docs WIP"} />
              </ListItem>
            </Tooltip>
            <Tooltip title="API">
              <ListItem
                button
                component="a"
                href={"https://194.210.120.209/api/NS/api/docs"}
                target={"_blank"}
                rel="noopener noreferrer"
              >
                <ListItemIcon>
                  <SvgIcon fontSize="large" htmlColor="#000000">
                    {" "}
                    <path d={mdiApi} />{" "}
                  </SvgIcon>
                </ListItemIcon>
                <ListItemText primary={"API"} />
              </ListItem>
            </Tooltip>
          </List>
        </Drawer>
        <main className={classes.content}>
          <div className={classes.drawerHeader} />
        </main>
      </div>
    );
  }
}

const mapStateToProps = state => {
  return {
    loading: state.auth.loading,
    error: state.auth.error,
    isAuthenticated: state.auth.token !== null,
    authRedirectPath: state.auth.authRedirectPath
  };
};

export default connect(
  mapStateToProps,
  null
)(withStyles(styles, { withTheme: true })(PersistentDrawerLeft));
