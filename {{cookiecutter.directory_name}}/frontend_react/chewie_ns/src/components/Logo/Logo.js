import React from 'react';

import chewieNSLogo from '../../assets/images/chewie_logo.png';
import classes from './Logo.module.css';

const logo = (props) => (
    {% raw -%}
    <div className={classes.Logo} style={{height: props.height}}>
        <img src={chewieNSLogo} alt="ChewieNS" />
    </div>
    {% endraw %}
);

export default logo;