import React, { Component } from "react";
import { connect } from "react-redux";

import axios from "../../axios-backend";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";
import Aux from "../../hoc/Aux/Aux";
import * as actions from "../../store/actions/index";
import classes from "./Schema.module.css";

import classNames from "classnames";

// Material-UI components
import CircularProgress from "@material-ui/core/CircularProgress";

import ExpansionPanelSummary from "@material-ui/core/ExpansionPanelSummary";
import ExpansionPanelDetails from "@material-ui/core/ExpansionPanelDetails";
import ExpansionPanel from "@material-ui/core/ExpansionPanel";
// import ExpandMoreIcon from "@material-ui/icons/ExpandMore";

import Typography from "@material-ui/core/Typography";

import Button from "@material-ui/core/Button";

import Box from "@material-ui/core/Box";

import { createMuiTheme, MuiThemeProvider } from "@material-ui/core/styles";

// Material-UI Datatables
import MUIDataTable from "mui-datatables";

// Plotly.js
import Plot from "react-plotly.js";

class Schema extends Component {
  state = {
    tabValue: 0
  };

  componentDidMount() {
    // console.log(this.props.match);
    // console.log(this.props.location);
    console.log(this.props.history);
    // console.log(this.props.match.params.species_id)

    const species_id = this.props.match.params.species_id;
    const schema_id = this.props.match.params.schema_id;

    this.props.onFetchSchemaAlleleMode(species_id, schema_id);

    // fetch schema annotations
    this.props.onFetchAnnotations(species_id, schema_id);

  }

  getMuiTheme = () =>
    createMuiTheme({
      overrides: {
        MUIDataTableToolbar: {
          titleText: {
            color: "#bb7944"
          }
        }
      }
    });

  plotChangeHandler = value => {
    this.setState({ tabValue: value });
  };

  clickScatterPlotHandler = event => {
    // console.log(event.points[0]);

    // const species_id = this.props.match.params.species_id;

    const schema_id = this.props.match.params.schema_id;

    const locus_id = event.points[0].text;

    // console.log(species_id);
    // console.log(schema_id);
    // console.log(locus_id);

    this.props.history.push(schema_id + "/locus/" + locus_id);
  };

