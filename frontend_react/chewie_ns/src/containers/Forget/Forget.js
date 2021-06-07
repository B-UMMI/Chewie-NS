import React, { Component } from "react";
import { connect } from "react-redux";
import { Redirect } from "react-router-dom";
import axios from "../../axios-backend";

// Chewie local import
import * as actions from "../../store/actions/index";

// Material UI imports
import Box from "@material-ui/core/Box";
import Grid from "@material-ui/core/Grid";
import Button from "@material-ui/core/Button";
import Container from "@material-ui/core/Container";
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import CssBaseline from "@material-ui/core/CssBaseline";
import { withStyles } from "@material-ui/core/styles";

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
  root: {
    width: "100%",
    "& > * + *": {
      marginTop: theme.spacing(2),
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

class Forget extends Component {
  state = {
    email: "",
    redirect: false,
    alertMui: false,
  };

  componentDidMount() {
    this.props.onSetAuthRedirectPath("/reset-token");
  }

  onSubmitHandler = (event) => {
    event.preventDefault();

    axios
      .post("/auth/forget", {
        email: this.state.email,
      })
      .then((res) => {
        if (res.status === 200) {
          alert("Please check your email for further instructions.");
          this.setState({ redirect: true });
        }
      })
      .catch((err) => {
        console.log(err);
        alert("An error has occurred. Please try again or contact support.");
        this.props.onSetAuthRedirectPath("/");
        this.setState({ redirect: true });
      });
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
            Please provide an email address to start the reset password process.
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
              SUBMIT
            </Button>
          </form>
        </div>
        <Box mt={8}>{copyright}</Box>
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
    onSetAuthRedirectPath: (path) =>
      dispatch(actions.setAuthRedirectPath(path)),
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withStyles(styles)(Forget));
