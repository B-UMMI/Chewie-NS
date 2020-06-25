import React, { Component } from "react";
import { connect } from "react-redux";

import axios from "../../axios-backend";
import Spinner from "../../components/UI/Spinner/Spinner";
import Copyright from "../../components/Copyright/Copyright";
import * as actions from "../../store/actions/index";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";

// Material-UI components
import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
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

    let species_url_array = species_url.split("/");

    let species_id = species_url_array[species_url_array.length - 1];

    this.props.onFetchSpecies(species_id);
    this.props.onFetchSpeciesAnnot(species_id);
  }

  clickPlotHandler = (event) => {
    console.log(event.points[0]);

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
    });

    const spd = JSON.parse(localStorage.getItem("speciesD"));

    let speciesName = spd[this.props.match.params.species_id];

    const fileName = speciesName.replace(" ", "_") + ".trn";

    // create download element
    const link = document.createElement("a");
    link.href =
      "https://chewbbaca.online/api/NS/api/download/prodigal_training_files/" +
      ptfHash;
    link.setAttribute("download", fileName);
    document.body.appendChild(link);
    link.click();
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
    const lastModifiedDate = this.props.species[schemaId - 1].lastModifiedISO;

    const endpointVariables =
      speciesId + "/" + schemaId + "/" + lastModifiedDate;

    // make a request to the download endpoint
    axios({
      method: "get",
      url: "/download/compressed_schemas/" + endpointVariables,
    }).then((res) => {
      console.log(res);
    });

    let speciesName = spd[this.props.match.params.species_id];

    const fileName =
      speciesName.replace(" ", "_") +
      "_" +
      schemaName +
      "_" +
      lastModifiedDate +
      ".zip";

    // create download element
    const link = document.createElement("a");
    link.href =
      "https://chewbbaca.online/api/NS/api/download/compressed_schemas/" +
      endpointVariables;
    link.setAttribute("download", fileName);
    document.body.appendChild(link);
    link.click();
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
    let species = <Spinner />;
    let species_plot = (
      <div style={{ textAlign: "center" }}>
        <CircularProgress />
      </div>
    );

    const spd = JSON.parse(localStorage.getItem("speciesD"));

    if (!this.props.loading) {
      const columns = [
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

      const options = {
        textLabels: {
          body: {
            noMatch: <CircularProgress />,
          },
        },
        responsive: "scrollMaxHeight",
        selectableRowsHeader: false,
        selectableRows: "none",
        print: false,
        viewColumns: true,
        pagination: false,
      };

      const title = spd[this.props.match.params.species_id];

      species = (
        <MuiThemeProvider theme={this.getMuiTheme()}>
          <MUIDataTable
            title={<i>{title}</i>}
            data={this.props.species}
            columns={columns}
            options={options}
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
      <div style={{ marginLeft: "5%", marginRight: "5%" }}>
        <div>
          <h1 style={{ textAlign: "center" }}>Schemas Overview</h1>
        </div>
        <div style={{ marginTop: "40px" }}>{species}</div>
        <div style={{ marginTop: "40px" }}>{species_plot}</div>
        <Copyright />
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    species: state.species.species,
    species_annot: state.species.species_annot,
    loading: state.species.loading,
    error: state.species.error,
  };
};

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
