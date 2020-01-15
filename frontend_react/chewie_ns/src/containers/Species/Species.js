import React, { Component } from "react";
import { connect } from "react-redux";

import axios from "../../axios-backend";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";
import * as actions from "../../store/actions/index";
import Spinner from "../../components/UI/Spinner/Spinner";

// Material-UI components
// import Table from "@material-ui/core/Table";
// import TableBody from "@material-ui/core/TableBody";
// import TableCell from "@material-ui/core/TableCell";
// import TableContainer from "@material-ui/core/TableContainer";
// import TableHead from "@material-ui/core/TableHead";
// import TableRow from "@material-ui/core/TableRow";
// import Paper from "@material-ui/core/Paper";

// Material-UI Datatables
import MUIDataTable from "mui-datatables";

// Plotly.js
import Plot from "react-plotly.js";

class Species extends Component {
  componentDidMount() {
    // console.log("[this.props Stats]")
    // console.log(this.props)
    // console.log("[PATH NAME]")
    // console.log(this.props.location.pathname[this.props.location.pathname.length - 1])
    this.props.onFetchSpecies(
      this.props.location.pathname[this.props.location.pathname.length - 1]
    );
    this.props.onFetchSpeciesAnnot(
      this.props.location.pathname[this.props.location.pathname.length - 1]
    );
  }

  render() {
    let species = <Spinner />;
    // if (!this.props.loading) {
    //     // console.log(this.props.species)
    //     species = this.props.species.map(sp => {
    //         return (
    //             <ul key={sp.id}>
    //                 <li>{sp.species_name} {sp.species_id}</li>
    //             </ul>
    //         )
    //     })
    // }
    if (!this.props.loading) {
      console.log("[before table]");
      // console.log(this.props.species);
      console.log(this.props.species_annot);
      // console.log(this.props.species)
      // species =
      //     <TableContainer component={Paper}>
      //       <Table style={{minWidth: 650}} aria-label="simple table">
      //         <TableHead>
      //           <TableRow>
      //             <TableCell style={{fontWeight: "bold"}}>Species</TableCell>
      //             <TableCell style={{fontWeight: "bold"}}>Species ID</TableCell>
      //           </TableRow>
      //         </TableHead>
      //         <TableBody>
      //           {this.props.species.map(sp => (
      //             <TableRow key={sp.id}>
      //               <TableCell component="th" scope="row">
      //                 {sp.species_name}
      //               </TableCell>
      //               <TableCell>{sp.species_id}</TableCell>
      //             </TableRow>
      //           ))}
      //         </TableBody>
      //       </Table>
      //     </TableContainer>

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
        responsive: "scrollMaxHeight",
        selectableRowsHeader: false,
        selectableRows: "none",
        print: false,
        viewColumns: true,
        pagination: false
        // onRowClick: (rowData) => this.rowClickHandler(rowData[rowData.length - 1])
      };

      // species = this.props.species.map(schema => (
      //   <div key={schema.id}>
      //     <MUIDataTable
      //     title={"Overview"}
      //     data={this.props.species[schema]}
      //     columns={columns}
      //     options={options}
      //     />
      //   </div>
      // ))
      species = (
        <MUIDataTable
          title={"Schema Details"}
          data={this.props.species}
          columns={columns}
          options={options}
        />
      );
    }
    return (
      <div>
        <div>{species}</div>
        <Plot
          data={this.props.species_annot}
          layout={{
            // height: 500,
            title: {
              text: "A Fancy Plot"
            },
            autosize: true,
            xaxis: {
              title: {text: 'Loci'}
            },
            yaxis: {
              title: {text: 'Nr alleles'}
            }
          }}
          useResizeHandler={true}
          style={{ width: "100%", height: "100%" }}
          line={{
            width: 1
          }}
        />
      </div>
    );
  }
}

const mapStateToProps = state => {
  return {
    species: state.species.species,
    species_annot: state.species.species_annot,
    loading: state.species.loading,
    error: state.species.error
    // token: state.auth.token
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
