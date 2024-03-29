import React, { Component } from "react";
import { connect } from "react-redux";

// Chewie local import
import Aux from "../../../hoc/Aux/Aux";
import * as actions from "../../../store/actions/index";
import axios from "../../../axios-backend";
import {
  PROFILE_STYLES,
  PROFILE_COLUMNS,
  PROFILE_OPTIONS,
} from "../../../components/data/table_columns/profile_columns";

import Spinner from "../../../components/UI/Spinner/Spinner";

// Material-UI components
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Grid,
  TextField,
  // CircularProgress,
  Container,
  Typography,
  withStyles,
} from "@material-ui/core";

// Material-UI Lab components
import Alert from "@material-ui/lab/Alert";

// Material-UI styles
import { createMuiTheme, MuiThemeProvider } from "@material-ui/core/styles";

// Material-UI icons
import SaveIcon from "@material-ui/icons/Save";

// Material-UI Datatables
import MUIDataTable from "mui-datatables";

// Custom TextField component
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

class ProfileDetails extends Component {
  state = {
    username: "",
    organization: "",
    country: "",
    email: "",
    name: "",
  };

  componentDidMount() {
    const token = localStorage.getItem("token");
    this.props.onToken(token);

    // this.props.onProfileTable(token);
  }

  getMuiTheme = () =>
    createMuiTheme({
      overrides: {
        MUIDataTableToolbar: {
          titleText: {
            color: "#bb7944",
          },
        },
      },
    });

  onSubmitHandler = (event) => {
    event.preventDefault();

    const token2 = localStorage.getItem("token");

    // console.log(this.props.cuser);

    const headers = {
      "Content-Type": "application/json",
      Authorization: token2,
    };

    axios
      .put(
        "/user/current_user",
        {
          email: this.state.email,
          name: this.state.name,
          username: this.state.username,
          organization: this.state.organization,
          country: this.state.country,
        },
        {
          headers: headers,
        }
      )
      .then((res) => {
        if (res.status === 200) {
          alert(
            "You have updated your profile successfully. You will now be redirected to the homepage."
          );
          this.props.history.push({
            pathname: "/",
          });
        }
      })
      .catch((err) => {
        console.log(err);
      });
  };

  render() {
    const { classes } = this.props;
    
    let profile = <Spinner />;
    let nameValue = "";
    let usernameValue = "";
    let emailValue = "";
    let organizationValue = "";
    let countryValue = "";

    let profile_table = (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <Spinner />
      </div>
    );

    if (!this.props.loading) {
      // console.log(this.props.cuser);
      const values = { ...this.props.cuser };
      // console.log(values);
      nameValue = values.name;
      usernameValue = values.username;
      emailValue = values.email;
      organizationValue = values.organization;
      countryValue = values.country;

      profile = (
        <Grid container spacing={3}>
          <Grid item md={6} xs={12}>
            <CssTextField
              fullWidth
              helperText="Please specify the username"
              label="Username"
              name="username"
              defaultValue={usernameValue}
              variant="outlined"
              onInput={(e) => this.setState({ username: e.target.value })}
            />
          </Grid>
          <Grid item md={6} xs={12}>
            <CssTextField
              fullWidth
              helperText="Please specify the name"
              label="Name"
              name="name"
              defaultValue={nameValue}
              variant="outlined"
              onInput={(e) => this.setState({ name: e.target.value })}
            />
          </Grid>
          <Grid item md={6} xs={12}>
            <CssTextField
              fullWidth
              label="Email Address"
              name="email"
              defaultValue={emailValue}
              variant="outlined"
              onInput={(e) => this.setState({ email: e.target.value })}
            />
          </Grid>
          <Grid item md={6} xs={12}>
            <CssTextField
              fullWidth
              label="Organization"
              name="organization"
              defaultValue={organizationValue}
              variant="outlined"
              onInput={(e) => this.setState({ organization: e.target.value })}
            />
          </Grid>
          <Grid item md={6} xs={12}>
            <CssTextField
              fullWidth
              label="Country"
              name="country"
              defaultValue={countryValue}
              variant="outlined"
              onInput={(e) => this.setState({ country: e.target.value })}
            />
          </Grid>
        </Grid>
      );
    }

    if (!this.props.loading_profile) {
      profile_table =
        this.props.cuser_profile === "undefined" ||
        this.props.cuser_profile === undefined ? (
          <div style={{ marginTop: "20px", width: "100%" }}>
            <Alert variant="outlined" severity="warning">
              <Typography variant="subtitle1">
                No contributions to the database yet.
              </Typography>
            </Alert>
          </div>
        ) : (
          <MuiThemeProvider theme={this.getMuiTheme()}>
            <MUIDataTable
              title={"Contributions"}
              data={this.props.cuser_profile}
              columns={PROFILE_COLUMNS}
              options={PROFILE_OPTIONS}
            />
          </MuiThemeProvider>
        );
    }

    return (
      <Aux>
        <div>
          <Container maxWidth="lg">
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <form
                  autoComplete="off"
                  noValidate
                  className={PROFILE_STYLES.root}
                  onSubmit={(e) => this.onSubmitHandler(e)}
                >
                  <Card>
                    <CardHeader
                      subheader="If you wish to the change your profile details, please fill the form below."
                      title="Profile Details"
                    />
                    <Divider />
                    <CardContent>{profile}</CardContent>
                    <Divider />
                    <Box display="flex" justifyContent="flex-end" p={2}>
                      <Button
                        variant="contained"
                        type="submit"
                        startIcon={<SaveIcon />}
                        classes={{
                          root: classes.buttonRoot,
                        }}
                      >
                        SAVE
                      </Button>
                    </Box>
                  </Card>
                </form>
              </Grid>
            </Grid>
          </Container>
        </div>
        {/* <div style={{ marginTop: "40px" }}>{profile_table}</div> */}
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
    cuser: state.auth.cuser,
    loading_profile: state.profile.loading_profile,
    error_profile: state.profile.error_profile,
    cuser_profile: state.profile.cuser_profile,
  };
};

// Map dispatch functions that trigger
// actions from redux
// to the props of this component
const mapDispatchToProps = (dispatch) => {
  return {
    onToken: (token) => dispatch(actions.authCuser(token)),
    // onProfileTable: (token) => dispatch(actions.fetchProfileContributions(token)),
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withStyles(PROFILE_STYLES)(ProfileDetails));
