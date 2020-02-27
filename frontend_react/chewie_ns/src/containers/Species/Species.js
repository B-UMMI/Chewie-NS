import React, { Component } from "react";
import { connect } from "react-redux";

import axios from "../../axios-backend";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";
import * as actions from "../../store/actions/index";
import Spinner from "../../components/UI/Spinner/Spinner";

// Material-UI components
import CircularProgress from "@material-ui/core/CircularProgress";
import Typography from "@material-ui/core/Typography";
import Button from "@material-ui/core/Button";
import GetAppSharpIcon from "@material-ui/icons/GetAppSharp";
import { createMuiTheme, MuiThemeProvider } from "@material-ui/core/styles";

// Material-UI Datatables
import MUIDataTable from "mui-datatables";

// Plotly.js
import Plot from "react-plotly.js";

class Species extends Component {
  componentDidMount() {
    // console.log("[this.props Stats]")
    // console.log(this.props.history)
    // console.log("[PATH NAME]")
    // console.log(this.props.location.pathname[this.props.location.pathname.length - 1])
    this.props.onFetchSpecies(
      this.props.location.pathname[this.props.location.pathname.length - 1]
    );
    this.props.onFetchSpeciesAnnot(
      this.props.location.pathname[this.props.location.pathname.length - 1]
    );

  }

  clickPlotHandler = event => {
    console.log(event.points[0]);
    // console.log("[Schema ID]");
    // console.log(event.points[0].data.name.slice(-1));
    // console.log("[Locus ID]");
    // console.log(event.points[0].hovertext);

    // const species_id = this.props.location.pathname[
    //   this.props.location.pathname.length - 1
    // ];

    // console.log(this.props.location.pathname)

    // const species_id = this.props.location.pathname;

    const schema_id = event.points[0].data.name.slice(-1);

    const locus_id = event.points[0].text;
    // console.log(schema_id)
    // console.log(locus_id)

    // console.log(this.props.match);

    this.props.history.push(
     this.props.match.params.species_id +
       "/schemas/" +
       schema_id +
       "/locus/" +
       locus_id
    );
  };

  rowClickHandler = schema_id => {
    console.log("[RowClick]");
    console.log("schema_id: ", schema_id);
    // console.log(this.props.match)
    // this.setState({ schema: schema_id})
    // console.log(this.props.match);
    this.props.history.push({
      pathname: `${this.props.match.params.species_id}/schemas/${schema_id}`
    });
  };

  getMuiTheme = () =>
    createMuiTheme({
      overrides: {
        MuiTableRow: {
          root: {
            cursor: "pointer"
          }
        }
      }
    });

  render() {
    let species = <Spinner />;
    let species_plot = <div style={{ textAlign: "center" }}><CircularProgress /></div>;

    // this.setState({
    //   species_name: this.props.location.state.species_name
    // })

    if (!this.props.loading) {
      const columns = [
        {
          name: "schema_id",
          label: "Schema ID",
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
          name: "schema_name",
          label: "Schema Name",
          options: {
            filter: true,
            sort: false,
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
          name: "user",
          label: "Created by",
          options: {
            filter: false,
            sort: true,
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
          name: "nr_loci",
          label: "Loci",
          options: {
            filter: false,
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
          name: "nr_allele",
          label: "Alleles",
          options: {
            filter: false,
            sort: true,
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
          name: "chewie",
          label: "chewBBACA version",
          options: {
            filter: false,
            sort: false,
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
          name: "bsr",
          label: "Blast Score Ratio",
          options: {
            filter: false,
            sort: true,
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
          name: "ptf",
          label: "Prodigal Training File",
          options: {
            filter: false,
            sort: true,
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
          name: "tl_table",
          label: "Translation Table",
          options: {
            filter: false,
            sort: true,
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
          name: "minLen",
          label: "Minimum Length (bp)",
          options: {
            filter: false,
            sort: true,
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
        print: false,
        viewColumns: true,
        pagination: false,
        onRowClick: rowData => this.rowClickHandler(rowData[0])
      };

      // for (i in this.props.speciesDict) {

      // }

      // const title = this.props.speciesDict[this.props.match.params.species_id];

      // console.log(this.props.speciesDict[this.props.match.params.species_id])

      species = (
        <MuiThemeProvider theme={this.getMuiTheme()}>
          <MUIDataTable
            title={<i>{this.props.speciesDict[this.props.match.params.species_id]}</i>}
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
              text: this.props.speciesDict[this.props.match.params.species_id]
            },
            autosize: true,
            xaxis: {
              title: { text: "Loci" },
              showticklabels: false
              // range: [0, 500]
            },
            yaxis: {
              title: { text: "Number of alleles" }
            },
            hovermode: "closest"
          }}
          useResizeHandler={true}
          style={{ width: "100%", height: "100%" }}
          line={{
            width: 1
          }}
          onClick={e => this.clickPlotHandler(e)}
        />
      );
    }
    return (
      <div style={{marginLeft : "5%", marginRight: "5%"}}>
        <div><h1 style={{ textAlign: "center" }}>Schemas Overview</h1></div>
        {species}
        {species_plot}
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
            <div
            >
              <Typography style={{fontSize: "10"}}>© UMMI 2020</Typography>
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
    species: state.species.species,
    species_annot: state.species.species_annot,
    loading: state.species.loading,
    error: state.species.error,
    speciesDict: state.stats.speciesDict
  };
};

const mapDispatchToProps = dispatch => {
  return {
    onFetchSpecies: spec_id => dispatch(actions.fetchSpecies(spec_id)),
    onFetchSpeciesAnnot: spec_id => dispatch(actions.fetchSpeciesAnnot(spec_id))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withErrorHandler(Species, axios));
