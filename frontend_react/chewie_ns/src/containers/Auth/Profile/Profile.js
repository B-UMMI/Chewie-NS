import React, { Component } from "react";
import { connect } from "react-redux";
// import clsx from "clsx";

// Chewie local import
import Aux from "../../../hoc/Aux/Aux";
import * as actions from "../../../store/actions/index";

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
  CircularProgress,
  Container,
  Typography,
  withStyles,
} from "@material-ui/core";

import { createMuiTheme, MuiThemeProvider } from "@material-ui/core/styles";

import SaveIcon from "@material-ui/icons/Save";

// Material-UI Datatables
import MUIDataTable from "mui-datatables";

const styles = (theme) => ({
  root: {},
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
});

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

    this.props.onProfileTable(token);
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

    console.log(this.props.cuser);

    // const headers = {
    //   "Content-Type": "application/json",
    //   Authorization: token2,
    // };

    // axios
    //   .put(
    //     "/user/current_user",
    //     {
    //       email: this.state.email,
    //       name: this.state.name,
    //       username: this.state.username,
    //       organization: this.state.organization,
    //       country: this.state.country,
    //     },
    //     {
    //       headers: headers,
    //     }
    //   )
    //   .then((res) => {
    //     if (res.status === 200) {
    //       alert("You have updated your profile successfully");
    //       this.props.history.push({
    //         pathname: "/",
    //       });
    //     }
    //   })
    //   .catch((err) => {
    //     console.log(err);
    //   });
  };

  // onHandleChange = (event) => {
  //   this.settate = {
  //     ...this.state,
  //     [event.target.name]: event.target.value
  //   }

  render() {
    const { classes } = this.props;

    let profile = <CircularProgress />;
    let nameValue = "";
    let usernameValue = "";
    let emailValue = "";
    let organizationValue = "";
    let countryValue = "";

    let profile_table = <CircularProgress />;

    if (!this.props.loading) {
      // console.log(this.props.cuser);
      const values = { ...this.props.cuser };
      console.log(values);
      // console.log(test['name']);
      // console.log(test.username);
      // console.log(test);
      nameValue = values.name;
      usernameValue = values.username;
      emailValue = values.email;
      organizationValue = values.organization;
      countryValue = values.country;

      profile = (
        <Grid container spacing={3}>
          <Grid item md={6} xs={12}>
            <TextField
              fullWidth
              helperText="Please specify the username"
              label="Username"
              name="username"
              // onChange={(e) => this.onHandleChange(e)}
              // required
              defaultValue={usernameValue}
              variant="outlined"
              onInput={(e) => this.setState({ username: e.target.value })}
            />
          </Grid>
          <Grid item md={6} xs={12}>
            <TextField
              fullWidth
              helperText="Please specify the name"
              label="Name"
              name="name"
              // onChange={(e) => this.onHandleChange(e)}
              // required
              defaultValue={nameValue}
              variant="outlined"
              onInput={(e) => this.setState({ name: e.target.value })}
            />
          </Grid>
          <Grid item md={6} xs={12}>
            <TextField
              fullWidth
              label="Email Address"
              name="email"
              // onChange={(e) => this.onHandleChange(e)}
              // required
              defaultValue={emailValue}
              variant="outlined"
              onInput={(e) => this.setState({ email: e.target.value })}
            />
          </Grid>
          <Grid item md={6} xs={12}>
            <TextField
              fullWidth
              label="Organization"
              name="organization"
              // required
              defaultValue={organizationValue}
              variant="outlined"
              // onChange={(e) => this.onHandleChange(e)}
              onInput={(e) => this.setState({ organization: e.target.value })}
            />
          </Grid>
          <Grid item md={6} xs={12}>
            <TextField
              fullWidth
              label="Country"
              name="country"
              // required
              defaultValue={countryValue}
              variant="outlined"
              // onChange={(e) => this.onHandleChange(e)}
              onInput={(e) => this.setState({ country: e.target.value })}
            />
          </Grid>
        </Grid>
      );
    }

    if (!this.props.loading_profile) {
      const profile_table_columns = [
        {
          name: "species_id",
          label: "Species ID",
          options: {
            filter: true,
            sort: true,
            display: true,
            setCellHeaderProps: (value) => {
              return {
                style: {
                  fontWeight: "bold",
                },
              };
            },
          },
        },
        {
          name: "schema_id",
          label: "Schema ID",
          options: {
            filter: true,
            sort: true,
            display: true,
            setCellHeaderProps: (value) => {
              return {
                style: {
                  fontWeight: "bold",
                },
              };
            },
          },
        },
        {
          name: "nr_loci",
          label: "Loci Added",
          options: {
            filter: true,
            sort: true,
            display: true,
            setCellHeaderProps: (value) => {
              return {
                style: {
                  fontWeight: "bold",
                },
              };
            },
          },
        },
        {
          name: "nr_allele",
          label: "Alleles Added",
          options: {
            filter: true,
            sort: true,
            display: true,
            setCellHeaderProps: (value) => {
              return {
                style: {
                  fontWeight: "bold",
                },
              };
            },
          },
        },
      ];

      const profile_table_options = {
        textLabels: {
          body: {
            noMatch: <CircularProgress />,
          },
        },
        responsive: "scrollMaxHeight",
        selectableRowsHeader: false,
        selectableRows: "none",
        print: false,
        viewColumns: false,
        pagination: false,
        download: false,
        filter: false,
        search: false,
      };

      profile_table = (
        <MuiThemeProvider theme={this.getMuiTheme()}>
          <MUIDataTable
            title={"Contributions"}
            data={this.props.cuser_profile}
            columns={profile_table_columns}
            options={profile_table_options}
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
                  className={styles.root}
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
        <div style={{ marginTop: "40px" }}>{profile_table}</div>
      </Aux>
    );
  }
}

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

const mapDispatchToProps = (dispatch) => {
  return {
    onToken: (token) => dispatch(actions.authCuser(token)),
    onProfileTable: (token) => dispatch(actions.fetchProfile(token)),
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withStyles(styles)(ProfileDetails));
