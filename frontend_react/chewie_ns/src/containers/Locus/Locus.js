import React, { Component } from "react";
import { connect } from "react-redux";

import axios from "../../axios-backend";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";
import * as actions from "../../store/actions/index";
// import Spinner from "../../components/UI/Spinner/Spinner";

// Material-UI components
import CircularProgress from "@material-ui/core/CircularProgress";
import Button from "@material-ui/core/Button";
import GetAppSharpIcon from "@material-ui/icons/GetAppSharp";
import Box from '@material-ui/core/Box';

// Material-UI Datatables
import MUIDataTable from "mui-datatables";

// Plotly.js
import Plot from "react-plotly.js";

// Download function
import { saveAs } from 'file-saver';

class Locus extends Component {
  componentDidMount() {
    const locusId = this.props.location.pathname.substring(
      this.props.location.pathname.lastIndexOf("/") + 1
    );

    console.log(["componentDidMount"]);
    console.log(locusId);

    this.props.onFetchLocusFasta(locusId);
    this.props.onFetchLocusUniprot(locusId);
  }

  downloadFastaHandler = () => {
    // console.log(this.props.fasta_data)
    const fastaJoin = this.props.fasta_data.join("\n")

    const blob = new Blob([fastaJoin], {type: "text/plain;charset=utf-8"});

    saveAs(blob, "test.txt")

  }

  render() {
    let uniprot_data = <CircularProgress />;
    let fasta_data = <CircularProgress />;
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
    // console.log(this.props.locus_fasta)
    if (!this.props.loading) {
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
          name: "uniprot_submitted_name",
          label: "Uniprot Submitted Name",
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
        }
      ];

      const options = {
        responsive: "scrollMaxHeight",
        selectableRowsHeader: false,
        selectableRows: "none",
        selectableRowsOnClick: false,
        print: false,
        download: false,
        filter: false,
        search: false,
        viewColumns: true,
        pagination: false
      };

      uniprot_data = (
        <MUIDataTable
          title={"Uniprot Annotation"}
          data={this.props.locus_uniprot}
          columns={columns}
          options={options}
        />
      );

      fasta_data = (
        <Plot
          data={this.props.locus_fasta}
          layout={{
            // height: 500,
            title: {
              text: "Locus Details"
            },
            xaxis: {
              title: { text: "Sequence size (bp)" }
            },
            yaxis: {
              title: { text: "# Alleles" }
            }
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
      <div>
        {fasta_data}
        {uniprot_data}
        <Box style={{height: 80, display: "flex", justifyContent: 'center', alignItems: 'center'}}>{downloadFasta}</Box>
      </div>
    );
  }
}

const mapStateToProps = state => {
  return {
    locus_fasta: state.locus.locus_fasta,
    locus_uniprot: state.locus.locus_uniprot,
    fasta_data: state.locus.fasta_data,
    loading: state.locus.loading,
    error: state.locus.error
    // token: state.auth.token
  };
};

const mapDispatchToProps = dispatch => {
  return {
    onFetchLocusFasta: locus_id => dispatch(actions.fetchLocusFasta(locus_id)),
    onFetchLocusUniprot: locus_id =>
      dispatch(actions.fetchLocusUniprot(locus_id))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withErrorHandler(Locus, axios));
