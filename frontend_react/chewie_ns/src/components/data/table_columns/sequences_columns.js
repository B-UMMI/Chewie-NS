import React from "react";

export const SEQUENCES_STYLES = (theme) => ({
  root: {
    "& .MuiTextField-root": {
      margin: theme.spacing(1),
      width: "100ch",
    },
  },
  paper: {
    marginTop: theme.spacing(8),
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
  },
  submit: {
    margin: theme.spacing(3, 0, 2),
  },
  buttonRoot: {
    boxShadow: "none",
    textTransform: "none",
    color: "#ffffff",
    borderRadius: 4,
    fontSize: 16,
    padding: "6px 12px",
    border: "1px solid",
    backgroundColor: "#3b3b3b",
    borderColor: "#3b3b3b",
    "&:hover": {
      backgroundColor: "#3b3b3b",
      borderColor: "#3b3b3b",
    },
    "&:active": {
      boxShadow: "none",
      backgroundColor: "#3b3b3b",
      borderColor: "#3b3b3b",
    },
    "&:focus": {
      boxShadow: "0 0 0 0.2rem rgba(0,123,255,.5)",
    },
  },
});

export const SEQUENCES_COLUMNS = [
  {
    name: "species_name",
    label: "Species",
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
      customBodyRender: (value, tableMeta, updateValue) => {
        return <i>{value}</i>;
      },
    },
  },
  {
    name: "schemas_url",
    label: "Schema",
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
      customBodyRender: (value, tableMeta, updateValue) => {
        let schema_id = value.substring(value.lastIndexOf("/") + 1);

        return (
          <a href={value} target={"_blank"} rel="noopener noreferrer">
            {schema_id}
          </a>
        );
      },
    },
  },
  {
    name: "locus_url",
    label: "Locus ID",
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
      customBodyRender: (value, tableMeta, updateValue) => {
        let locus_id = value.substring(value.lastIndexOf("/") + 1);

        return (
          <a href={value} target={"_blank"} rel="noopener noreferrer">
            {locus_id}
          </a>
        );
      },
    },
  },
  {
    name: "alleles",
    label: "Number of alleles",
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

export const SEQUENCES_OPTIONS = {
  responsive: "scrollMaxHeight",
  selectableRowsHeader: false,
  selectableRows: "none",
  selectableRowsOnClick: false,
  print: false,
  download: false,
  filter: true,
  filterType: "multiselect",
  search: false,
  viewColumns: true,
  pagination: true,
};
