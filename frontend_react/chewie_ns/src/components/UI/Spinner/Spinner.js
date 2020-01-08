import React from 'react';

// import classes from './Spinner.module.css';
import ChewieGif from '../../../assets/images/chewie.gif'

const spinner = () => (
    // <div className={classes.Loader}>Loading...</div>
    <div>
        <img src={ChewieGif} alt="Loading..." />
    </div>
);

export default spinner;