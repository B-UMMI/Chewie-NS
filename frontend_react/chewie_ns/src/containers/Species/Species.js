import React, { Component } from 'react';
import { connect } from "react-redux";

import axios from "../../axios-backend";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";
import * as actions from "../../store/actions/index";
import Spinner from "../../components/UI/Spinner/Spinner";

class Species extends Component {
    componentDidMount() {
        // console.log("[this.props Stats]")
        // console.log(this.props)
        this.props.onFetchSpecies(this.props.token);
      }

    render() {
        let species = <Spinner />;
        if (!this.props.loading) {
            // console.log(this.props.species)
            species = this.props.species.map(sp => {
                return (
                    <ul key={sp.id}>
                        {sp.species_name} {sp.species_id} 
                    </ul>
                )
            })
        }
        return (
            <div>
               {species} 
            </div>
        );
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
      onFetchSpecies: (token) => dispatch(actions.fetchSpecies(token))
    };
  };
  
  export default connect(
    mapStateToProps,
    mapDispatchToProps
  )(withErrorHandler(Species, axios));