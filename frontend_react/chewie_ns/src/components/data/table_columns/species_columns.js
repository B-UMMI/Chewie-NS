import React from "react";

// Material UI imports
import CircularProgress from "@material-ui/core/CircularProgress";

export const SPECIES_COLUMNS = [
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
    name: "schema_name",
    label: "Schema Name",
    options: {
      filter: true,
      sort: false,
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
    name: "user",
    label: "Created by user",
    options: {
      filter: false,
      sort: true,
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
    label: "Loci",
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
    name: "nr_allele",
    label: "Alleles",
    options: {
      filter: false,
      sort: true,
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
    name: "chewie",
    label: "Software",
    options: {
      filter: false,
      sort: false,
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
    name: "dateEntered",
    label: "Creation Date",
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
    name: "lastModified",
    label: "Last Change Date",
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
    name: "bsr",
    label: "Blast Score Ratio",
    options: {
      filter: false,
      sort: true,
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
    name: "ptf",
    label: "Prodigal Training File",
    options: {
      filter: false,
      sort: true,
      display: false,
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
    name: "tl_table",
    label: "Translation Table",
    options: {
      filter: false,
      sort: true,
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
    name: "minLen",
    label: "Minimum Length (bp)",
    options: {
      filter: false,
      sort: true,
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
    name: "sizeThresh",
    label: "Size Threshold",
    options: {
      filter: false,
      sort: true,
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

export const SPECIES_OPTIONS = {
  textLabels: {
    body: {
      noMatch: <CircularProgress />,
    },
  },
  responsive: "scrollMaxHeight",
  selectableRowsHeader: false,
  selectableRows: "none",
  print: false,
  viewColumns: true,
  pagination: false,
};

export const SCHEMA_SPECIES_OPTIONS = {
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
