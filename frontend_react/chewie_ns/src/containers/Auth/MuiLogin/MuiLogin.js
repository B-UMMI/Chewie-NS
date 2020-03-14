import React, { Component } from "react";
import { connect } from "react-redux";
import { Redirect } from 'react-router-dom';

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


const styles = theme => ({
  paper: {
    marginTop: theme.spacing(8),
    display: "flex",
    flexDirection: "column",
    alignItems: "center"
  },
  form: {
    width: "100%",
    marginTop: theme.spacing(1)
  },
  submit: {
    margin: theme.spacing(3, 0, 2)
  }
});

class SignIn extends Component {
  state = {
    email: "",
    password: "",
    showPassword: false,
    isSignup: false,
  };

  componentDidMount() {
    if (this.props.authRedirectPath !== '/') {
      this.props.onSetAuthRedirectPath()
    }
  }

  handleClickShowPassword = () => {
    this.setState({ showPassword: !this.state.showPassword });
  };

  handleMouseDownPassword = event => {
    event.preventDefault();
  };

  onSubmitHandler = event => {
    event.preventDefault();
    this.props.onAuth(
      this.state.email,
      this.state.password,
      this.state.isSignup
    );
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

    let errorMessage = null;

    if (this.props.error) {
        errorMessage = (
        <p>{this.props.error.message}</p>
        )
    }

    let authRedirect = null;
    if (this.props.isAuthenticated) {
      authRedirect = <Redirect to={this.props.authRedirectPath} />
    }


    return (
      <Container component="main" maxWidth="xs">
        <CssBaseline />
        <div className={classes.paper}>
          <Typography component="h1" variant="h5">
            Sign in
          </Typography>
          {authRedirect}
          <form
            className={classes.form}
            noValidate
            onSubmit={e => this.onSubmitHandler(e)}
          >
            <TextField
              variant="outlined"
              margin="normal"
              required
              fullWidth
              id="email"
              label="Email Address"
              name="email"
              autoComplete="email"
              autoFocus
              onInput={e => this.setState({ email: e.target.value })}
            />
            <TextField
              variant="outlined"
              margin="normal"
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
            <Button
              type="submit"
              fullWidth
              variant="contained"
              color="primary"
              className={classes.submit}
            >
              Sign In
            </Button>
            <Grid container>
              <Grid item xs>
                <Link href="#" variant="body2">
                  Forgot password?
                </Link>
              </Grid>
              <Grid item>
                <Link href="#" variant="body2">
                  {"Don't have an account? Sign Up"}
                </Link>
              </Grid>
            </Grid>
          </form>
        </div>
        <Box mt={8}>
          {copyright}
        </Box>
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
  onAuth: (email, password, isSignup) => dispatch(actions.auth(email, password, isSignup)),
  onSetAuthRedirectPath: () => dispatch(actions.setAuthRedirectPath('/'))
};
};

export default connect(mapStateToProps, mapDispatchToProps)(withStyles(styles)(SignIn));
