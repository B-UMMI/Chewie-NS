import React, { Component } from "react";
import { connect } from "react-redux";

import axios from "../../axios-backend";
import classes from "./Schema.module.css";
import Copyright from "../../components/Copyright/Copyright";
import classNames from "classnames";
import * as actions from "../../store/actions/index";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";

// Chewie Markdown component
import Markdown from "../../components/Markdown/Markdown";

// Material-UI components
import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
import CircularProgress from "@material-ui/core/CircularProgress";
import { createMuiTheme, MuiThemeProvider } from "@material-ui/core/styles";

// Material-UI ExpansionPanel components
import ExpansionPanel from "@material-ui/core/ExpansionPanel";
import ExpandMoreIcon from "@material-ui/icons/ExpandMore";
import ExpansionPanelSummary from "@material-ui/core/ExpansionPanelSummary";
import ExpansionPanelDetails from "@material-ui/core/ExpansionPanelDetails";

// Material-UI Datatables
import MUIDataTable from "mui-datatables";

// Plotly.js
import Plot from "react-plotly.js";

class Schema extends Component {
  state = {
    tabValue: 0,
    hits: [],
  };

  componentDidMount() {
    const species_id = this.props.match.params.species_id;
    const schema_id = this.props.match.params.schema_id;

    // fetch schema allele modes
    this.props.onFetchSchemaAlleleMode(species_id, schema_id);

    // fetch schema annotations
    this.props.onFetchAnnotations(species_id, schema_id);

    // fetch schema description
    this.props.onFetchDescriptions(species_id, schema_id);
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

  plotChangeHandler = (value) => {
    this.setState({ tabValue: value });
  };

  clickScatterPlotHandler = (event) => {
    const schema_id = this.props.match.params.schema_id;

    const locus_id = event.points[0].text;

    this.props.history.push(schema_id + "/locus/" + locus_id);
  };

  render() {
    const style = {
      buttonBar: {
        overflowX: "auto",
        display: "flex",
        justifyContent: "center",
        marginBottom: "20px",
      },
      button: {
        minWidth: "150px",
      },
    };

    let mode_plot = <CircularProgress />;
    let total_allele_plot = <CircularProgress />;
    let scatter_plot = <CircularProgress />;
    let annotations = <CircularProgress />;
    let schema_table = <CircularProgress />;
    let schema_description = <div />;

    const spd = JSON.parse(localStorage.getItem("speciesD"));
    const tableData = JSON.parse(localStorage.getItem("tableData"));

    if (!this.props.loading) {
      let mode_plot_data =
        typeof this.props.mode_data === "undefined" ||
        this.props.mode_data === []
          ? this.state.hits[0]
          : this.props.mode_data;

      mode_plot = (
        <Plot
          data={mode_plot_data}
          layout={{
            title: {
              text: "Distribution of allele mode sizes",
            },
            xaxis: {
              title: { text: "Allele Mode Size" },
              showgrid: true,
            },
            yaxis: {
              title: { text: "Number of Loci" },
            },
          }}
          useResizeHandler={true}
          style={{ width: "100%", height: "100%" }}
          line={{
            width: 1,
          }}
        />
      );

      let total_allele_plot_data =
        typeof this.props.total_allele_data === "undefined" ||
        this.props.total_allele_data === []
          ? this.state.hits[1]
          : this.props.total_allele_data;

      total_allele_plot = (
        <Plot
          data={total_allele_plot_data}
          layout={{
            title: {
              text: "Number of Loci with given Number of Alleles",
            },
            xaxis: {
              title: { text: "Number of Different Alleles" },
              showgrid: true,
            },
            yaxis: {
              title: { text: "Number of Loci" },
            },
          }}
          useResizeHandler={true}
          style={{ width: "100%", height: "100%" }}
          line={{
            width: 1,
          }}
        />
      );

      let scatter_plot_data =
        typeof this.props.scatter_data === "undefined" ||
        this.props.scatter_data === []
          ? this.state.hits[2]
          : this.props.scatter_data;

      scatter_plot = (
        <Plot
          data={scatter_plot_data}
          layout={{
            title: {
              text: "Locus Statistics",
            },
            xaxis: {
              title: { text: "Allele size in bp" },
              showgrid: true,
              zeroline: false,
            },
            yaxis: {
              title: { text: "Number of alleles" },
              zeroline: false,
            },
            hovermode: "closest",
          }}
          useResizeHandler={true}
          style={{ width: "100%", height: "100%" }}
          line={{
            width: 1,
          }}
          onClick={(e) => this.clickScatterPlotHandler(e)}
        />
      );
    }

    if (this.props.annotations !== undefined || this.props.annotations !== []) {
      const columns = [
        {
          name: "uniprot_label",
          label: "Uniprot Label",
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
          name: "uniprot_uri",
          label: "Uniprot URI",
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
              let link = value;

              if (link === "N/A") {
                return <div>{link}</div>;
              } else {
                return (
                  <a href={link} target="_blank" rel="noopener noreferrer">
                    {link}
                  </a>
                );
              }
            },
          },
        },
        {
          name: "user_annotation",
          label: "User Annotation",
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
          name: "custom_annotation",
          label: "Custom Annotation",
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
          name: "locus",
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
              return (
                <a
                  href={`${this.props.history.location.pathname}/locus/${value}`}
                >
                  {value}
                </a>
              );
            },
          },
        },
        {
          name: "locus_name",
          label: "Locus Label",
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
          name: "nr_alleles",
          label: "Total Number of Alleles",
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
          name: "alleles_mode",
          label: "Alleles Mode",
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
        download: true,
        filter: true,
        filterType: "multiselect",
        search: true,
        viewColumns: true,
        pagination: true,
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
    }

