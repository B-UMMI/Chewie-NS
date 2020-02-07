import React, { Component } from "react";
import { connect } from "react-redux";

import axios from "../../axios-backend";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";
import Aux from "../../hoc/Aux/Aux"
import * as actions from "../../store/actions/index";
// import Spinner from "../../components/UI/Spinner/Spinner";

// Material-UI components
import CircularProgress from "@material-ui/core/CircularProgress";
import Typography from "@material-ui/core/Typography";
import Box from "@material-ui/core/Box";
import { createMuiTheme, MuiThemeProvider } from "@material-ui/core/styles";

// Material-UI Datatables
import MUIDataTable from "mui-datatables";

class Stats extends Component {
  componentDidMount() {
    // console.log("[this.props Stats]")
    // console.log(this.props)
    // this.props.onFetchStats();
    this.props.onFetchSpeciesStats();
  }

  rowClickHandler = species_id => {
    console.log("[RowClick]");
    console.log("species_id: ", species_id);
    // console.log(this.props.match);
    this.props.history.push("/species/" + species_id);
  };

  getMuiTheme = () =>
    createMuiTheme({
      overrides: {
        MuiTableRow: {
          root: {
            cursor: "pointer"
          }
        },
        MUIDataTableToolbar: {
          titleText: {
            color: "#bb7944"
          }
        }
      }
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
            setCellHeaderProps: value => {
              return {
                style: {
                  fontWeight: "bold"
                }
              };
            },
            customBodyRender: (value, tableMeta, updateValue) => (
              <Aux>
                <Typography component="div">
                  <Box
                    display="inline"
                    fontStyle="italic"
                    m={1}
                  >
                    {value}
                  </Box>
                </Typography>
              </Aux>
            )
          }
        },
        {
          name: "nr_schemas",
          label: "Schemas available",
          options: {
            filter: true,
            setCellHeaderProps: value => {
              return {
                style: {
                  fontWeight: "bold"
                }
              };
            }
          }
        },
        {
          name: "species_id",
          label: "Species ID",
          options: {
            filter: false,
            sort: true,
            display: false,
            setCellHeaderProps: value => {
              return {
                style: {
                  fontWeight: "bold"
                }
              };
            }
          }
        }
      ];

      const options = {
        textLabels: {
          body: {
            noMatch: <CircularProgress />
          }
        },
        responsive: "scrollMaxHeight",
        selectableRowsHeader: false,
        selectableRows: "none",
        selectableRowsOnClick: false,
        print: false,
        viewColumns: false,
        onRowClick: rowData => this.rowClickHandler(rowData[rowData.length - 1])
      };

      stats = (
        <MuiThemeProvider theme={this.getMuiTheme()}>
          <MUIDataTable
            title={"Overview"}
            data={this.props.stats}
            columns={columns}
            options={options}
          />
        </MuiThemeProvider>
      );
    }
    return (
      <div>
        <div>{stats}</div>
      </div>
    );
  }
}

const mapStateToProps = state => {
  return {
    stats: state.stats.stats,
    loading: state.stats.loading,
    error: state.stats.error
  };
};

const mapDispatchToProps = dispatch => {
  return {
    onFetchStats: () => dispatch(actions.fetchStats()),
    onFetchSpeciesStats: () => dispatch(actions.fetchStatsSpecies())
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withErrorHandler(Stats, axios));
