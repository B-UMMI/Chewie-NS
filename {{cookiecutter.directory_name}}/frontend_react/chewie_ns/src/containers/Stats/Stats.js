import React, { Component } from "react";
import { connect } from "react-redux";

// Chewie local imports
import axios from "../../axios-backend";
import Copyright from "../../components/Copyright/Copyright";
import * as actions from "../../store/actions/index";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";
import {
  STATS_COLUMNS,
  STATS_OPTIONS,
} from "../../components/data/table_columns/stats_columns";

// Material-UI components
import CircularProgress from "@material-ui/core/CircularProgress";
import { createMuiTheme, MuiThemeProvider } from "@material-ui/core/styles";

// Material-UI Datatables
import MUIDataTable from "mui-datatables";

class Stats extends Component {
  componentDidMount() {
    this.props.onFetchSpeciesStats();
  }

  rowClickHandler = (species_id) => {
    this.props.history.push({
      pathname: "/species/" + species_id[2],
    });
  };

  getMuiTheme = () =>
    createMuiTheme({
      overrides: {
        MuiTableRow: {
          root: {
            cursor: "pointer",
          },
        },
        MUIDataTableHeadCell: {
          fixedHeaderCommon: {
            backgroundColor: "#ccc",
          },
        },
      },
    });

  render() {
    let stats = <CircularProgress />;

    if (!this.props.loading) {
      stats = (
        <MuiThemeProvider theme={this.getMuiTheme()}>
          <MUIDataTable
            data={this.props.stats}
            columns={STATS_COLUMNS}
            options={STATS_OPTIONS}
          />
        </MuiThemeProvider>
      );
    }

    return (
      <div style={{ marginLeft: "5%", marginRight: "5%" }}>
        <div>
          <h1 style={{ textAlign: "center" }}>Overview</h1>
        </div>
        <div>{stats}</div>
        <Copyright />
      </div>
    );
  }
}

// Redux functions

// Map state from the central warehouse
// to the props of this component
const mapStateToProps = (state) => {
  return {
    stats: state.stats.stats,
    loading: state.stats.loading,
    error: state.stats.error,
  };
};

// Map dispatch functions that trigger
// actions from redux 
// to the props of this component
const mapDispatchToProps = (dispatch) => {
  return {
    onFetchStats: () => dispatch(actions.fetchStats()),
    onFetchSpeciesStats: () => dispatch(actions.fetchStatsSpecies()),
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withErrorHandler(Stats, axios));
