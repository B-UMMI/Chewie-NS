import React from "react";

// Chewie local imports
import Markdown from "../../Markdown/Markdown";

// Material UI imports
import CircularProgress from "@material-ui/core/CircularProgress";

export const ANNOTATIONS_COLUMNS = [
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
];

export const ANNOTATIONS_COLUMNS2 = [
  {
    name: "locus_name",
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
    name: "locus_original_name",
    label: "Locus Original Name",
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
    name: "nr_alleles",
    label: "Total Number of Alleles",
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
    name: "alleles_mode",
    label: "Alleles Mode",
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
];

export const ANNOTATIONS_OPTIONS = {
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
  download: true,
  filter: true,
  filterType: "multiselect",
  search: true,
  viewColumns: true,
  pagination: true,
};
