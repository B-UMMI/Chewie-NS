import React, { Component } from "react";
import axios from "../../axios-backend";
import ReactDependentScript from "react-dependent-script";

// Chewie local imports
import Aux from "../../hoc/Aux/Aux";
import text from "../../components/data/about_md";
import classes from "./About.module.css";
import Markdown from "../../components/Markdown/Markdown";
import Copyright from "../../components/Copyright/Copyright";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";

class About extends Component {
  render() {
    return (
      <Aux>
        <ReactDependentScript
          loadingComponent={<div></div>}
          scripts={["https://d1bxh8uas1mnw7.cloudfront.net/assets/embed.js"]}
        >
          <div></div>
        </ReactDependentScript>
        <ReactDependentScript
          loadingComponent={<div></div>}
          scripts={["https://badge.dimensions.ai/badge.js"]}
        >
          <div></div>
        </ReactDependentScript>

        <div id="homeDiv" className={classes.homeDiv}>
          <Markdown markdown={text} />
          <Copyright />
        </div>
        <div
          style={{
            display: "flex",
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "center",
            marginTop: "40px",
          }}
        >
          <h3>chewBBACA metrics:</h3>
        </div>
        <div
          style={{
            display: "flex",
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <div
            id="engagement"
            class="altmetric-embed"
            data-link-target="_blank"
            data-badge-type="medium-donut"
            data-badge-details="right"
            data-pmid="29543149"
          ></div>
          <div
            id="citations"
            class="__dimensions_badge_embed__"
            data-id="pub.1101538024"
            data-legend="always"
            style={{ marginLeft: "2%", marginBottom: "4%" }}
          ></div>
        </div>
      </Aux>
    );
  }
}

export default withErrorHandler(About, axios);
