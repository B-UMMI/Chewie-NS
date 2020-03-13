import React, { Component } from "react";
import axios from "../../axios-backend";

import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";

import classes from "./About.module.css";

class About extends Component {
  render() {
    return (
      <div id="homeDiv" className={classes.homeDiv}>
        <div id="titleDiv" className={classes.titleDiv}>
          <h2>About</h2>
        </div>
        <div id="bodyDiv" className={classes.bodyDiv}>
          Chewie-NS is developed by the{" "}
          <a
            href="http://darwin.phyloviz.net/wiki/doku.php?id=start"
            target={"_blank"}
            rel="noopener noreferrer"
          >
            Molecular Microbiology and Infection Unit (UMMI)
          </a>{" "}
          at the{" "}
          <a
            href="https://imm.medicina.ulisboa.pt/"
            target={"_blank"}
            rel="noopener noreferrer"
          >
            Instituto de Medicina Molecular Joao Lobo Antunes
          </a>
          . This project is licensed under the{" "}
          <a
            href="https://github.com/B-UMMI/Nomenclature_Server_docker_compose/blob/master/LICENSE"
            target={"_blank"}
            rel="noopener noreferrer"
          >
            GPLv3 license
          </a>
          . The source code of Chewie-NS is available at <a
            href="https://github.com/B-UMMI/Nomenclature_Server_docker_compose"
            target={"_blank"}
            rel="noopener noreferrer"
          >
            https://github.com/B-UMMI/Nomenclature_Server_docker_compose
          </a>
          .
        </div>
        <footer
          style={{
            position: "fixed",
            bottom: "0",
            left: "0",
            backgroundColor: "#ccc",
            width: "100%",
            textAlign: "center"
          }}
        >
          <div id="homeFooter" style={{ display: "block" }}>
            <div>
              <Typography style={{ fontSize: "10" }}>© UMMI 2020</Typography>
              {/* <p>© UMMI 2020</p> */}
            </div>
          </div>
        </footer>
      </div>
    );
  }
}

export default withErrorHandler(About, axios);
