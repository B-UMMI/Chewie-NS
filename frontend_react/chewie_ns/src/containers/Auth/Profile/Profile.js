import React, { Component } from "react";
import axios from "../../../axios-backend";
import { connect } from "react-redux";
// import clsx from "clsx";

// Chewie local import
import * as actions from "../../../store/actions/index";

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

const styles = (theme) => ({
  root: {},
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
  }

  onSubmitHandler = (event) => {
    event.preventDefault();

    const token2 = localStorage.getItem("token");

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
          alert("You have updated your profile successfully");
          this.props.history.push({
            pathname: "/",
          });
        }
      })
      .catch((err) => {
        console.log(err);
      });
  };

  // onHandleChange = (event) => {
  //   this.settate = {
  //     ...this.state,
  //     [event.target.name]: event.target.value
  //   }

  render() {
    let profile = <CircularProgress />;
    let nameValue = "";
    let usernameValue = "";
    let emailValue = "";
    let organizationValue = "";
    let countryValue = "";

    if (!this.props.loading) {
      // console.log(this.props.cuser);
      const values = { ...this.props.cuser };
      // console.log(test['name']);
      // console.log(test.username);
      // console.log(test);
      nameValue = values.name;
      usernameValue = values.username;
      emailValue = values.email;
      organizationValue = values.organization;
      countryValue = values.country;

      profile = (
        <Card>
          <CardContent>
            <Box alignItems="center" display="flex" flexDirection="column">
              <Typography color="textPrimary" gutterBottom variant="h3">
                {`Name: ${nameValue}`}
              </Typography>
              <Typography color="textSecondary" variant="body1">
                {`Username: ${usernameValue}`}
              </Typography>
              <Typography color="textSecondary" variant="body1">
                {`Organization: ${organizationValue}`}
              </Typography>
              <Typography color="textSecondary" variant="body1">
                {`Country: ${countryValue}`}
              </Typography>
              <Typography color="textSecondary" variant="body1">
                {`Email: ${emailValue}`}
              </Typography>
            </Box>
          </CardContent>
        </Card>
      );
    }

    return (
      <div>
        <Container maxWidth="lg">
          <Grid container spacing={3}>
            <Grid item lg={4} md={6} xs={12}>
              {profile}
            </Grid>
            <Grid item lg={8} md={6} xs={12}>
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
                  <CardContent>
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
                          onInput={(e) =>
                            this.setState({ username: e.target.value })
                          }
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
                          onInput={(e) =>
                            this.setState({ name: e.target.value })
                          }
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
                          onInput={(e) =>
                            this.setState({ email: e.target.value })
                          }
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
                          onInput={(e) =>
                            this.setState({ organization: e.target.value })
                          }
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
                          onInput={(e) =>
                            this.setState({ country: e.target.value })
                          }
                        />
                      </Grid>
                    </Grid>
                  </CardContent>
                  <Divider />
                  <Box display="flex" justifyContent="flex-end" p={2}>
                    <Button color="primary" variant="contained" type="submit">
                      Save details
                    </Button>
                  </Box>
                </Card>
              </form>
            </Grid>
          </Grid>
        </Container>
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    loading: state.auth.loading,
    error: state.auth.error,
    cuser: state.auth.cuser,
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    onToken: (token) => dispatch(actions.authCuser(token)),
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withStyles(styles)(ProfileDetails));
