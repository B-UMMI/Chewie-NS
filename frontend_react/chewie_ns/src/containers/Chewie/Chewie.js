import React, { Component } from "react";
import { Link } from "react-router-dom";

// Assets imports
import INCDlogo from "../../assets/images/INCD-small.png";
import UMMIlogo from "../../assets/images/ummi1small2.png";
import IMMlogo from "../../assets/images/iMM_JLA_medium2.png";
import FMULlogo from "../../assets/images/fmul_logo.png";

// Material UI import
import Button from "@material-ui/core/Button";

// Chewie local imports
import axios from "../../axios-backend";
import classes from "./Chewie.module.css";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";

class Chewie extends Component {
  render() {
    return (
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
            href={"http://darwin.phyloviz.net/wiki/doku.php?id=start"}
            target="_blank"
            rel="noopener noreferrer"
          >
            <img src={UMMIlogo} alt="UMMI!" />
          </a>
        </div>
        <div id="titleDIv" className={classes.titleDiv}>
          <h2>
            Chewie-NS: Enabling the use of gene-by-gene typing methods through a
            public and centralized service
          </h2>
        </div>
        <div id="bodyDiv" className={classes.bodyDiv}>
          <div style={{ marginTop: "30px" }}>
            <p>
              <b>Chewie-NS</b> is a Nomenclature Server that is based on the
              TypOn ontology and aims to provide a centralized service to
              download or update cg/wgMLST schemas, allowing the easy sharing of
              results, while ensuring the reproducibility and consistency of
              these steps. It has an integration with the previously proposed{" "}
              <b>chewBBACA</b>, a suite that allows the creation of gene-by-gene
              schemas and determination of allelic profiles from assembled draft
              genomes.
            </p>
            <p>
              <b>Chewie-NS</b> is an easy way for users worldwide to download
              the necessary data defining the cg/wgMLST schemas, perform
              analyses locally with chewBBACA, and, if they so wish, to submit
              their novel results to the web service through a REST API to
              ensure that a common nomenclature is maintained.
            </p>
            <p>
              Please visit the <b>Tutorial</b> site at{" "}
              <a href="https://tutorial.chewbbaca.online/">
                https://tutorial.chewbbaca.online/
              </a>{" "}
              or by clicking on the test tube icon on the sidebar! The{" "}
              <b>Tutorial</b> instructions will be available soon at{" "}
              <a
                href={"https://chewie-ns.readthedocs.io/en/latest/index.html"}
                target={"_blank"}
                rel="noopener noreferrer"
              >
                Chewie-NS' Read The Docs
              </a>
              .
            </p>
            <p>
              For any issues or requests contact the development team at{" "}
              <a href="mailto:imm-bioinfo@medicina.ulisboa.pt">
                imm-bioinfo@medicina.ulisboa.pt
              </a>
              .
            </p>
          </div>
        </div>
        <div style={{ textAlign: "center", marginTop: "20px" }}>
          <div id="availableSchemasDiv" style={{ marginTop: "30px" }}>
            <Button
              variant="contained"
              color="default"
              component={Link}
              to="/stats"
            >
              Available Schemas
            </Button>
          </div>
        </div>
        <div id="INCD_div" className={classes.incdDiv}>
          <div id="resourcesTextDiv">
            <p className={classes.resourcesText}>
              <b>Resources provided by</b>
            </p>
            <img src={INCDlogo} alt="Resources provided by" />
          </div>
        </div>
      </div>
    );
  }
}

export default withErrorHandler(Chewie, axios);
