import React, { Component } from "react";
import { connect } from "react-redux";

import axios from "../../axios-backend";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";
import * as actions from "../../store/actions/index";
import Spinner from "../../components/UI/Spinner/Spinner";

class Stats extends Component {
  componentDidMount() {
    // console.log("[this.props Stats]")
    // console.log(this.props)
    this.props.onFetchStats();
  }

  render() {
    // console.log("[props loading]")
    // console.log(this.props.loading)
    let stats = <Spinner />;
    if (!this.props.loading) {
      stats = this.props.stats.map(stat => {
        return (
          <span
            style={{
              textTransform: "capitalize",
              display: "inline-block",
              margin: "0 8px",
              border: "1px solid #ccc",
              padding: "5px"
            }}
            key={stat.id}
          >
            {stat.data}
          </span>
        );
      });
    }
    return (
      <div>{stats}</div>
    );
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
    onFetchStats: () => dispatch(actions.fetchStats())
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withErrorHandler(Stats, axios));
