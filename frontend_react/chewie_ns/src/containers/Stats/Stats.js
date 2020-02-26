import React, { Component } from "react";
import { connect } from "react-redux";

import axios from "../../axios-backend";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";
import Aux from "../../hoc/Aux/Aux";
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

    console.log(species_id);

    console.log(species_id[0].props.children.props.children);

    // console.log("species_id: ", species_id);
    // console.log(this.props.match);
    this.props.history.push({
      pathname: "/species/" + species_id[2]
    });
  };

  getMuiTheme = () =>
    createMuiTheme({
      overrides: {
        MuiTableRow: {
          root: {
            cursor: "pointer"
          }
        },
        MUIDataTableHeadCell: {
          fixedHeaderCommon: {
            backgroundColor: "#ccc"
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
                {/* <Typography component="div">
                  <Box
                    display="inline"
                    fontStyle="italic"
                    color="#bb7944"
                    m={1}
                  >
                    {value}
                  </Box>
                </Typography> */}
                <i>{value}</i>
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
        download: false,
        search: false,
        filter: false,
        viewColumns: false,
        onRowClick: rowData => this.rowClickHandler(rowData)
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
        <div>
          <p>Lorem Ipsum</p>
        </div>
        <div>{stats}</div>
        <footer
          style={{
            position: "fixed",
            bottom: "0",
            left: "0",
            backgroundColor: "#ccc",
            width: "100%",
            textAlign: "center"
          }}
        >
          <div id="homeFooter" style={{ display: "block" }}>
            <div>
              <Typography style={{ fontSize: "10" }}>© UMMI 2020</Typography>
              {/* <p>© UMMI 2020</p> */}
            </div>
          </div>
        </footer>
      </div>
    );
  }
}

const mapStateToProps = state => {
  return {
    stats: state.stats.stats,
    speciesDict: state.stats.speciesDict,
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
