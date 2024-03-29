import React, { Component } from "react";
import { connect } from "react-redux";
import { Redirect, Link as RouterLink } from "react-router-dom";

// Chewie local import
import Aux from "../../../hoc/Aux/Aux";
import * as actions from "../../../store/actions/index";
import Markdown from "../../../components/Markdown/Markdown";
import Copyright from "../../../components/Copyright/Copyright";

// Material UI imports
import Grid from "@material-ui/core/Grid";
import Link from "@material-ui/core/Link";
import Button from "@material-ui/core/Button";
import Container from "@material-ui/core/Container";
import TextField from "@material-ui/core/TextField";
import IconButton from "@material-ui/core/IconButton";
import CssBaseline from "@material-ui/core/CssBaseline";
import InputAdornment from "@material-ui/core/InputAdornment";
import { withStyles } from "@material-ui/core/styles";

// Material UI icon imports
import Visibility from "@material-ui/icons/Visibility";
import VisibilityOff from "@material-ui/icons/VisibilityOff";

// Define inline css styles
const styles = (theme) => ({
  paper: {
    marginTop: theme.spacing(8),
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
  },
  form: {
    width: "100%",
    marginTop: theme.spacing(1),
  },
  submit: {
    margin: theme.spacing(3, 0, 2),
  },
  buttonRoot: {
    boxShadow: "none",
    textTransform: "none",
    color: "#ffffff",
    borderRadius: 4,
    fontSize: 16,
    padding: "6px 12px",
    border: "1px solid",
    backgroundColor: "#3b3b3b",
    borderColor: "#3b3b3b",
    "&:hover": {
      backgroundColor: "#3b3b3b",
      borderColor: "#3b3b3b",
    },
    "&:active": {
      boxShadow: "none",
      backgroundColor: "#3b3b3b",
      borderColor: "#3b3b3b",
    },
    "&:focus": {
      boxShadow: "0 0 0 0.2rem rgba(0,123,255,.5)",
    },
  },
  linkRoot: {
    color: "#b26046",
  },
});

// Defines a custom TextField component
const CssTextField = withStyles({
  root: {
    "& label.Mui-focused": {
      color: "#b26046",
    },
    "& .MuiInput-underline:after": {
      borderBottomColor: "#b26046",
    },
    "& .MuiOutlinedInput-root": {
      "& fieldset": {
        borderColor: "black",
      },
      "&:hover fieldset": {
        borderColor: "black",
      },
      "&.Mui-focused fieldset": {
        borderColor: "#b26046",
      },
    },
  },
})(TextField);

class SignIn extends Component {
  state = {
    email: "",
    password: "",
    showPassword: false,
    isSignup: false,
  };

  componentDidMount() {
    if (this.props.authRedirectPath !== "/") {
      this.props.onSetAuthRedirectPath();
    }
  }

  handleClickShowPassword = () => {
    this.setState({ showPassword: !this.state.showPassword });
  };

  handleMouseDownPassword = (event) => {
    event.preventDefault();
  };

  onSubmitHandler = (event) => {
    event.preventDefault();
    this.props.onAuth(
      this.state.email,
      this.state.password,
      this.state.isSignup
    );
  };

  render() {
    const { classes } = this.props;

    const UserMessage = `# IMPORTANT
    A reset was performed on our databases. We kindly ask users that had an account to register once more.
    We apologize for the incovenience.`;

    let visibilityIcon = (
      <InputAdornment position="end">
        <IconButton
          aria-label="toggle password visibility"
          onClick={(e) => this.handleClickShowPassword(e)}
          onMouseDown={(e) => this.handleMouseDownPassword(e)}
        >
          {this.state.showPassword ? <Visibility /> : <VisibilityOff />}
        </IconButton>
      </InputAdornment>
    );

    let errorMessage = null;

    if (this.props.error) {
      errorMessage = <p>{this.props.error.message}</p>;
    }

    let authRedirect = null;
    if (this.props.isAuthenticated) {
      authRedirect = <Redirect to={this.props.authRedirectPath} />;
    }

    return (
      <Aux>
        <Container component="main" maxWidth="xs">
          <CssBaseline />
          <div className={classes.paper}>
            <Markdown markdown={UserMessage} />
            {authRedirect}
            {errorMessage}
            <form
              className={classes.form}
              noValidate
              onSubmit={(e) => this.onSubmitHandler(e)}
            >
              <CssTextField
                variant="outlined"
                margin="normal"
                required
                fullWidth
                id="email"
                label="Email Address"
                name="email"
                autoComplete="email"
                autoFocus
                onInput={(e) => this.setState({ email: e.target.value })}
              />
              <CssTextField
                variant="outlined"
                margin="normal"
                required
                fullWidth
                name="password"
                label="Password"
                type="password"
                id="password"
                autoComplete="current-password"
                onInput={(e) => this.setState({ password: e.target.value })}
                InputProps={{
                  id: "standard-adornment-password",
                  type: this.state.showPassword ? "text" : "password",
                  value: this.state.password,
                  endAdornment: visibilityIcon,
                }}
              />
              <Button
                type="submit"
                fullWidth
                variant="contained"
                className={classes.submit}
                classes={{
                  root: classes.buttonRoot,
                }}
              >
                SIGN IN
              </Button>
              <Grid container>
                <Grid item xs>
                  <Link
                    variant="body2"
                    component={RouterLink}
                    to="/forget"
                    classes={{ root: classes.linkRoot }}
                  >
                    Forgot password?
                  </Link>
                </Grid>
                <Grid item>
                  <Link
                    variant="body2"
                    component={RouterLink}
                    to="/register"
                    classes={{ root: classes.linkRoot }}
                  >
                    Don't have an account? Sign Up
                  </Link>
                </Grid>
              </Grid>
            </form>
          </div>
        </Container>
        <div>
          <Copyright />
        </div>
      </Aux>
    );
  }
}

// Redux functions

// Map state from the central warehouse
// to the props of this component
const mapStateToProps = (state) => {
  return {
    loading: state.auth.loading,
    error: state.auth.error,
    isAuthenticated: state.auth.token !== null,
    authRedirectPath: state.auth.authRedirectPath,
  };
};

// Map dispatch functions that trigger
// actions from redux
// to the props of this component
const mapDispatchToProps = (dispatch) => {
  return {
    onAuth: (email, password, isSignup) =>
      dispatch(actions.auth(email, password, isSignup)),
    onSetAuthRedirectPath: () => dispatch(actions.setAuthRedirectPath("/")),
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withStyles(styles)(SignIn));