  render() {
    const style = {
      buttonBar: {
        overflowX: "auto",
        display: "flex",
        justifyContent: "center",
        marginBottom: "20px"
      },
      button: {
        minWidth: "150px"
      }
    };

    let mode_plot = <CircularProgress />;
    let total_allele_plot = <CircularProgress />;
    let scatter_plot = <CircularProgress />;
    let annotations = <CircularProgress />;

    if (!this.props.loading) {
      // console.log(this.props.mode_data)

      mode_plot = (
        <Plot
          data={this.props.mode_data}
          layout={{
            title: {
              text: "Distribution of allele mode sizes"
            },
            xaxis: {
              title: { text: "Allele Mode Size" },
              showgrid: true
            },
            yaxis: {
              title: { text: "Number of Loci" }
            }
          }}
          useResizeHandler={true}
          style={{ width: "100%", height: "100%" }}
          line={{
            width: 1
          }}
          //   onClick={e => this.clickPlotHandler(e)}
        />
      );

      total_allele_plot = (
        <Plot
          data={this.props.total_allele_data}
          layout={{
            title: {
              text: "Number of Loci with given Number of Alleles"
            },
            xaxis: {
              title: { text: "Number of Different Alleles" },
              showgrid: true
            },
            yaxis: {
              title: { text: "Number of Loci" }
            }
          }}
          useResizeHandler={true}
          style={{ width: "100%", height: "100%" }}
          line={{
            width: 1
          }}
          // onClick={e => console.log(e)}
        />
      );

      scatter_plot = (
        <Plot
          data={this.props.scatter_data}
          layout={{
            title: {
              text: "Locus Statistics"
            },
            xaxis: {
              title: { text: "Allele size in bp" },
              showgrid: true,
              zeroline: false
              // tick0: 1,
              // dtick: 1000
            },
            yaxis: {
              title: { text: "Number of alleles" },
              zeroline: false
              // tick0: 0
            },
            hovermode: "closest"
          }}
          useResizeHandler={true}
          style={{ width: "100%", height: "100%" }}
          line={{
            width: 1
          }}
          onClick={e => this.clickScatterPlotHandler(e)}
        />
      );
    }

    const columns = [
      {
        name: "uniprot_label",
        label: "Uniprot Label",
        options: {
          filter: true,
          sort: true,
          display: true,
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
        name: "uniprot_uri",
        label: "Uniprot URI",
        options: {
          filter: true,
          sort: true,
          display: true,
          setCellHeaderProps: value => {
            return {
              style: {
                fontWeight: "bold"
              }
            };
          },
          customBodyRender: (value, tableMeta, updateValue) => {
            return (
              <a href={value} target="_blank" rel="noopener noreferrer">
                {value}
              </a>
            );
          }
        }
      },
      {
        name: "species",
        label: "Species",
        options: {
          filter: true,
          sort: true,
          display: true,
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
                <Box display="inline" fontStyle="italic" m={1}>
                  {value}
                </Box>
              </Typography>
            </Aux>
          )
        }
      },
      {
        name: "locus",
        label: "Locus ID",
        options: {
          filter: true,
          sort: true,
          display: true,
          setCellHeaderProps: value => {
            return {
              style: {
                fontWeight: "bold"
              }
            };
          },
          customBodyRender: (value, tableMeta, updateValue) => {
            return (
              <a
                href={`${this.props.history.location.pathname}/locus/${value}`}
              >
                {value}
                {/* href={`/locus/${value}` */}
              </a>
            );
          }
        }
      },
      {
        name: "locus_name",
        label: "Locus Label",
        options: {
          filter: true,
          sort: true,
          display: true,
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
      download: true,
      filter: true,
      filterType: "multiselect",
      search: true,
      viewColumns: true,
      pagination: true
    };

    annotations = (
      <MuiThemeProvider theme={this.getMuiTheme()}>
        <MUIDataTable
          title={"Annotations"}
          data={this.props.annotations}
          columns={columns}
          options={options}
        />
      </MuiThemeProvider>
    );

    return (
      // <div>
      //   <div>{mode_plot}</div>
      //   <div>{total_allele_plot}</div>
      //   <div>{scatter_plot}</div>
      // </div>
      <div style={{ marginLeft: "5%", marginRight: "5%" }}>
        <div>
          <h1 style={{ textAlign: "center" }}>
            Schema Evaluation and Annotation
          </h1>
          <p style={{ textAlign: "center" }}>{this.props.speciesDict[this.props.match.params.species_id]}</p>
        </div>
        <div>
          <div>
            <ExpansionPanel defaultExpanded>
              <ExpansionPanelSummary>
                <Typography variant="h5" className={classes.title}>
                  Schema Evaluation
                </Typography>
              </ExpansionPanelSummary>
              <ExpansionPanelDetails>
                <div
                  className={classes.mainPaper}
                  style={{ width: "100%", height: "100%" }}
                >
                  <div style={style.buttonBar}>
                    <Button
                      style={style.button}
                      className={classNames(
                        this.state.tabValue === 0 && classes.tabButton
                      )}
                      onClick={() => {
                        this.plotChangeHandler(0);
                      }}
                    >
                      Allele Numbers Analysis
                    </Button>
                    <Button
                      style={style.button}
                      className={classNames(
                        this.state.tabValue === 1 && classes.tabButton
                      )}
                      onClick={() => {
                        this.plotChangeHandler(1);
                      }}
                    >
                      Allele Length Analysis
                    </Button>
                    <Button
                      style={style.button}
                      className={classNames(
                        this.state.tabValue === 2 && classes.tabButton
                      )}
                      onClick={() => {
                        this.plotChangeHandler(2);
                      }}
                    >
                      Locus Statistics
                    </Button>
                  </div>
                  {this.state.tabValue === 0 && total_allele_plot}
                  {this.state.tabValue === 1 && mode_plot}
                  {this.state.tabValue === 2 && scatter_plot}
                </div>
              </ExpansionPanelDetails>
            </ExpansionPanel>
          </div>
          <div style={{ marginBottom: "5%" }}>{annotations}</div>
        </div>
        {/* <div style={{marginBottom: "5%"}}>
          {annotations}
        </div> */}
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
    mode_data: state.schema.mode_data,
    total_allele_data: state.schema.total_allele_data,
    scatter_data: state.schema.scatter_data,
    loading: state.schema.loading,
    error: state.schema.error,
    annotations: state.annotations.annotations,
    loading_annotations: state.annotations.loading,
    error_annotations: state.annotations.error,
    speciesDict: state.stats.speciesDict
    // token: state.auth.token
  };
};

const mapDispatchToProps = dispatch => {
  return {
    onFetchSchemaAlleleMode: (species_id, schema_id) =>
      dispatch(actions.fetchSchemaAlleleMode(species_id, schema_id)),
    onFetchAnnotations: (species_id, schema_id) =>
      dispatch(actions.fetchAnnotations(species_id, schema_id))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withErrorHandler(Schema, axios));
