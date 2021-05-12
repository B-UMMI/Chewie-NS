import React, { Component } from "react";
import { connect } from "react-redux";
import { Link } from "react-router-dom";

// Chewie local imports
import Aux from "../../hoc/Aux/Aux";
import axios from "../../axios-backend";
import Copyright from "../../components/Copyright/Copyright";
import * as actions from "../../store/actions/index";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";
import {
  SPECIES_COLUMNS,
  SPECIES_OPTIONS,
} from "../../components/data/table_columns/species_columns";

// Material-UI components
import Button from "@material-ui/core/Button";
import GetAppSharpIcon from "@material-ui/icons/GetAppSharp";
import CircularProgress from "@material-ui/core/CircularProgress";
import { createMuiTheme, MuiThemeProvider } from "@material-ui/core/styles";

// Material-UI Datatables
import MUIDataTable from "mui-datatables";

// Plotly.js
import Plot from "react-plotly.js";

class Species extends Component {
  componentDidMount() {
    let species_url = this.props.location.pathname;

    let species_id = species_url.substring(species_url.lastIndexOf("/") + 1);

    // let species_id = species_url_array[species_url_array.length - 1];

    this.props.onFetchSpecies(species_id);
    this.props.onFetchSpeciesAnnot(species_id);
  }

  clickPlotHandler = (event) => {
    const schema_id = event.points[0].data.name.slice(-1);

    const locus_id = event.points[0].text;

    this.props.history.push({
      pathname:
        this.props.match.params.species_id +
        "/schemas/" +
        schema_id +
        "/locus/" +
        locus_id,
    });
  };

  rowClickHandler = (tableMeta) => {
    const schema_id = tableMeta.rowData[0];

    localStorage.setItem("schemaName", tableMeta.rowData[1]);

    const tableData = [];

    tableData.push({
      schema_id: tableMeta.rowData[0],
      schema_name: tableMeta.rowData[1],
      user: tableMeta.rowData[2],
      nr_loci: tableMeta.rowData[3],
      nr_allele: tableMeta.rowData[4],
      chewie: tableMeta.rowData[5],
      dateEntered: tableMeta.rowData[6],
      lastModified: tableMeta.rowData[7],
      bsr: tableMeta.rowData[8],
      ptf: tableMeta.rowData[9],
      tl_table: tableMeta.rowData[10],
      minLen: tableMeta.rowData[11],
      sizeThresh: tableMeta.rowData[12],
    });

    localStorage.setItem("tableData", JSON.stringify(tableData));

    this.props.history.push({
      pathname: `${this.props.match.params.species_id}/schemas/${schema_id}`,
    });
  };

  downloadPTFHandler = (tableMeta) => {
    // get the ptf has from the table data
    const ptfHash = tableMeta.rowData[9];

    // make a request to the download endpoint
    axios({
      method: "get",
      url: "/download/prodigal_training_files/" + ptfHash,
    }).then((res) => {
      console.log(res);

      const url_hostname = new URL(res.config.baseURL).hostname;

      let link_href = "undefined";

      if (url_hostname.includes("chewbbaca")) {
        link_href = `https://${url_hostname}/api/NS/api/download/prodigal_training_files/${ptfHash}`;
      } else {
        link_href = `https://${url_hostname}/NS/api/download/prodigal_training_files/${ptfHash}`;
      }

      const spd = JSON.parse(localStorage.getItem("speciesD"));

      let speciesName = spd[this.props.match.params.species_id];

      const fileName = speciesName.replace(" ", "_") + ".trn";

      // create download element
      const link = document.createElement("a");
      link.href = link_href;
      link.setAttribute("download", fileName);
      document.body.appendChild(link);
      link.click();
    });
  };

