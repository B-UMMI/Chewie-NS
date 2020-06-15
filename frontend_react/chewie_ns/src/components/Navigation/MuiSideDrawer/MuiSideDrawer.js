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
import ListItem from "@material-ui/core/ListItem";
import ListItemIcon from "@material-ui/core/ListItemIcon";
import ListItemText from "@material-ui/core/ListItemText";
import Typography from "@material-ui/core/Typography";
import Divider from "@material-ui/core/Divider";
import Button from "@material-ui/core/Button";
import IconButton from "@material-ui/core/IconButton";
import SvgIcon from "@material-ui/core/SvgIcon";

// Material UI  icon imports
import MenuIcon from "@material-ui/icons/Menu";
import ChevronLeftIcon from "@material-ui/icons/ChevronLeft";
import ChevronRightIcon from "@material-ui/icons/ChevronRight";
import HomeIcon from "@material-ui/icons/Home";
import DescriptionIcon from "@material-ui/icons/Description";
import InfoIcon from "@material-ui/icons/Info";
import GitHubIcon from "@material-ui/icons/GitHub";
import ChromeReaderModeIcon from "@material-ui/icons/ChromeReaderMode";
import SearchIcon from "@material-ui/icons/Search";

// Material Design Icon import
import { mdiApi } from "@mdi/js";

// React Router Dom import
import { Link } from "react-router-dom";

const drawerWidth = 240;

const styles = (theme) => ({
  root: {
    display: "flex",
  },
  appBar: {
    zIndex: theme.zIndex.drawer + 1,
    transition: theme.transitions.create(["margin", "width"], {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
  },
  appBarShift: {
    marginLeft: drawerWidth,
    width: `calc(100% - ${drawerWidth}px)`,
    transition: theme.transitions.create(["margin", "width"], {
      easing: theme.transitions.easing.easeOut,
      duration: theme.transitions.duration.enteringScreen,
    }),
  },
  menuButton: {
    // marginRight: theme.spacing(2)
    marginRight: 36,
  },
  hide: {
    display: "none",
  },
  drawer: {
    width: drawerWidth,
    flexShrink: 0,
    whiteSpace: "nowrap",
  },
  drawerOpen: {
    backgroundColor: "#3b3b3b",
    color: "white",
    width: drawerWidth,
    transition: theme.transitions.create("width", {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.enteringScreen,
    }),
  },
  drawerClose: {
    backgroundColor: "#3b3b3b",
    color: "white",
    transition: theme.transitions.create("width", {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
    overflowX: "hidden",
    width: theme.spacing(7) + 1,
    [theme.breakpoints.up("sm")]: {
      width: theme.spacing(9) + 1,
    },
  },
  // drawerPaper: {
  //   width: drawerWidth
  // },
  drawerHeader: {
    display: "flex",
    alignItems: "center",
    padding: theme.spacing(0, 1),
    ...theme.mixins.toolbar,
    justifyContent: "flex-end",
  },
  content: {
    flexGrow: 1,
    padding: theme.spacing(3),
    marginTop: "10px",
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
    flexGrow: 1,
  },
});

class PersistentDrawerLeft extends Component {
  constructor(props) {
    super(props);

    this.state = {
      open: false,
      hoverOpen: false,
    };

    this.mouseOverTimer = null;
  }

  handleDrawerOpen = () => {
    this.setState({ open: true });
  };

  handleDrawerClose = () => {
    this.setState({ open: false });
  };

  scheduleMouseOver = () => {
    if (this.state.open === false && this.state.hoverOpen === false) {
      this.mouseOverTimer = setTimeout(() => {
        this.handleDrawerOpen();
      }, 350);
      this.setState({ hoverOpen: true });
    }
  };

  cancelMouseOver = () => {
    if (this.state.hoverOpen === true) {
      this.handleDrawerClose();
      this.setState({ hoverOpen: false });
    }
    if (this.state.mouseOverTimer) {
      clearTimeout(this.mouseOverTimer);
      this.mouseOverTimer = null;
    }
  };

  render() {
    const { classes } = this.props;

    return (
      <div className={classes.root}>
        <CssBaseline />
        <AppBar
          position="fixed"
          className={clsx(classes.appBar, {
            [classes.appBarShift]: this.state.open,
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
          open={this.state.open}
          //onMouseEnter={() => this.scheduleMouseOver()}
          //onMouseLeave={() => this.cancelMouseOver()}
          className={clsx(classes.drawer, {
            [classes.drawerOpen]: this.state.open,
            [classes.drawerClose]: !this.state.open,
          })}
          classes={{
            paper: clsx({
              [classes.drawerOpen]: this.state.open,
              [classes.drawerClose]: !this.state.open,
            }),
          }}
        >
          <div className={classes.drawerHeader}>
            <IconButton onClick={() => this.handleDrawerClose()}>
              {this.props.theme.direction === "ltr" ? (
                <ChevronLeftIcon style={{ color: "white" }} />
              ) : (
                <ChevronRightIcon style={{ color: "white" }} />
              )}
            </IconButton>
          </div>
          <Divider />
          <List>
            <ListItem button component={Link} to="/">
              <ListItemIcon>
                <HomeIcon style={{ color: "white" }} />
              </ListItemIcon>
              <ListItemText primary={"Home"} />
            </ListItem>
            <ListItem button component={Link} to="/stats">
              <ListItemIcon>
                <DescriptionIcon style={{ color: "white" }} />
              </ListItemIcon>
              <ListItemText primary={"Schemas"} />
            </ListItem>
            <ListItem button component={Link} to="/sequences">
              <ListItemIcon>
                <SearchIcon style={{ color: "white" }} />
              </ListItemIcon>
              <ListItemText primary={"Search"} />
            </ListItem>
            <ListItem button component={Link} to="/about">
              <ListItemIcon>
                <InfoIcon style={{ color: "white" }} />
              </ListItemIcon>
              <ListItemText primary={"About Us"} />
            </ListItem>
          </List>
          <Divider />
          <List>
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
                <GitHubIcon style={{ color: "white" }} />
              </ListItemIcon>
              <ListItemText primary={"Github"} />
            </ListItem>
            <ListItem
              button
              component="a"
              href={"https://chewie-ns.readthedocs.io/en/latest/"}
              target={"_blank"}
              rel="noopener noreferrer"
            >
              <ListItemIcon>
                <ChromeReaderModeIcon style={{ color: "white" }} />
              </ListItemIcon>
              <ListItemText primary={"Read The Docs"} />
            </ListItem>
            <ListItem
              button
              component="a"
              href={"https://chewbbaca.online/api/NS/api/docs"}
              target={"_blank"}
              rel="noopener noreferrer"
            >
              <ListItemIcon>
                <SvgIcon fontSize="large" htmlColor="#ffffff">
                  {" "}
                  <path d={mdiApi} />{" "}
                </SvgIcon>
              </ListItemIcon>
              <ListItemText primary={"API"} />
            </ListItem>
          </List>
        </Drawer>
        <main className={classes.content}>
          <div className={classes.drawerHeader} />
          {this.props.children}
        </main>
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    loading: state.auth.loading,
    error: state.auth.error,
    isAuthenticated: state.auth.token !== null,
    authRedirectPath: state.auth.authRedirectPath,
  };
};

export default connect(
  mapStateToProps,
  null
)(withStyles(styles, { withTheme: true })(PersistentDrawerLeft));
