import React, { Component } from "react";
import { connect } from "react-redux";

import axios from "../../axios-backend";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";
import * as actions from "../../store/actions/index";
// import Spinner from "../../components/UI/Spinner/Spinner";

// Material-UI components
import CircularProgress from "@material-ui/core/CircularProgress";

// Material-UI Datatables
import MUIDataTable from "mui-datatables";

// Plotly.js
import Plot from "react-plotly.js";


class Locus extends Component {
  componentDidMount() {
    const locusId = this.props.location.pathname.substring(this.props.location.pathname.lastIndexOf("/") + 1);

    console.log(["componentDidMount"])
    console.log(locusId)

    this.props.onFetchLocusFasta(locusId);
    this.props.onFetchLocusUniprot(locusId);
  }

  render() {
    let uniprot_data = <CircularProgress />;
    let fasta_data = <CircularProgress />;
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
                <a href={value} target="_blank" rel="noopener noreferrer">{value}</a>
              )
            }
          }
        }
      ]

      const options = {
        responsive: "scrollMaxHeight",
        selectableRowsHeader: false,
        selectableRows: "none",
        selectableRowsOnClick: true,
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
              title: { text: "Sequence size (bp)" },
            },
            yaxis: {
              title: { text: "# Alleles" }
            },

          }}
          useResizeHandler={true}
          style={{ width: "100%", height: "100%" }}
          line={{
            width: 1
          }}
          onClick={e => this.clickPlotHandler(e)}
        />
      )
    }
    return <div>
      {fasta_data}
      {uniprot_data}
    </div>;
  }
}

const mapStateToProps = state => {
  return {
    locus_fasta: state.locus.locus_fasta,
    locus_uniprot: state.locus.locus_uniprot,
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
