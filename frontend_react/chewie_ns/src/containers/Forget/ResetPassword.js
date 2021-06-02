import React, { Component } from "react";
import axios from "../../axios-backend";
import { connect } from "react-redux";
import { Redirect } from "react-router-dom";

// Chewie local import
import * as actions from "../../store/actions/index";

// Material Ui imports
import Box from "@material-ui/core/Box";
import Grid from "@material-ui/core/Grid";
import Button from "@material-ui/core/Button";
import Container from "@material-ui/core/Container";
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import IconButton from "@material-ui/core/IconButton";
import CssBaseline from "@material-ui/core/CssBaseline";
import InputAdornment from "@material-ui/core/InputAdornment";
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

class ResetPassword extends Component {
  state = {
    password: "",
    confirmPassword: "",
    showPassword: false,
    redirect: false,
  };

  componentDidMount() {
    this.props.onSetAuthRedirectPath();
  }

  handleClickShowPassword = () => {
    this.setState({ showPassword: !this.state.showPassword });
  };

  handleMouseDownPassword = (event) => {
    event.preventDefault();
  };

  onSubmitHandler = (event) => {
    event.preventDefault();

    const resetToken = localStorage.getItem("resetToken");

    if (resetToken === null) {
      alert("Credentials were not provided to execute this request.");
      this.setState({ redirect: true });
    }

    // console.log(resetToken);

    const headers = {
      "Content-Type": "application/json",
      Authorization: resetToken,
    };

    if (this.state.password === this.state.confirmPassword) {
      axios
        .put(
          "/auth/reset_password",
          {
            password: this.state.password,
          },
          {
            headers: headers,
          }
        )
        .then((res) => {
          if (res.status === 201) {
            alert("You have changed your password successfully.");
            localStorage.removeItem("resetToken");
            this.setState({ redirect: true });
          }
        })
        .catch((err) => {
          console.log(err);
          alert("Invalid or expired token has been provided.");
          this.setState({ redirect: true });
        });
    } else {
      alert("Passwords do not match. Please try again.");
      window.location.reload();
    }
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
    if (this.state.redirect) {
      authRedirect = <Redirect to={this.props.authRedirectPath} />;
    }

    return (
      <Container component="main" maxWidth="xs">
        <CssBaseline />
        <div className={classes.paper}>
          {authRedirect}
          {errorMessage}
          <Typography component="h1" variant="h5">
            Please provide a new password.
          </Typography>
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
                  name="password"
                  label="Password"
                  type="password"
                  id="password"
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
          </form>
        </div>
        <Box mt={5}>{copyright}</Box>
      </Container>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    authRedirectPath: state.auth.authRedirectPath,
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    onSetAuthRedirectPath: () => dispatch(actions.setAuthRedirectPath("/")),
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withStyles(styles)(ResetPassword));
