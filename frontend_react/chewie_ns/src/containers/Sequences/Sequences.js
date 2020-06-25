import React, { Component } from "react";
import { connect } from "react-redux";

import * as actions from "../../store/actions/index";
import Copyright from "../../components/Copyright/Copyright";

// Material UI component imports
import Button from "@material-ui/core/Button";
import TextField from "@material-ui/core/TextField";
import Container from "@material-ui/core/Container";
import CssBaseline from "@material-ui/core/CssBaseline";

// Material UI function imports
import { withStyles } from "@material-ui/core/styles";
import { createMuiTheme, MuiThemeProvider } from "@material-ui/core/styles";

// Material-UI Datatables
import MUIDataTable from "mui-datatables";

const styles = (theme) => ({
  root: {
    "& .MuiTextField-root": {
      margin: theme.spacing(1),
      width: "100ch",
    },
  },
  paper: {
    marginTop: theme.spacing(8),
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
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
});

class Sequences extends Component {
  state = {
    seq: "",
  };

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

    console.log(this.state.seq);

    this.props.onFetchSequence(this.state.seq);
  };

  onClickClear = () => {
    this.setState({
      seq: "",
    });
  };

  render() {
    const { classes } = this.props;

    let sequenceTable = <MUIDataTable />;

    let errorMessage = null;

    if (this.props.error) {
      errorMessage = <p>{this.props.error.message}</p>;
    }

    if (!this.props.loading) {
      let seqData = this.props.sequence_data;

      const columns = [
        {
          name: "schemas_url",
          label: "Schema",
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
            customBodyRender: (value, tableMeta, updateValue) => {
              let schema_id = value.substring(value.lastIndexOf("/") + 1);

              return (
                <a href={value} target={"_blank"} rel="noopener noreferrer">
                  {schema_id}
                </a>
              );
            },
          },
        },
        {
          name: "locus_url",
          label: "Locus ID",
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
            customBodyRender: (value, tableMeta, updateValue) => {
              let locus_id = value.substring(value.lastIndexOf("/") + 1);

              return (
                <a href={value} target={"_blank"} rel="noopener noreferrer">
                  {locus_id}
                </a>
              );
            },
          },
        },
      ];

      const options = {
        responsive: "scrollMaxHeight",
        selectableRowsHeader: false,
        selectableRows: "none",
        selectableRowsOnClick: false,
        print: false,
        download: false,
        filter: true,
        filterType: "multiselect",
        search: false,
        viewColumns: true,
        pagination: true,
      };

      sequenceTable = (
        <MuiThemeProvider theme={this.getMuiTheme()}>
          <MUIDataTable
            title={"Results"}
            data={seqData}
            columns={columns}
            options={options}
          />
        </MuiThemeProvider>
      );
    }

    return (
      <div id="homeDiv">
        <div id="titleDiv">
          <h1 style={{ textAlign: "center" }}>Allele Search</h1>
        </div>
        <div id="TextAreaDiv">
          <Container component="main" maxWidth="xs">
            <CssBaseline />
            <div className={classes.paper}>
              <form
                className={classes.root}
                onSubmit={(e) => this.onSubmitHandler(e)}
                noValidate
                autoComplete="off"
              >
                <div>
                  <TextField
                    id="outlined-textarea"
                    label="Alelle Sequence"
                    placeholder="DNA Sequence"
                    rows={4}
                    multiline
                    variant="outlined"
                    onInput={(e) => this.setState({ seq: e.target.value })}
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
                    SEARCH
                  </Button>
                </div>
              </form>
            </div>
          </Container>
        </div>
        <div>{errorMessage}</div>
        <div>{sequenceTable}</div>
        <Copyright />
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    loading: state.sequences.loading,
    error: state.sequences.error,
    sequence_data: state.sequences.sequence_data,
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    onFetchSequence: (sequence) => dispatch(actions.fetchSequence(sequence)),
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withStyles(styles)(Sequences));
