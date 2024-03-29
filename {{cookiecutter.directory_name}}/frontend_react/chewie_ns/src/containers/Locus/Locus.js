import React, { Component } from "react";
import { Link } from "react-router-dom";
import { connect } from "react-redux";

// Chewie local imports
import Aux from "../../hoc/Aux/Aux";
import axios from "../../axios-backend";
import classes from "./Locus.module.css";
import Copyright from "../../components/Copyright/Copyright";
import classNames from "classnames";
import AlertSnackbar from "../../components/AlertSnackbar/AlertSnackbar";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";
import * as actions from "../../store/actions/index";
import {
  LOCUS_COLUMNS,
  LOCUS_OPTIONS,
} from "../../components/data/table_columns/loci_columns";

// Import Icons from Material UI and Material Design
import SvgIcon from "@material-ui/core/SvgIcon";
import { mdiOpenInNew } from "@mdi/js";

// Material-UI components
import Box from "@material-ui/core/Box";
import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
import CircularProgress from "@material-ui/core/CircularProgress";
import GetAppSharpIcon from "@material-ui/icons/GetAppSharp";

// Material-UI ExpansionPanel related components
import ExpansionPanel from "@material-ui/core/ExpansionPanel";
import ExpandMoreIcon from "@material-ui/icons/ExpandMore";
import ExpansionPanelSummary from "@material-ui/core/ExpansionPanelSummary";
import ExpansionPanelDetails from "@material-ui/core/ExpansionPanelDetails";

// Material-UI Datatables
import MUIDataTable from "mui-datatables";

// Plotly.js
import Plot from "react-plotly.js";

// Download function
import { saveAs } from "file-saver";

class Locus extends Component {
  state = {
    tabValue: 0,
    showSnack: false,
  };

  componentDidMount() {
    const species_id = this.props.location.pathname.split("/")[2];

    const schema_id = this.props.location.pathname.split("/")[4];

    const locusId = this.props.location.pathname.substring(
      this.props.location.pathname.lastIndexOf("/") + 1
    );

    this.props.onFetchLocusFasta(locusId);
    this.props.onFetchLocusUniprot(locusId);
    this.props.onFetchLocusAlleleContribution(species_id, schema_id, locusId);
  }

  downloadFastaHandler = () => {
    const fastaJoin = this.props.fasta_data.join("\n");

    const blob = new Blob([fastaJoin], { type: "text/plain;charset=utf-8" });

    const locusIdDown = this.props.location.pathname.substring(
      this.props.location.pathname.lastIndexOf("/") + 1
    );

    console.log(locusIdDown);

    saveAs(blob, "locus_" + locusIdDown + ".fasta");
  };

  openBlastxPageHandler = () => {
    const queryToCheck = this.props.blastxQuery;

    // If query is too long show warning.
    // Else open the page.
    if (queryToCheck.length > 8000) {
      this.setState({ showSnack: true });
    } else {
      const anchor = document.createElement("a");
      anchor.href = queryToCheck;
      anchor.target = "_blank";
      anchor.rel = "noopener noreferrer";
      anchor.click();
    }
  };

  openBlastnPageHandler = () => {
    const queryToCheck = this.props.blastnQuery;

    // If query is too long show warning.
    // Else open the page.
    if (queryToCheck.length > 8000) {
      this.setState({ showSnack: true });
    } else {
      const anchor = document.createElement("a");
      anchor.href = queryToCheck;
      anchor.target = "_blank";
      anchor.rel = "noopener noreferrer";
      anchor.click();
    }
  };

