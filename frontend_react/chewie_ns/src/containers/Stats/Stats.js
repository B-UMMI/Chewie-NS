import React, { Component } from "react";
import { connect } from "react-redux";
import { Link as RouterLink } from "react-router-dom";

import Aux from "../../hoc/Aux/Aux";
import axios from "../../axios-backend";
import Copyright from "../../components/Copyright/Copyright";
import * as actions from "../../store/actions/index";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";

// Material-UI components
import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
import CircularProgress from "@material-ui/core/CircularProgress";
import { createMuiTheme, MuiThemeProvider } from "@material-ui/core/styles";

// Material-UI Datatables
import MUIDataTable from "mui-datatables";

class Stats extends Component {
  componentDidMount() {
    this.props.onFetchSpeciesStats();
  }

  rowClickHandler = (species_id) => {
    console.log("[RowClick]");

    console.log(species_id);

    console.log(species_id[0].props.children.props.children);

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
      const columns = [
        {
          name: "species_name",
          label: "Species",
          options: {
            filter: true,
            setCellHeaderProps: (value) => {
              return {
                style: {
                  fontWeight: "bold",
                },
              };
            },
            customBodyRender: (value, tableMeta, updateValue) => (
              <Aux>
                <i>{value}</i>
              </Aux>
            ),
          },
        },
        {
          name: "nr_schemas",
          label: "Schemas available",
          options: {
            filter: true,
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
          name: "Schema Details",
          options: {
            filter: false,
            empty: true,
            setCellHeaderProps: (value) => {
              return {
                style: {
                  fontWeight: "bold",
                },
              };
            },
            customBodyRender: (value, tableMeta, updateValue) => {
              return (
                <Button
                  variant="contained"
                  color="default"
                  component={RouterLink}
                  to={"/species/" + tableMeta.rowData[3]}
                  onClick={() => console.log(tableMeta.rowData[3])}
                >
                  Schema Details
                </Button>
              );
            },
          },
        },
        {
          name: "species_id",
          label: "Species ID",
          options: {
            filter: false,
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

      const options = {
        textLabels: {
          body: {
            noMatch: <CircularProgress />,
          },
        },
        responsive: "scrollMaxHeight",
        selectableRowsHeader: false,
        selectableRows: "none",
        selectableRowsOnClick: false,
        print: false,
        download: false,
        search: false,
        filter: false,
        viewColumns: false,
      };

      stats = (
        <MuiThemeProvider theme={this.getMuiTheme()}>
          <MUIDataTable
            data={this.props.stats}
            columns={columns}
            options={options}
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

const mapStateToProps = (state) => {
  return {
    stats: state.stats.stats,
    loading: state.stats.loading,
    error: state.stats.error,
  };
};

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
