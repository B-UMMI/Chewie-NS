import React from "react";

// Material Ui import
import Typography from "@material-ui/core/Typography";

const Copyright = () => {
  return (
    <footer
      style={{
        position: "fixed",
        bottom: "0",
        left: "0",
        backgroundColor: "#ccc",
        width: "100%",
        textAlign: "center",
      }}
    >
      <div id="homeFooter" style={{ display: "block" }}>
        <div>
          <Typography style={{ fontSize: "10" }}>
            © UMMI {new Date().getFullYear()}
          </Typography>
        </div>
      </div>
    </footer>
  );
};

export default Copyright;
