import React, { Component } from "react";
import { connect } from "react-redux";

import axios from "../../axios-backend";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";
import * as actions from "../../store/actions/index";
// import Spinner from "../../components/UI/Spinner/Spinner";

// Material-UI components

import CircularProgress from "@material-ui/core/CircularProgress";

class Locus extends Component {
  componentDidMount() {
    const locusId = this.props.location.pathname.substring(this.props.location.pathname.lastIndexOf("/") + 1);

    console.log(["componentDidMount"])
    console.log(locusId)

    this.props.onFetchLocusFasta(locusId);
    this.props.onFetchLocusUniprot(locusId);
  }

  render() {
    let fasta_data = <CircularProgress />;
    // if (!this.props.loading) {
    // }
    return <div>{fasta_data}</div>;
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
