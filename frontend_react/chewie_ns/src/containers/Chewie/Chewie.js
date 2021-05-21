import React, { Component } from "react";

// Assets imports
import INCDlogo from "../../assets/images/INCD-small.png";
import UMMIlogo from "../../assets/images/ummi1small2.png";
import IMMlogo from "../../assets/images/iMM_JLA_medium2.png";
import FMULlogo from "../../assets/images/fmul_logo.png";

// Chewie local imports
import Aux from "../../hoc/Aux/Aux";
import axios from "../../axios-backend";
import classes from "./Chewie.module.css";
import Markdown from "../../components/Markdown/Markdown";
import ChewieFrontPageMarkdown from "../../components/data/chewie";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";

class Chewie extends Component {
  render() {
    return (
      <Aux>
        <div id="homeDiv" className={classes.homeDiv}>
          <div
            id="logoDiv"
            style={{
              display: "flex",
              flexDirection: "row",
              alignItems: "center",
              justifyContent: "center",
              marginTop: "-50px",
            }}
          >
            <a
              href={"https://imm.medicina.ulisboa.pt/"}
              target="_blank"
              rel="noopener noreferrer"
            >
              <img src={IMMlogo} alt="IMM" />
            </a>
            <a
              href={"https://www.medicina.ulisboa.pt/"}
              target="_blank"
              rel="noopener noreferrer"
            >
              <img src={FMULlogo} alt="FM" />
            </a>
            <a
              href={"http://im.fm.ul.pt"}
              target="_blank"
              rel="noopener noreferrer"
            >
              <img src={UMMIlogo} alt="UMMI!" />
            </a>
          </div>
          <Markdown markdown={ChewieFrontPageMarkdown} />
          <div id="INCD_div" className={classes.incdDiv}>
            <div id="resourcesTextDiv">
              <p className={classes.resourcesText}>
                <b>Resources provided by</b>
              </p>
              <a
                href={"https://www.incd.pt/"}
                target={"_blank"}
                rel={"noopener noreferrer"}
              >
                <img src={INCDlogo} alt="Resources provided by" />
              </a>
            </div>
          </div>
        </div>
      </Aux>
    );
  }
}

export default withErrorHandler(Chewie, axios);