  plotChangeHandler = (value) => {
    this.setState({ tabValue: value });
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

    let uniprot_data = <CircularProgress />;
    let fasta_data = <CircularProgress />;
    let scatter_data = <CircularProgress />;
    let locus_contribData = <CircularProgress />;

    let downloadFasta = (
      <Button
        variant="contained"
        color="default"
        startIcon={<GetAppSharpIcon />}
        onClick={() => this.downloadFastaHandler()}
      >
        Download FASTA
      </Button>
    );

    let blastx = (
      <Button
        variant="contained"
        color="default"
        startIcon={
          <SvgIcon fontSize="small">
            <path d={mdiOpenInNew} />
          </SvgIcon>
        }
        onClick={this.openBlastxPageHandler}
      >
        BLASTx
      </Button>
    );

    let blastn = (
      <Button
        variant="contained"
        color="default"
        startIcon={
          <SvgIcon fontSize="small">
            <path d={mdiOpenInNew} />
          </SvgIcon>
        }
        onClick={this.openBlastnPageHandler}
      >
        BLASTn
      </Button>
    );

    if (!this.props.loading) {
      let table_data = [
        { ...this.props.locus_uniprot[0], ...this.props.basic_stats[0] },
      ];

      uniprot_data = (
        <MUIDataTable
          title={"Locus Details"}
          data={table_data}
          columns={LOCUS_COLUMNS}
          options={LOCUS_OPTIONS}
        />
      );

      fasta_data = (
        <Plot
          data={this.props.locus_fasta}
          layout={{
            title: {
              text: table_data[0].locus_label,
            },
            xaxis: {
              title: { text: "Sequence size in bp" },
            },
            yaxis: {
              title: { text: "Number of Alleles" },
            },
          }}
          useResizeHandler={true}
          style={{ width: "100%", height: "100%" }}
          line={{
            width: 1,
          }}
        />
      );

      scatter_data = (
        <Plot
          data={this.props.scatter_data}
          layout={{
            title: {
              text: table_data[0].locus_label,
            },
            xaxis: {
              title: { text: "Allele ID", tick0: 0, dtick: 1 },
            },
            yaxis: {
              title: { text: "Sequence size in bp", tick0: 0, dtick: 1 },
            },
            hovermode: "closest",
          }}
          useResizeHandler={true}
          style={{ width: "100%", height: "100%" }}
          line={{
            width: 1,
          }}
        />
      );
    }

    if (!this.props.loading_contribData) {
      let contribData = this.props.contribData;

      locus_contribData =
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
                tickformat: "%-Y/%-m/%d",
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
                title: { text: "Alleles Added" },
              },
              hovermode: "closest",
            }}
            useResizeHandler={true}
            style={{ width: "100%", height: "100%" }}
          />
        );
    }

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
        <div
          style={{
            marginLeft: "5%",
            marginRight: "5%",
            marginBottom: "2%",
            marginTop: "3%",
          }}
        >
          <div>
            <ExpansionPanel defaultExpanded>
              <ExpansionPanelSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h5" className={classes.title}>
                  Locus Details
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
                      Histogram
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
                      Scatter
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
                      Allele Timeline
                    </Button>
                  </div>
                  {this.state.tabValue === 0 && fasta_data}
                  {this.state.tabValue === 1 && scatter_data}
                  {this.state.tabValue === 2 && locus_contribData}
                </div>
              </ExpansionPanelDetails>
            </ExpansionPanel>
          </div>

          <div style={{ marginTop: "40px" }}>{uniprot_data}</div>

          <Box
            style={{
              height: 80,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            {downloadFasta}
            {blastx}
            {blastn}
          </Box>

          <div>{this.state.showSnack ? <AlertSnackbar /> : null}</div>

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
    locus_fasta: state.locus.locus_fasta,
    locus_uniprot: state.locus.locus_uniprot,
    fasta_data: state.locus.fasta_data,
    blastxQuery: state.locus.blastxQuery,
    blastnQuery: state.locus.blastnQuery,
    scatter_data: state.locus.scatter_data,
    basic_stats: state.locus.basic_stats,
    loading: state.locus.loading,
    error: state.locus.error,
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
    onFetchLocusFasta: (locus_id) =>
      dispatch(actions.fetchLocusFasta(locus_id)),
    onFetchLocusUniprot: (locus_id) =>
      dispatch(actions.fetchLocusUniprot(locus_id)),
    onFetchLocusAlleleContribution: (species_id, schema_id, locus_id) =>
      dispatch(
        actions.fetchAlleleContributionLocus(species_id, schema_id, locus_id)
      ),
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withErrorHandler(Locus, axios));
