import React, { Component } from "react";
import axios from "../../axios-backend";

// Chewie local imports
import text from "../../components/data/about_md";
import Markdown from "../../components/Markdown/Markdown";
import Copyright from "../../components/Copyright/Copyright";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";

class About extends Component {
  render() {
    return (
      <div id="homeDiv" className={classes.homeDiv}>
        <Markdown markdown={text} />
        <Copyright />
      </div>
    );
  }
}

export default withErrorHandler(About, axios);
