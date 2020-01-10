import React, { Component } from "react";
import { connect } from "react-redux";

import axios from "../../axios-backend";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";
import * as actions from "../../store/actions/index";
import Spinner from "../../components/UI/Spinner/Spinner";

// Material-UI components
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableContainer from "@material-ui/core/TableContainer";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import Paper from "@material-ui/core/Paper";

class Species extends Component {
  componentDidMount() {
    // console.log("[this.props Stats]")
    // console.log(this.props)
    this.props.onFetchSpecies(this.props.token);
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
      // console.log(this.props.species)
      species =
          <TableContainer component={Paper}>
            <Table style={{minWidth: 650}} aria-label="simple table">
              <TableHead>
                <TableRow>
                  <TableCell style={{fontWeight: "bold"}}>Species</TableCell>
                  <TableCell style={{fontWeight: "bold"}}>Species ID</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {this.props.species.map(sp => (
                  <TableRow key={sp.id}>
                    <TableCell component="th" scope="row">
                      {sp.species_name}
                    </TableCell>
                    <TableCell>{sp.species_id}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
      }
      return <div>{species}</div>;
    }
  }

const mapStateToProps = state => {
  return {
    species: state.species.species,
    loading: state.species.loading,
    error: state.species.error,
    token: state.auth.token
  };
};

const mapDispatchToProps = dispatch => {
  return {
    onFetchSpecies: token => dispatch(actions.fetchSpecies(token))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withErrorHandler(Species, axios));
