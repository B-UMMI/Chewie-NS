import React, { Component } from "react";
import { connect } from "react-redux";

import axios from "../../axios-backend";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";
import * as actions from "../../store/actions/index";

// Material-UI components
import CircularProgress from "@material-ui/core/CircularProgress";

// Plotly.js
import Plot from "react-plotly.js";

class Schema extends Component {
  componentDidMount() {
    // console.log(this.props.match);

    const species_id = this.props.match.params.species_id;
    const schema_id = this.props.match.params.schema_id
    
    this.props.onFetchSchemaAlleleMode(species_id, schema_id)
  }

  render() {
    let mode_plot = <CircularProgress />;
    let total_allele_plot = <CircularProgress />;

    if (!this.props.loading) {
        // console.log(this.props.mode_data)
        
        mode_plot = (
            <Plot
              data={this.props.mode_data}
              layout={{
                title: {
                  text: "Distribution of allele mode sizes per gene"
                },
                xaxis: {
                  title: { text: "Allele Size" },
                  showgrid: true
                },
                yaxis: {
                  title: { text: "Number of occurrences" }
                }
              }}
              useResizeHandler={true}
              style={{ width: "100%", height: "100%" }}
              line={{
                width: 1
              }}
            //   onClick={e => this.clickPlotHandler(e)}
            />
          );

        total_allele_plot = (
            <Plot
              data={this.props.total_allele_data}
              layout={{
                title: {
                  text: "Alleles per locus"
                },
                xaxis: {
                  title: { text: "Number of Different Alleles" },
                  showgrid: true
                },
                yaxis: {
                  title: { text: "Number of Loci" }
                }
              }}
              useResizeHandler={true}
              style={{ width: "100%", height: "100%" }}
              line={{
                width: 1
              }}
              onClick={e => console.log(e)}
            />
          );
    
    }

    return <div>
            <div>{mode_plot}</div>
            <div>{total_allele_plot}</div>
           </div>
  }
}

const mapStateToProps = state => {
  return {
    mode_data: state.schema.mode_data,
    total_allele_data: state.schema.total_allele_data,
    loading: state.schema.loading,
    error: state.schema.error
    // token: state.auth.token
  };
};

const mapDispatchToProps = dispatch => {
  return {
    onFetchSchemaAlleleMode: (species_id, schema_id) =>
      dispatch(actions.fetchSchemaAlleleMode(species_id, schema_id))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withErrorHandler(Schema, axios));