    const columns2 = [
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
        name: "schema_name",
        label: "Schema Name",
        options: {
          filter: true,
          sort: false,
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
        name: "user",
        label: "Created by user",
        options: {
          filter: false,
          sort: true,
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
        label: "Loci",
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
      {
        name: "nr_allele",
        label: "Alleles",
        options: {
          filter: false,
          sort: true,
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
        name: "chewie",
        label: "chewBBACA version",
        options: {
          filter: false,
          sort: false,
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
        name: "dateEntered",
        label: "Creation Date",
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
      {
        name: "lastModified",
        label: "Last Change Date",
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
      {
        name: "bsr",
        label: "Blast Score Ratio",
        options: {
          filter: false,
          sort: true,
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
        name: "ptf",
        label: "Prodigal Training File",
        options: {
          filter: false,
          sort: true,
          display: false,
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
        name: "tl_table",
        label: "Translation Table",
        options: {
          filter: false,
          sort: true,
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
        name: "minLen",
        label: "Minimum Length (bp)",
        options: {
          filter: false,
          sort: true,
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

    const options2 = {
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

    schema_table = (
      <MuiThemeProvider theme={this.getMuiTheme()}>
        <MUIDataTable
          title={`${spd[this.props.match.params.species_id]} ${
            tableData[0].schema_name
          } Overview`}
          data={tableData}
          columns={columns2}
          options={options2}
        />
      </MuiThemeProvider>
    );

    schema_description = (
      <div>
        <div style={{ marginTop: "40px" }}>
          <ExpansionPanel defaultExpanded>
            <ExpansionPanelSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h5" className={classes.title}>
                Schema Description
              </Typography>
            </ExpansionPanelSummary>
            <ExpansionPanelDetails>
              <div
                className={classes.mainPaper}
                style={{ width: "100%", height: "100%" }}
              >
                <Markdown markdown={this.props.descriptions} />
              </div>
            </ExpansionPanelDetails>
          </ExpansionPanel>
        </div>
      </div>
    );

    return (
      <div style={{ marginLeft: "5%", marginRight: "5%" }}>
        <div>
          <h1 style={{ textAlign: "center" }}>
            Schema Evaluation and Annotation
          </h1>
        </div>
        <div style={{ marginTop: "40px" }}>{schema_table}</div>
        <div>{schema_description}</div>
        <div>
          <div style={{ marginTop: "40px" }}>
            <ExpansionPanel defaultExpanded>
              <ExpansionPanelSummary expandIcon={<ExpandMoreIcon />}>
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
          <div style={{ marginTop: "40px", marginBottom: "40px" }}>
            {annotations}
          </div>
        </div>
        <Copyright />
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    mode_data: state.schema.mode_data,
    total_allele_data: state.schema.total_allele_data,
    scatter_data: state.schema.scatter_data,
    mode_data2: state.schema.mode_data2,
    loading: state.schema.loading,
    error: state.schema.error,
    annotations: state.annotations.annotations,
    loading_annotations: state.annotations.loading,
    error_annotations: state.annotations.error,
    descriptions: state.descriptions.descriptions,
    loading_descriptions: state.descriptions.loading,
    error_descriptions: state.descriptions.error,
    species: state.species.species,
    // token: state.auth.token
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    onFetchSchemaAlleleMode: (species_id, schema_id) =>
      dispatch(actions.fetchSchemaAlleleMode(species_id, schema_id)),
    onFetchAnnotations: (species_id, schema_id) =>
      dispatch(actions.fetchAnnotations(species_id, schema_id)),
    onFetchDescriptions: (species_id, schema_id) =>
      dispatch(actions.fetchDescriptions(species_id, schema_id)),
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withErrorHandler(Schema, axios));
