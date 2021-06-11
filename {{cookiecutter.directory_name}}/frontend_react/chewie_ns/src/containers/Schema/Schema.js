import React, { Component } from "react";
import { Link } from "react-router-dom";
import { connect } from "react-redux";

// Chewie local imports
import Aux from "../../hoc/Aux/Aux";
import axios from "../../axios-backend";
import classes from "./Schema.module.css";
import Markdown from "../../components/Markdown/Markdown";
import Copyright from "../../components/Copyright/Copyright";
import classNames from "classnames";
import * as actions from "../../store/actions/index";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";
import {
  SPECIES_COLUMNS,
  SCHEMA_SPECIES_OPTIONS,
} from "../../components/data/table_columns/species_columns";
import {
  ANNOTATIONS_COLUMNS,
  ANNOTATIONS_COLUMNS2,
  ANNOTATIONS_OPTIONS,
} from "../../components/data/table_columns/schema_columns";

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

    // fetch schema boxplot data
    this.props.onFetchBoxplotData(species_id, schema_id);

    // fetch allele contributions
    this.props.onFetchAlleleContribution(species_id, schema_id);
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

  clickBoxPlotHandler = (event) => {
    const schema_id = this.props.match.params.schema_id;

    const locus_id = parseInt(event.points[0].x.split("-")[1]);

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
    let schema_boxplot = <CircularProgress />;
    let schema_contribData = <CircularProgress />;

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

    if (!this.props.loading_boxplot) {
      let boxplot_data = this.props.boxplotData;

      schema_boxplot = (
        <Plot
          data={boxplot_data}
          layout={{
            title: {
              text: "Locus Size Variation",
            },
            xaxis: {
              title: { text: "Loci" },
              showticklabels: false,
            },
            yaxis: {
              title: { text: "Allele size variation" },
            },
            boxgap: 0.05,
            boxgapgroup: 0.05,
          }}
          useResizeHandler={true}
          style={{ width: "100%", height: "100%" }}
          onClick={(e) => this.clickBoxPlotHandler(e)}
        />
      );
    }

    if (!this.props.loading_contribData) {
      let contribData = this.props.contribData;

      schema_contribData =
        this.props.contribData === "undefined" ? (
          <div>
            <Typography variant="subtitle1">
              No new alleles added to the schema.
            </Typography>
          </div>
        ) : (
          <Plot
            data={contribData}
            layout={{
              title: {
                text: "Allele Timeline Information",
              },
              xaxis: {
                type: "date",
                title: "Sync Dates",
                autorange: true,
                tickformat: "%-Y/%-m/%d",
                // tickmode: "linear",
                // tick0: "2021-03-01",
                // dtick: 86400000.0,
                // range: ['2015-01-01', '2015-12-31'],
                rangeselector: {
                  buttons: [
                    {
                      count: 1,
                      label: "1m",
                      step: "month",
                      stepmode: "backward",
                    },
                    {
                      count: 6,
                      label: "6m",
                      step: "month",
                      stepmode: "backward",
                    },
                    {
                      count: 1,
                      label: "1y",
                      step: "year",
                      stepmode: "backward",
                    },
                    { step: "all" },
                  ],
                },
                rangeslider: {},
                // autorange: true,
              },
              yaxis: {
                autorange: true,
                title: { text: "Alleles Added" },
              },
              hovermode: "closest",
            }}
            useResizeHandler={true}
            style={{ width: "100%", height: "100%" }}
          />
        );
    }

    if (this.props.annotations !== undefined || this.props.annotations !== []) {
      const columns = [
        ...ANNOTATIONS_COLUMNS,
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
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {value}
                </a>
              );
            },
          },
        },
        ...ANNOTATIONS_COLUMNS2,
      ];

      annotations = (
        <MuiThemeProvider theme={this.getMuiTheme()}>
          <MUIDataTable
            title={"Locus information"}
            data={this.props.annotations}
            columns={columns}
            options={ANNOTATIONS_OPTIONS}
          />
        </MuiThemeProvider>
      );
    }

    schema_table = (
      <MuiThemeProvider theme={this.getMuiTheme()}>
        <MUIDataTable
          title={`${spd[this.props.match.params.species_id]} ${
            tableData[0].schema_name
          } Overview`}
          data={tableData}
          columns={SPECIES_COLUMNS}
          options={SCHEMA_SPECIES_OPTIONS}
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
      <Aux>
        <div id="schemasAvailable" style={{ float: "right" }}>
          <Button
            variant="contained"
            color="default"
            component={Link}
            to="/stats"
          >
            Back to Available Schemas
          </Button>
        </div>
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
                      <Button
                        style={style.button}
                        className={classNames(
                          this.state.tabValue === 3 && classes.tabButton
                        )}
                        onClick={() => {
                          this.plotChangeHandler(3);
                        }}
                      >
                        Locus Size Variation
                      </Button>
                      <Button
                        style={style.button}
                        className={classNames(
                          this.state.tabValue === 4 && classes.tabButton
                        )}
                        onClick={() => {
                          this.plotChangeHandler(4);
                        }}
                      >
                        Allele Timeline Information
                      </Button>
                    </div>
                    {this.state.tabValue === 0 && total_allele_plot}
                    {this.state.tabValue === 1 && mode_plot}
                    {this.state.tabValue === 2 && scatter_plot}
                    {this.state.tabValue === 3 && schema_boxplot}
                    {this.state.tabValue === 4 && schema_contribData}
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
      </Aux>
    );
  }
}

// Redux functions

// Map state from the central warehouse
// to the props of this component
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
    boxplotData: state.schemaBox.boxplotData,
    loading_boxplot: state.schemaBox.loading,
    error_boxplot: state.schemaBox.error,
    contribData: state.contributions.contribData,
    loading_contribData: state.contributions.loading,
    error_contribData: state.contributions.error,
    // token: state.auth.token
  };
};

// Map dispatch functions that trigger
// actions from redux
// to the props of this component
const mapDispatchToProps = (dispatch) => {
  return {
    onFetchSchemaAlleleMode: (species_id, schema_id) =>
      dispatch(actions.fetchSchemaAlleleMode(species_id, schema_id)),
    onFetchAnnotations: (species_id, schema_id) =>
      dispatch(actions.fetchAnnotations(species_id, schema_id)),
    onFetchDescriptions: (species_id, schema_id) =>
      dispatch(actions.fetchDescriptions(species_id, schema_id)),
    onFetchBoxplotData: (species_id, schema_id) =>
      dispatch(actions.fetchSchemaBox(species_id, schema_id)),
    onFetchAlleleContribution: (species_id, schema_id) =>
      dispatch(actions.fetchAlleleContribution(species_id, schema_id)),
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withErrorHandler(Schema, axios));
