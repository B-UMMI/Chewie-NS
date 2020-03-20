import React, { Component } from "react";
import { connect } from "react-redux";
import { Redirect, Link as RouterLink } from "react-router-dom";

import * as actions from "../../../store/actions/index";

// Material Ui imports
import Button from "@material-ui/core/Button";
import CssBaseline from "@material-ui/core/CssBaseline";
import TextField from "@material-ui/core/TextField";
import Link from "@material-ui/core/Link";
import Grid from "@material-ui/core/Grid";
import Box from "@material-ui/core/Box";
import Typography from "@material-ui/core/Typography";
import { withStyles } from "@material-ui/core/styles";
import Container from "@material-ui/core/Container";

import InputAdornment from "@material-ui/core/InputAdornment";
import IconButton from "@material-ui/core/IconButton";
import Visibility from "@material-ui/icons/Visibility";
import VisibilityOff from "@material-ui/icons/VisibilityOff";

// import Snackbar from "@material-ui/core/Snackbar";
// import MuiAlert from '@material-ui/lab/Alert';
// import CloseIcon from "@material-ui/icons/Close";

const styles = theme => ({
  paper: {
    marginTop: theme.spacing(8),
    display: "flex",
    flexDirection: "column",
    alignItems: "center"
  },
  avatar: {
    margin: theme.spacing(1),
    backgroundColor: theme.palette.secondary.main
  },
  form: {
    width: "100%", // Fix IE 11 issue.
    marginTop: theme.spacing(3)
  },
  submit: {
    margin: theme.spacing(3, 0, 2)
  }
});

class SignUp extends Component {
  state = {
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
    // status: {
    //   msg: "Error. Passwords do not match. Please try again.",
    //   key: Math.random()
    // },
    // openSnackBar: false,
    showPassword: false,
    isSignup: true
  };

  componentDidMount() {
    if (this.props.authRedirectPath !== "/") {
      this.props.onSetAuthRedirectPath();
    }
  }

  handleClickShowPassword = () => {
    this.setState({ showPassword: !this.state.showPassword });
  };

  handleMouseDownPassword = event => {
    event.preventDefault();
  };

  //   handleOpenSnackBar = () => {
  //     this.setState({ openSnackBar: true });
  //   };

  //   handleCloseSnackBar = (event, reason) => {
  //     if (reason === "clickaway") {
  //       return;
  //     }
  //   };

  onSubmitHandler = event => {
    event.preventDefault();
    console.log(event);
    console.log(this.state.email);
    console.log(this.state.username);
    console.log(this.state.password);
    console.log(this.state.confirmPassword);

    if (this.state.password === this.state.confirmPassword) {
      console.log("Happy Chewie");
    } else {
      //   this.setState({ openSnackBar: true, status: "error" });
      alert("Passwords do not match. Please try again.");
    }
    // this.props.onAuth(
    //   this.state.email,
    //   this.state.password,
    //   this.state.isSignup
    // );
  };

  render() {
    const { classes } = this.props;

    const copyright = (
      <Typography variant="body2" color="textSecondary" align="center">
        {"Copyright © "}
        UMMI {new Date().getFullYear()}
        {"."}
      </Typography>
    );

    let visibilityIcon = (
      <InputAdornment position="end">
        <IconButton
          aria-label="toggle password visibility"
          onClick={e => this.handleClickShowPassword(e)}
          onMouseDown={e => this.handleMouseDownPassword(e)}
        >
          {this.state.showPassword ? <Visibility /> : <VisibilityOff />}
        </IconButton>
      </InputAdornment>
    );

    // let snackBar = (
    //   <Snackbar
    //     anchorOrigin={{
    //       vertical: "bottom",
    //       horizontal: "left"
    //     }}
    //     open={this.state.open}
    //     autoHideDuration={2000}
    //     onClose={(e, r) => this.handleCloseSnackBar(e, r)}
    //     variant="warning"
    //     ContentProps={{
    //       "aria-describedby": "message-id"
    //     }}
    //     message={this.state.status.msg}
    //     key={this.state.status.key}
    //     action={[
    //       <IconButton
    //         key="close"
    //         onClick={(e, r) => this.handleCloseSnackBar(e, r)}
    //       >
    //         <CloseIcon />
    //       </IconButton>
    //     ]}
    //   />
    // );

    let errorMessage = null;

    if (this.props.error) {
      errorMessage = <p>{this.props.error.message}</p>;
    }

    let authRedirect = null;
    if (this.props.isAuthenticated) {
      authRedirect = <Redirect to={this.props.authRedirectPath} />;
    }

    return (
      <Container component="main" maxWidth="xs">
        <CssBaseline />
        <div className={classes.paper}>
          <Typography component="h1" variant="h5">
            Sign up
          </Typography>
          {authRedirect}
          <form
            className={classes.form}
            noValidate
            onSubmit={e => this.onSubmitHandler(e)}
          >
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  variant="outlined"
                  required
                  fullWidth
                  id="username"
                  label="Username"
                  name="username"
                  autoComplete="username"
                  onInput={e => this.setState({ username: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  variant="outlined"
                  required
                  fullWidth
                  id="email"
                  label="Email Address"
                  name="email"
                  autoComplete="email"
                  onInput={e => this.setState({ email: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  variant="outlined"
                  required
                  fullWidth
                  name="password"
                  label="Password"
                  type="password"
                  id="password"
                  autoComplete="current-password"
                  onInput={e => this.setState({ password: e.target.value })}
                  InputProps={{
                    id: "standard-adornment-password",
                    type: this.state.showPassword ? "text" : "password",
                    value: this.state.password,
                    endAdornment: visibilityIcon
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  variant="outlined"
                  required
                  fullWidth
                  name="password"
                  label="Confirm Password"
                  type="password"
                  id="password"
                  autoComplete="current-password"
                  onInput={e =>
                    this.setState({ confirmPassword: e.target.value })
                  }
                  InputProps={{
                    id: "standard-adornment-confirm-password",
                    type: this.state.showPassword ? "text" : "password",
                    value: this.state.confirmPassword,
                    endAdornment: visibilityIcon
                  }}
                />
              </Grid>
            </Grid>
            <Button
              type="submit"
              fullWidth
              variant="contained"
              color="primary"
              className={classes.submit}
            >
              Sign Up
            </Button>
            {/* {this.state.status === "error" ? { snackBar } : null} */}
            <Grid container justify="flex-end">
              <Grid item>
                <Link variant="body2" component={RouterLink} to="/auth">
                  Already have an account? Sign in
                </Link>
              </Grid>
            </Grid>
          </form>
        </div>
        <Box mt={5}>{copyright}</Box>
      </Container>
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

const mapDispatchToProps = dispatch => {
  return {
    onAuth: (email, password, isSignup) =>
      dispatch(actions.auth(email, password, isSignup)),
    onSetAuthRedirectPath: () => dispatch(actions.setAuthRedirectPath("/"))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withStyles(styles)(SignUp));
