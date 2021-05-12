import React, { Component } from "react";
import axios from "../../../axios-backend";
import { connect } from "react-redux";
import { Redirect, Link as RouterLink } from "react-router-dom";

// Chewie local import
import Aux from "../../../hoc/Aux/Aux";
import { countries } from "./countries";
import Copyright from "../../../components/Copyright/Copyright";
import * as actions from "../../../store/actions/index";

// Material Ui imports
import Grid from "@material-ui/core/Grid";
import Link from "@material-ui/core/Link";
import Button from "@material-ui/core/Button";
import Container from "@material-ui/core/Container";
import TextField from "@material-ui/core/TextField";
import IconButton from "@material-ui/core/IconButton";
import CssBaseline from "@material-ui/core/CssBaseline";
import InputAdornment from "@material-ui/core/InputAdornment";
import Autocomplete from "@material-ui/lab/Autocomplete";
import { withStyles } from "@material-ui/core/styles";

// Material UI icon imports
import Visibility from "@material-ui/icons/Visibility";
import VisibilityOff from "@material-ui/icons/VisibilityOff";

const styles = (theme) => ({
  paper: {
    marginTop: theme.spacing(8),
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
  },
  avatar: {
    margin: theme.spacing(1),
    backgroundColor: theme.palette.secondary.main,
  },
  form: {
    width: "100%", // Fix IE 11 issue.
    marginTop: theme.spacing(3),
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
  option: {
    fontSize: 15,
    "& > span": {
      marginRight: 10,
      fontSize: 18,
    },
  },
});

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

class SignUp extends Component {
  state = {
    username: "",
    organization: "",
    country: "",
    email: "",
    password: "",
    name: "",
    confirmPassword: "",
    showPassword: false,
    isSignup: true,
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

    // console.log(this.state.organization);
    console.log(this.state.country.label);

    if (this.state.password === this.state.confirmPassword) {
      axios
        .post("/user/register_user", {
          email: this.state.email,
          password: this.state.password,
          name: this.state.name,
          username: this.state.username,
          organization: this.state.organization,
          country: this.state.country.label.toString(),
        })
        .then((res) => {
          if (res.status === 200) {
            alert("You have registered successfully.");
            this.props.history.push({
              pathname: "/auth",
            });
          }
        })
        .catch((err) => {
          console.log(err);
        });
    } else {
      alert("Passwords do not match. Please try again.");
      window.location.reload();
    }
  };

  countryToFlag = (isoCode) => {
    return typeof String.fromCodePoint !== "undefined"
      ? isoCode
          .toUpperCase()
          .replace(/./g, (char) =>
            String.fromCodePoint(char.charCodeAt(0) + 127397)
          )
      : isoCode;
  };

  render() {
    const { classes } = this.props;

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
            {authRedirect}
            {errorMessage}
            <form
              className={classes.form}
              noValidate
              onSubmit={(e) => this.onSubmitHandler(e)}
            >
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <CssTextField
                    variant="outlined"
                    required
                    fullWidth
                    id="name"
                    label="Name"
                    name="name"
                    onInput={(e) => this.setState({ name: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12}>
                  <CssTextField
                    variant="outlined"
                    required
                    fullWidth
                    id="username"
                    label="Username"
                    name="username"
                    autoComplete="username"
                    onInput={(e) => this.setState({ username: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12}>
                  <CssTextField
                    variant="outlined"
                    required
                    fullWidth
                    id="organization"
                    label="Organization"
                    name="Organization"
                    onInput={(e) =>
                      this.setState({ organization: e.target.value })
                    }
                  />
                </Grid>
                <Grid item xs={12}>
                  <Autocomplete
                    id="country-select"
                    style={{ width: 300 }}
                    options={countries}
                    classes={{
                      option: classes.option,
                    }}
                    autoHighlight
                    getOptionLabel={(option) => option.label}
                    renderOption={(option) => (
                      <React.Fragment>
                        <span>{this.countryToFlag(option.code)}</span>
                        {option.label} ({option.code})
                      </React.Fragment>
                    )}
                    onChange={(event, value) =>
                      this.setState({ country: value })
                    }
                    renderInput={(params) => (
                      <CssTextField
                        {...params}
                        label="Choose a country"
                        variant="outlined"
                        fullWidth
                        inputProps={{
                          ...params.inputProps,
                          autoComplete: "new-password", // disable autocomplete and autofill
                        }}
                      />
                    )}
                  />
                </Grid>
                <Grid item xs={12}>
                  <CssTextField
                    variant="outlined"
                    required
                    fullWidth
                    id="email"
                    label="Email Address"
                    name="email"
                    autoComplete="email"
                    onInput={(e) => this.setState({ email: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12}>
                  <CssTextField
                    variant="outlined"
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
                </Grid>
                <Grid item xs={12}>
                  <CssTextField
                    variant="outlined"
                    required
                    fullWidth
                    name="password"
                    label="Confirm Password"
                    type="password"
                    id="password"
                    autoComplete="current-password"
                    onInput={(e) =>
                      this.setState({ confirmPassword: e.target.value })
                    }
                    InputProps={{
                      id: "standard-adornment-confirm-password",
                      type: this.state.showPassword ? "text" : "password",
                      value: this.state.confirmPassword,
                      endAdornment: visibilityIcon,
                    }}
                  />
                </Grid>
              </Grid>
              <Button
                type="submit"
                fullWidth
                variant="contained"
                className={classes.submit}
                classes={{
                  root: classes.buttonRoot,
                }}
              >
                SIGN UP
              </Button>
              <Grid container justify="flex-end">
                <Grid item>
                  <Link
                    variant="body2"
                    component={RouterLink}
                    to="/auth"
                    classes={{
                      root: classes.linkRoot,
                    }}
                  >
                    Already have an account? Sign in
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
)(withStyles(styles)(SignUp));
