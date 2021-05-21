import React from "react";
import { Link as RouterLink } from "react-router-dom";

// Chewie local imports
import Aux from "../../../hoc/Aux/Aux";

// Material UI imports
import Button from "@material-ui/core/Button";
import CircularProgress from "@material-ui/core/CircularProgress";

export const STATS_COLUMNS = [
  {
    name: "species_id",
    label: "Species ID",
    options: {
      filter: false,
      sort: true,
      display: true,
      setCellHeaderProps: (value) => {
        return {
          style: {
            fontWeight: "bold",
          },
        };
      },
    },
  },
  {
    name: "species_name",
    label: "Species",
    options: {
      filter: true,
      setCellHeaderProps: (value) => {
        return {
          style: {
            fontWeight: "bold",
          },
        };
      },
      customBodyRender: (value, tableMeta, updateValue) => (
        <Aux>
          <i>{value}</i>
        </Aux>
      ),
    },
  },
  {
    name: "nr_schemas",
    label: "No. Schemas available",
    options: {
      filter: true,
      setCellHeaderProps: (value) => {
        return {
          style: {
            fontWeight: "bold",
          },
        };
      },
    },
  },
  {
    name: "Schemas Details",
    options: {
      filter: false,
      empty: true,
      setCellHeaderProps: (value) => {
        return {
          style: {
            fontWeight: "bold",
          },
        };
      },
      customBodyRender: (value, tableMeta, updateValue) => {
        return (
          <Button
            variant="contained"
            color="default"
            component={RouterLink}
            to={"/species/" + tableMeta.rowData[0]}
            onClick={() => console.log(tableMeta.rowData[0])}
          >
            Schema Details
          </Button>
        );
      },
    },
  },
];

export const STATS_OPTIONS = {
  textLabels: {
    body: {
      noMatch: <CircularProgress />,
    },
  },
  responsive: "scrollMaxHeight",
  selectableRowsHeader: false,
  selectableRows: "none",
  selectableRowsOnClick: false,
  print: false,
  download: false,
  search: false,
  filter: false,
  viewColumns: false,
};
