import React from "react";

// Material Ui import
import Typography from "@material-ui/core/Typography";
import { withStyles } from "@material-ui/core/styles";

const WhiteTextTypography = withStyles({
  root: {
    color: "#FFFFFF",
  },
})(Typography);

const Copyright = () => {
  return (
    <footer
      style={{
        position: "fixed",
        bottom: "0",
        left: "0",
        backgroundColor: "#3b3b3b",
        width: "100%",
        textAlign: "center",
      }}
    >
      <div id="homeFooter" style={{ display: "block" }}>
        <div>
          <WhiteTextTypography style={{ fontSize: "10" }}>
            © UMMI {new Date().getFullYear()}
          </WhiteTextTypography>
        </div>
      </div>
    </footer>
  );
};

export default Copyright;
