import React, { Component } from 'react';

import Spinner from "../../components/UI/Spinner/Spinner";

import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";
// import * as actions from '../../store/actions/index';
import axios from "../../axios-backend";

class Chewie extends Component {
    render() {
        return (
            <div>
                <h1>WELCOME TO CHEWIE-NS!!</h1>
                <Spinner />
            </div>
        );
    }
}

export default withErrorHandler( Chewie, axios ) ;