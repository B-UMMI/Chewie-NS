import React from 'react';

// import classes from './Spinner.module.css';
import ChewieGif from '../../../assets/images/chewie.gif'

const spinner = () => (
    {% raw -%}
    <div style={{textAlign: "center"}}>
        <img src={ChewieGif} alt="Loading..." />
    </div>
    {% endraw %}
);

export default spinner;