  downloadCompressedSchemasHandler = (tableMeta) => {
    const spd = JSON.parse(localStorage.getItem("speciesD"));

    // get the species ID
    const speciesId = this.props.match.params.species_id;

    // get the Schema ID
    const schemaId = tableMeta.rowData[0];

    // get the Schema Name
    const schemaName = tableMeta.rowData[1];

    // get last modification date
    let lastModifiedDate = "";

    for (let scheID in this.props.species) {
      console.log(this.props.species[scheID]);
      if (schemaId === this.props.species[scheID].schema_id) {
        lastModifiedDate = this.props.species[scheID].lastModifiedISO;
      } else {
        lastModifiedDate = this.props.species[0].lastModifiedISO;
      }
    }

    const endpointVariables =
      speciesId + "/" + schemaId + "/" + lastModifiedDate;

    // make a request to the download endpoint
    axios({
      method: "get",
      url: "/download/compressed_schemas/" + endpointVariables,
    }).then((res) => {
      console.log(res);

      const url_hostname = new URL(res.config.baseURL).hostname;

      let link_href = "undefined";

      if (url_hostname.includes("chewbbaca")) {
        link_href = `https://${url_hostname}/api/NS/api/download/compressed_schemas/${endpointVariables}`;
      } else {
        link_href = `https://${url_hostname}/NS/api/download/compressed_schemas/${endpointVariables}`;
      }

      let speciesName2 = spd[this.props.match.params.species_id];

      const fileName2 =
        speciesName2.replace(" ", "_") +
        "_" +
        schemaName +
        "_" +
        lastModifiedDate +
        ".zip";

      // create download element
      const link = document.createElement("a");
      link.href = link_href;
      link.setAttribute("download", fileName2);
      document.body.appendChild(link);
      link.click();
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
        MUIDataTableToolbar: {
          titleText: {
            color: "#bb7944",
          },
        },
      },
    });

  render() {
    let species = <CircularProgress />;
    let species_plot = (
      <div style={{ textAlign: "center" }}>
        <CircularProgress />
      </div>
    );

    const spd = JSON.parse(localStorage.getItem("speciesD"));

    if (!this.props.loading) {
      const columns = [
        ...SPECIES_COLUMNS,
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
                  onClick={() => this.rowClickHandler(tableMeta)}
                >
                  More Details
                </Button>
              );
            },
          },
        },
        {
          name: "Prodigal Training File",
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
            customBodyRender: (value, tableMeta, updateValue) => {
              return (
                <div>
                  <div>
                    <Button
                      variant="contained"
                      color="default"
                      startIcon={<GetAppSharpIcon />}
                      onClick={() => this.downloadPTFHandler(tableMeta)}
                    >
                      Download
                    </Button>
                  </div>
                </div>
              );
            },
          },
        },
        {
          name: "Compressed Schema",
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
            customBodyRender: (value, tableMeta, updateValue) => {
              return (
                <div>
                  <div>
                    <Button
                      variant="contained"
                      color="default"
                      startIcon={<GetAppSharpIcon />}
                      onClick={() =>
                        this.downloadCompressedSchemasHandler(tableMeta)
                      }
                    >
                      Download
                    </Button>
                  </div>
                </div>
              );
            },
          },
        },
      ];

      const title = spd[this.props.match.params.species_id];

      species = (
        <MuiThemeProvider theme={this.getMuiTheme()}>
          <MUIDataTable
            title={<i>{title}</i>}
            data={this.props.species}
            columns={columns}
            options={SPECIES_OPTIONS}
          />
        </MuiThemeProvider>
      );

      species_plot = (
        <Plot
          data={this.props.species_annot}
          layout={{
            title: {
              text: "<i>" + title + "</i>",
            },
            autosize: true,
            xaxis: {
              title: { text: "Loci" },
              showticklabels: false,
            },
            yaxis: {
              title: { text: "Number of alleles" },
            },
            hovermode: "closest",
          }}
          useResizeHandler={true}
          style={{ width: "100%", height: "100%" }}
          line={{
            width: 1,
          }}
          onClick={(e) => this.clickPlotHandler(e)}
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
        <div style={{ marginLeft: "5%", marginRight: "5%" }}>
          <div>
            <h1 style={{ textAlign: "center" }}>Schemas Overview</h1>
          </div>
          <div style={{ marginTop: "40px" }}>{species}</div>
          <div style={{ marginTop: "40px", marginBottom: "40px" }}>
            {species_plot}
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
    species: state.species.species,
    species_annot: state.species.species_annot,
    loading: state.species.loading,
    error: state.species.error,
  };
};

// Map dispatch functions that trigger
// actions from redux
// to the props of this component
const mapDispatchToProps = (dispatch) => {
  return {
    onFetchSpecies: (spec_id) => dispatch(actions.fetchSpecies(spec_id)),
    onFetchSpeciesAnnot: (spec_id) =>
      dispatch(actions.fetchSpeciesAnnot(spec_id)),
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withErrorHandler(Species, axios));
