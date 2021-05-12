import React from "react";

// Material UI imports
import CircularProgress from "@material-ui/core/CircularProgress";

export const PROFILE_COLUMNS = [
  {
    name: "species_id",
    label: "Species ID",
    options: {
      filter: true,
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
    name: "schema_id",
    label: "Schema ID",
    options: {
      filter: true,
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
    name: "nr_loci",
    label: "Loci Added",
    options: {
      filter: true,
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
    name: "nr_allele",
    label: "Alleles Added",
    options: {
      filter: true,
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
];

export const PROFILE_OPTIONS = {
  textLabels: {
    body: {
      noMatch: <CircularProgress />,
    },
  },
  responsive: "scrollMaxHeight",
  selectableRowsHeader: false,
  selectableRows: "none",
  print: false,
  viewColumns: false,
  pagination: false,
  download: false,
  filter: false,
  search: false,
};
