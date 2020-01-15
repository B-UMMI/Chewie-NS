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

// Material Table
// import MaterialTable from 'material-table';

// Material-UI Datatables
import MUIDataTable from "mui-datatables";

class Stats extends Component {
  componentDidMount() {
    // console.log("[this.props Stats]")
    // console.log(this.props)
    // this.props.onFetchStats();
    this.props.onFetchSpeciesStats();
  }

  rowClickHandler = (species_id) => {
    console.log("[RowClick]");
    console.log("species_id: ", species_id);
    // console.log("rowMeta: ", rowMeta);
    this.props.history.push('/species/' + species_id);
  }
  
  render() {
    // console.log("[props loading]")
    // console.log(this.props.loading)
    let stats = <Spinner />;
    // if (!this.props.loading) {
    //   stats = this.props.stats.map(stat => {
    //     return (
    //       <span
    //         style={{
    //           textTransform: "capitalize",
    //           display: "inline-block",
    //           margin: "0 8px",
    //           border: "1px solid #ccc",
    //           padding: "5px"
    //         }}
    //         key={stat.id}
    //       >
    //         {stat.data}
    //       </span>
    //     );
    //   });
    // }
    if (!this.props.loading) {
      console.log("[before table]");
      console.log(this.props.stats);


      // stats =
      //     <TableContainer component={Paper}>
      //       <Table style={{minWidth: 650}} aria-label="simple table">
      //         <TableHead>
      //           <TableRow>
      //             <TableCell style={{fontWeight: "bold"}}>Species</TableCell>
      //             <TableCell style={{fontWeight: "bold"}}>Schemas Available</TableCell>
      //           </TableRow>
      //         </TableHead>
      //         <TableBody>
      //           {this.props.stats.map(stat => (
      //             <TableRow hover key={stat.id} onClick={this.clickHandler(stat.id, stat.species_name)}>
      //               <TableCell component="th" scope="row">
      //                 {stat.species_name}
      //               </TableCell>
      //               <TableCell>{stat.nr_schemas}</TableCell>
      //             </TableRow>
      //           ))}
      //         </TableBody>
      //       </Table>
      //     </TableContainer>

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
            }
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
        responsive: "scrollMaxHeight",
        selectableRowsHeader: false,
        selectableRows: "none",
        print: false,
        viewColumns: false,
        onRowClick: (rowData) => this.rowClickHandler(rowData[rowData.length - 1])
      };

      stats = (
        <MUIDataTable
          title={"Overview"}
          data={this.props.stats}
          columns={columns}
          options={options}
        />
      );

    }
    return <div>{stats}</div>;
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
