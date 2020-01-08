import React from 'react';

// import classes from '../../../assets/images/';

// import classes from './GithubButton.module.css';

const button = (props) => (
    <button>
        <img src="../../../assets/images/github_logo.png" alt="Github Logo" onClick={props.clicked}>{props.children} /></img>
    </button>    
);

export default button;