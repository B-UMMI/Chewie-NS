import React, { Component } from "react";
import { connect } from "react-redux";

// Chewie local imports
import * as actions from "../../store/actions/index";
import {
  SEQUENCES_COLUMNS,
  SEQUENCES_OPTIONS,
  SEQUENCES_STYLES,
} from "../../components/data/table_columns/sequences_columns";
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

      sequenceTable = (
        <MuiThemeProvider theme={this.getMuiTheme()}>
          <MUIDataTable
            title={"Results"}
            data={seqData}
            columns={SEQUENCES_COLUMNS}
            options={SEQUENCES_OPTIONS}
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
                    label="Alelle Sequence or Hash"
                    placeholder="DNA Sequence or Hash"
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
)(withStyles(SEQUENCES_STYLES)(Sequences));
