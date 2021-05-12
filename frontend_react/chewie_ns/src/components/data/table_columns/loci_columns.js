import React from "react";

// Chewie local imports
import Markdown from "../../Markdown/Markdown";

export const LOCUS_COLUMNS = [
  {
    name: "locus_ID",
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
    },
  },
  {
    name: "locus_label",
    label: "Locus Label",
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
    name: "num_alleles",
    label: "Number of Alleles",
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
    name: "size_range",
    label: "Size Range (bp)",
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
    name: "min",
    label: "Minimum size (bp)",
    options: {
      filter: true,
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
    name: "max",
    label: "Maximum size (bp)",
    options: {
      filter: true,
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
    name: "median",
    label: "Median Size (bp)",
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
    name: "user_annotation",
    label: "User locus name",
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
        return <Markdown markdown={value} />;
      },
    },
  },
  {
    name: "custom_annotation",
    label: "Custom Annotation",
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
        return <Markdown markdown={value} />;
      },
    },
  },
  {
    name: "uniprot_label",
    label: "Uniprot Label",
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
    name: "uniprot_submitted_name",
    label: "Uniprot Submitted Name",
    options: {
      filter: true,
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
    name: "uniprot_uri",
    label: "Uniprot URI",
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
        let link = value;

        if (link === "N/A") {
          return <div>{link}</div>;
        } else {
          return (
            <a href={link} target="_blank" rel="noopener noreferrer">
              {link}
            </a>
          );
        }
      },
    },
  },
];

export const LOCUS_OPTIONS = {
  responsive: "scrollMaxHeight",
  selectableRowsHeader: false,
  selectableRows: "none",
  selectableRowsOnClick: false,
  print: false,
  download: true,
  filter: false,
  search: false,
  viewColumns: true,
  pagination: false,
};
